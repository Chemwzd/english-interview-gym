#!/usr/bin/env python3
"""把所有会话的指标汇总成一张总览表：data/reports/OVERVIEW.md
用法：.venv/bin/python scripts/baseline_report.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from server import config, store  # noqa: E402


def main():
    rows = []
    for meta in store.list_sessions(limit=200):
        recs = store.load_records(meta["sid"])
        answers = [r for r in recs if r.get("type") == "answer"]
        if not answers:
            continue
        wpm = [a["metrics"]["wpm"] for a in answers if a.get("metrics", {}).get("wpm")]
        fill = [a["metrics"]["fillers"] for a in answers if a.get("metrics")]
        pauses = [a["metrics"]["long_pauses"] for a in answers if a.get("metrics")]
        rows.append(
            {
                "sid": meta["sid"],
                "persona": meta.get("persona") or "",
                "answers": len(answers),
                "avg_wpm": round(sum(wpm) / len(wpm), 1) if wpm else 0,
                "fillers": sum(fill),
                "long_pauses": sum(pauses),
            }
        )
    out = [
        "# 训练总览（自动生成）",
        "",
        "| 会话 | 考官 | 作答 | 平均语速 | 填充词 | 长停顿 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(f"| {r['sid']} | {r['persona']} | {r['answers']} | {r['avg_wpm']} | {r['fillers']} | {r['long_pauses']} |")
    out += ["", "目标参考（12 周）：语速 120–150 wpm · 长停顿 ≤4 次/5 分钟 · 填充词趋降 · 语法错 ≤2.5/100 词"]
    p = config.data_dir() / "reports" / "OVERVIEW.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"written: {p} ({len(rows)} sessions)")


if __name__ == "__main__":
    main()
