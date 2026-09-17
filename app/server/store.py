"""会话与错题本存储（JSONL，全部落在 data/ 下）。"""
import json
import time
import uuid
from pathlib import Path

from . import config


def new_session_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]


def sessions_root() -> Path:
    d = config.data_dir() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def session_path(sid: str) -> Path:
    return sessions_root() / f"{sid}.jsonl"


def append(sid: str, record: dict):
    record = {"ts": time.time(), **record}
    with session_path(sid).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_records(sid: str) -> list:
    p = session_path(sid)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def list_sessions(limit: int = 20) -> list:
    out = []
    for p in sorted(sessions_root().glob("*.jsonl"), reverse=True)[:limit]:
        recs = load_records(p.stem)
        meta = next((r for r in recs if r.get("type") == "meta"), {})
        answers = [r for r in recs if r.get("type") == "answer"]
        out.append(
            {
                "sid": p.stem,
                "persona": meta.get("persona_title") or meta.get("persona"),
                "set": meta.get("set"),
                "started_at": meta.get("ts"),
                "answers": len(answers),
                "ended": any(r.get("type") == "review" for r in recs),
            }
        )
    return out


def append_errorbook(entries: list):
    p = config.data_dir() / "errorbook.jsonl"
    with p.open("a", encoding="utf-8") as f:
        for e in entries:
            e = {"ts": time.time(), **e}
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- 收藏夹（Speakey 式 Favorite）

def _read_jsonl(path) -> list:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _fav_key(e: dict) -> str:
    """词条去重键：生词按小写，句子按原文。"""
    typ = e.get("ftype") or e.get("type") or "word"
    text = (e.get("text") or "").strip()
    return text.lower() if typ == "word" else text


def append_favorite(entry: dict):
    p = config.data_dir() / "favorites.jsonl"
    e = {"ts": time.time(), **entry}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def delete_favorite(text: str, kind: str = "word"):
    """软删除（墓碑记录）：读取时生效；删除后再重新收藏同名词不受影响。"""
    p = config.data_dir() / "favorites.jsonl"
    e = {"ts": time.time(), "type": "delete", "ftype": kind, "text": text}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def list_favorites(limit: int = 500) -> list:
    """去重后的收藏列表：同词只留一条（最新释义 + ipa，首次收藏时间），支持墓碑删除。"""
    state: dict = {}
    for e in _read_jsonl(config.data_dir() / "favorites.jsonl"):
        if e.get("type") == "delete":
            state.pop(_fav_key(e), None)
            continue
        k = _fav_key(e)
        if not k:
            continue
        if k in state:
            old = state[k]
            merged = {**old, **e}
            merged["ts"] = old.get("ts", e.get("ts"))
            if not (e.get("note") or "").strip():
                merged["note"] = old.get("note") or ""
            if not (e.get("ipa") or "").strip():
                merged["ipa"] = old.get("ipa") or ""
            state[k] = merged
        else:
            state[k] = e
    items = sorted(state.values(), key=lambda x: x.get("ts") or 0, reverse=True)
    return items[:limit]


# ---------------------------------------------------------------- 单词复习（按比例每日温故）

def _review_cfg() -> dict:
    r = config.get("review", {}) or {}

    def _f(v, dflt):
        try:
            return float(v)
        except Exception:
            return dflt

    def _i(v, dflt):
        try:
            return int(float(v))
        except Exception:
            return dflt

    ratio = min(max(_f(r.get("ratio"), 0.3), 0.05), 1.0)
    return {
        "ratio": ratio,
        "min_per_day": max(1, _i(r.get("min_per_day"), 5)),
        "max_per_day": max(1, _i(r.get("max_per_day"), 30)),
    }


def review_events() -> list:
    return _read_jsonl(config.data_dir() / "reviews.jsonl")


def _review_history() -> dict:
    """key -> {\"last\": ts, \"ok\": 最近一次, \"count\": 次数}"""
    out: dict = {}
    for e in review_events():
        k = e.get("key") or ""
        if not k:
            continue
        h = out.setdefault(k, {"last": 0.0, "ok": None, "count": 0})
        h["last"] = max(h["last"], e.get("ts") or 0)
        h["ok"] = bool(e.get("ok"))
        h["count"] += 1
    return out


def _today_words() -> list:
    """今日复习词表：按比例随机抽样（同一天内固定），优先：从未复习 > 上次没记住 > 久未复习。"""
    import datetime as _dt
    import random as _random

    today = _dt.date.today().isoformat()
    words = [f for f in list_favorites() if (f.get("type") or "word") == "word"]
    cfg = _review_cfg()
    n = min(len(words), cfg["max_per_day"], max(cfg["min_per_day"], round(cfg["ratio"] * len(words))))
    if n <= 0:
        return []

    decks_path = config.data_dir() / "review_decks.json"
    decks = {}
    if decks_path.exists():
        try:
            decks = json.loads(decks_path.read_text(encoding="utf-8")) or {}
        except Exception:
            decks = {}
    by_key = {_fav_key(w): w for w in words}
    saved = decks.get(today)
    if isinstance(saved, list):
        picked = [by_key[k] for k in saved if k in by_key]
        if picked:
            return picked

    hist = _review_history()
    now = time.time()

    def bucket(w):
        h = hist.get(_fav_key(w))
        if not h:
            return 0  # 从未复习
        if h.get("ok") is False:
            return 1  # 上次没记住
        return 3 if (now - (h.get("last") or 0)) / 86400 >= 7 else 2

    rng = _random.Random(today)
    rnd = [rng.random() for _ in words]
    order = sorted(range(len(words)), key=lambda i: (bucket(words[i]), rnd[i]))
    picked = [words[i] for i in order[:n]]

    decks[today] = [_fav_key(w) for w in picked]
    cutoff = (_dt.date.today() - _dt.timedelta(days=60)).isoformat()
    decks = {d: v for d, v in decks.items() if isinstance(d, str) and d >= cutoff}
    decks_path.write_text(json.dumps(decks, ensure_ascii=False, indent=1), encoding="utf-8")
    return picked


def review_today() -> dict:
    import datetime as _dt

    today = _dt.date.today().isoformat()
    deck_words = _today_words()
    hist = _review_history()
    ans: dict = {}
    prev: dict = {}
    for e in review_events():
        if not e.get("key"):
            continue
        if e.get("date") == today:
            ans[e["key"]] = bool(e.get("ok"))
        else:
            prev[e["key"]] = bool(e.get("ok"))  # 今天之前最近一次的结果

    deck = []
    n_ans = n_ok = n_no = 0
    for w in deck_words:
        k = _fav_key(w)
        a = ans.get(k)
        h = hist.get(k) or {}
        deck.append(
            {
                "key": k,
                "text": w.get("text"),
                "note": w.get("note") or "",
                "ipa": w.get("ipa") or "",
                "done": a is not None,
                "last_ok": a,
                "prev_ok": prev.get(k),
                "reviewed_before": bool(h.get("count")),
                "times": h.get("count", 0),
            }
        )
        if a is not None:
            n_ans += 1
            if a:
                n_ok += 1
            else:
                n_no += 1

    # 最近 7 天复习词数（用于迷你周历）
    by_day: dict = {}
    for e in review_events():
        d, k = e.get("date"), e.get("key")
        if d and k:
            by_day.setdefault(d, set()).add(k)
    recent = []
    for i in range(6, -1, -1):
        d = (_dt.date.today() - _dt.timedelta(days=i)).isoformat()
        recent.append({"date": d, "count": len(by_day.get(d, ()))})

    cfg = _review_cfg()
    total = len(deck)
    return {
        "date": today,
        "deck": deck,
        "goal": total,
        "answered": n_ans,
        "correct": n_ok,
        "wrong": n_no,
        "remaining": total - n_ans,
        "done": total > 0 and n_ans >= total,
        "pool": len([f for f in list_favorites() if (f.get("type") or "word") == "word"]),
        "ratio": cfg["ratio"],
        "min_per_day": cfg["min_per_day"],
        "max_per_day": cfg["max_per_day"],
        "recent": recent,
    }


def append_review_answer(word: str, ok: bool) -> dict:
    import datetime as _dt

    w = (word or "").strip()
    rec = {"ts": time.time(), "date": _dt.date.today().isoformat(), "key": w.lower(), "word": w, "ok": bool(ok)}
    p = config.data_dir() / "reviews.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return review_today()


# ---------------------------------------------------------------- 打卡统计

def stats() -> dict:
    """打卡统计：连续/最长连胜、今日进度、近 14 天活跃（场次 + 分钟）。"""
    import datetime as _dt

    days: dict = {}  # date -> {"sessions", "minutes", "answers"}
    total_answers = 0
    total_ms = 0
    n_sessions = 0
    for p in sorted(sessions_root().glob("*.jsonl")):
        recs = load_records(p.stem)
        meta = next((r for r in recs if r.get("type") == "meta"), None)
        if not meta or not meta.get("ts"):
            continue
        n_sessions += 1
        d = _dt.datetime.fromtimestamp(meta["ts"]).strftime("%Y-%m-%d")
        slot = days.setdefault(d, {"sessions": 0, "minutes": 0.0, "answers": 0})
        slot["sessions"] += 1
        answers = [r for r in recs if r.get("type") == "answer"]
        ms = sum(a.get("duration_ms") or 0 for a in answers)
        slot["minutes"] += ms / 60000.0
        slot["answers"] += len(answers)
        total_answers += len(answers)
        total_ms += ms

    today = _dt.date.today()
    cur = today
    if not days.get(cur.isoformat()) and days.get((cur - _dt.timedelta(days=1)).isoformat()):
        cur = cur - _dt.timedelta(days=1)  # 昨天打过卡也连续
    streak = 0
    while days.get(cur.isoformat()):
        streak += 1
        cur = cur - _dt.timedelta(days=1)

    best = 0
    run = 0
    prev = None
    for d in sorted(days):
        dd = _dt.date.fromisoformat(d)
        run = run + 1 if (prev is not None and (dd - prev).days == 1) else 1
        best = max(best, run)
        prev = dd

    rv_days: dict = {}
    for e in review_events():
        d, k = e.get("date"), e.get("key")
        if d and k:
            rv_days.setdefault(d, set()).add(k)

    recent = []
    for i in range(13, -1, -1):
        d = (today - _dt.timedelta(days=i)).isoformat()
        s = days.get(d, {})
        recent.append(
            {
                "date": d,
                "count": s.get("sessions", 0),
                "minutes": round(s.get("minutes", 0.0), 1),
                "reviewed": len(rv_days.get(d, ())),
            }
        )

    tk = today.isoformat()
    ts = days.get(tk, {"sessions": 0, "minutes": 0.0, "answers": 0})
    rv = review_today()
    return {
        "streak_days": streak,
        "best_streak": best,
        "total_sessions": n_sessions,
        "total_answers": total_answers,
        "total_minutes": round(total_ms / 60000, 1),
        "today": {"date": tk, "sessions": ts["sessions"], "minutes": round(ts["minutes"], 1), "answered": ts["answers"]},
        "daily_goal_minutes": config.get("session.daily_goal_minutes", 20),
        "review": {
            "goal": rv["goal"],
            "answered": rv["answered"],
            "correct": rv["correct"],
            "remaining": rv["remaining"],
            "done": rv["done"],
            "ratio": rv["ratio"],
        },
        "recent_14": recent,
    }


# ---------------------------------------------------------------- 题目历史（题集详情页）

def attempts_by_question() -> dict:
    """按题目文本聚合历史作答（跨会话），用于题集详情页的追溯视图。"""
    out: dict = {}
    for p in sorted(sessions_root().glob("*.jsonl")):
        sid = p.stem
        for r in load_records(sid):
            if r.get("type") != "answer":
                continue
            q = (r.get("question") or "").strip()
            if not q:
                continue
            fb = r.get("feedback") or {}
            met = r.get("metrics") or {}
            sd = r.get("script_diff") or {}
            out.setdefault(q, []).append(
                {
                    "sid": sid,
                    "ts": r.get("ts"),
                    "mode": r.get("mode"),
                    "duration_s": met.get("duration_s"),
                    "wpm": met.get("wpm"),
                    "fillers": met.get("fillers"),
                    "score": fb.get("score"),
                    "accuracy": sd.get("accuracy") if r.get("mode") == "read" else None,
                }
            )
    for q in out:
        out[q].sort(key=lambda a: a.get("ts") or 0, reverse=True)
    return out
