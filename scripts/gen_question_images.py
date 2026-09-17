"""用腾讯云 VOD AIGC 生图（GPT-Image2 / image2_medium）为每道题生成形象图。
- 结果: materials/question-bank/images/<set>/<qid>.png
- 断点续跑：已存在的图跳过
- 用法: cd EngTraining && python3 scripts/gen_question_images.py [--set baseline-8] [--limit N] [--dry-run]
注意：调用会产生腾讯云 AIGC 费用（每张图按 GPT-Image2 medium 计费）。
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
META_PATH = ROOT / "materials" / "question-bank" / "meta.json"
IMGDIR = ROOT / "materials" / "question-bank" / "images"
VOD_SCRIPT = Path.home() / ".hermes" / "skills" / "tencent-vod" / "scripts" / "vod_aigc_image.py"


def gen_one(prompt: str, out_path: Path, dry: bool = False) -> str:
    cmd = [
        "python3", str(VOD_SCRIPT), "create",
        "--model", "OG", "--model-version", "image2_medium",
        "--prompt", prompt,
        "--output-aspect-ratio", "1:1",
        "--output-resolution", "1K",
        "--output-format", "png",
        "--output-storage-mode", "Temporary",
        "--max-wait", "420",
    ]
    if dry:
        print("[dry] " + " ".join(cmd[:8]) + " ... ->", out_path)
        return "dry"
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=520,
                       cwd=str(VOD_SCRIPT.parent.parent))
    out = p.stdout + "\n" + p.stderr
    urls = re.findall(r"https?://[^\s\)]+", out)
    urls = [u for u in urls if "myqcloud" in u or "tencent" in u or "vod" in u]
    if not urls:
        raise RuntimeError(f"no url in output: {out[-600:]}")
    url = urls[-1].rstrip('",')
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)
    return f"{len(r.content) // 1024}KB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="only_set")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT / "app"))
    from server import prompts  # noqa: E402

    done = skipped = failed = 0
    jobs = []
    for set_key, items in meta.items():
        if args.only_set and set_key != args.only_set:
            continue
        qset = prompts.load_question_set(set_key)
        for i, q in enumerate(qset.get("questions") or []):
            qid = q.get("id") or f"q{i + 1}"
            m = items.get(qid)
            if not m:
                continue
            out_path = IMGDIR / set_key / f"{qid}.png"
            if out_path.exists():
                skipped += 1
                continue
            jobs.append((set_key, qid, m["img_prompt"], out_path))
    if args.limit:
        jobs = jobs[: args.limit]

    print(f"jobs={len(jobs)} skipped(existing)={skipped}")
    for idx, (set_key, qid, prompt, out_path) in enumerate(jobs, 1):
        t0 = time.time()
        try:
            info = gen_one(prompt, out_path, dry=args.dry_run)
            done += 1
            print(f"[{idx}/{len(jobs)}] {set_key}/{qid} OK {info} ({time.time() - t0:.0f}s)")
        except Exception as e:
            failed += 1
            print(f"[{idx}/{len(jobs)}] {set_key}/{qid} FAIL: {str(e)[:220]}")
        time.sleep(2)
    print(f"DONE: ok={done} fail={failed} skipped={skipped}")


if __name__ == "__main__":
    main()
