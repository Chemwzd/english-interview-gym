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

def append_favorite(entry: dict):
    p = config.data_dir() / "favorites.jsonl"
    e = {"ts": time.time(), **entry}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def list_favorites(limit: int = 100) -> list:
    p = config.data_dir() / "favorites.jsonl"
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
    return out[-limit:][::-1]


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

    recent = []
    for i in range(13, -1, -1):
        d = (today - _dt.timedelta(days=i)).isoformat()
        s = days.get(d, {})
        recent.append({"date": d, "count": s.get("sessions", 0), "minutes": round(s.get("minutes", 0.0), 1)})

    tk = today.isoformat()
    ts = days.get(tk, {"sessions": 0, "minutes": 0.0, "answers": 0})
    return {
        "streak_days": streak,
        "best_streak": best,
        "total_sessions": n_sessions,
        "total_answers": total_answers,
        "total_minutes": round(total_ms / 60000, 1),
        "today": {"date": tk, "sessions": ts["sessions"], "minutes": round(ts["minutes"], 1), "answered": ts["answers"]},
        "daily_goal_minutes": config.get("session.daily_goal_minutes", 20),
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
