"""为全部题目生成：中文短标题 + 生图 prompt（English, flat app-icon style）。
结果存 materials/question-bank/meta.json，可重复运行（已有条目跳过）。
用法：cd EngTraining && .venv/bin/python scripts/gen_question_meta.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from server import prompts  # noqa: E402
from server.llm import get_llm  # noqa: E402

META_PATH = ROOT / "materials" / "question-bank" / "meta.json"

SYS = """你在为一个英语面试训练 App 的题目卡片设计元信息。对每个面试题输出两项：
1. title：中文短标题（4-12 个汉字，概括这题答什么，如"自我介绍·90秒""为什么选我们""讲一次失败"），彼此有区分度、不重复；
2. img_prompt：英文生图提示词——为这题画一个"形象化小图标插画"。
生图提示词规范（严格遵守）：
- Style: flat vector illustration, minimal, soft pastel palette with teal (#0FA79A) accent, rounded organic shapes, clean white background, single centered symbol, absolutely NO text or letters, no human faces, subtle soft shadow, modern app icon aesthetic.
- Content: 用日常物件或抽象符号隐喻题目主题（例：团队冲突→两只互扣的拼图；自我介绍→舞台聚光灯下的名片；失败→折返的路标箭头）。
- 40-70 英文单词，只描述画面内容，不要任何解释。
只输出一个 JSON 对象：{"<题目id>": {"title": "...", "img_prompt": "..."}, ...}，id 必须与输入完全一致且不遗漏任何一题。"""


def main():
    meta = {}
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    set_files = sorted((ROOT / "materials" / "question-bank").glob("*.yml"))
    total_new = 0
    for f in set_files:
        set_key = f.stem
        qset = prompts.load_question_set(set_key)
        items = []
        for i, q in enumerate(qset.get("questions") or []):
            qid = q.get("id") or f"q{i + 1}"
            items.append({"id": qid, "text": q.get("text", ""), "category": q.get("category") or q.get("tag") or ""})
        have = meta.setdefault(set_key, {})
        todo = [it for it in items if it["id"] not in have]
        print(f"[{set_key}] total={len(items)} missing={len(todo)}")
        B = 15  # 分批，防输出过长
        for k in range(0, len(todo), B):
            batch = todo[k : k + B]
            msgs = [
                {"role": "system", "content": SYS},
                {"role": "user", "content": "题目列表：\n" + json.dumps(batch, ensure_ascii=False, indent=1)},
            ]
            try:
                obj = get_llm().chat_json(msgs, temperature=0.4, max_tokens=3200)
            except Exception as e:
                print(f"  batch {k // B} FAILED: {e}")
                continue
            got = 0
            for it in batch:
                v = obj.get(it["id"])
                if isinstance(v, dict) and v.get("title") and v.get("img_prompt"):
                    have[it["id"]] = {"title": str(v["title"])[:20], "img_prompt": str(v["img_prompt"])}
                    got += 1
            total_new += got
            print(f"  batch {k // B}: +{got}/{len(batch)}")
            # 缺失的立即单发重试一次
            missing = [it for it in batch if it["id"] not in have]
            if missing:
                msgs2 = msgs + [
                    {"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)[:1500]},
                    {"role": "user", "content": "上一批缺了这些 id：" + json.dumps([m["id"] for m in missing]) + "。请为它们补上，只输出缺失项的 JSON。"},
                ]
                try:
                    obj2 = get_llm().chat_json(msgs2, temperature=0.4, max_tokens=1600)
                    for it in missing:
                        v = obj2.get(it["id"])
                        if isinstance(v, dict) and v.get("title") and v.get("img_prompt"):
                            have[it["id"]] = {"title": str(v["title"])[:20], "img_prompt": str(v["img_prompt"])}
                            total_new += 1
                except Exception as e:
                    print(f"    retry failed: {e}")
            META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v) for v in meta.values())
    print(f"DONE: +{total_new} new, meta total {n} -> {META_PATH}")


if __name__ == "__main__":
    main()
