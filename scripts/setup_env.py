#!/usr/bin/env python3
"""生成 app/.env（可选的便捷脚本）：
- 本机如装有 Hermes Agent：自动从其 ~/.hermes/config.yaml 中寻找可用的 TokenHub API Key（逐个实测）
- 如装有 tencent-vod 技能：顺带带上腾讯云凭证（可选）
- 找不到时：按提示手动创建 app/.env（复制 app/.env.example 填写即可）
用法：python3 scripts/setup_env.py
"""
import os
import re
import sys
import urllib.request
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[1]
ENV_OUT = ROOT / "app" / ".env"


def read_text(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""


def find_tokenhub_key():
    txt = read_text(HOME / ".hermes" / "config.yaml")
    cands = []
    # 1) custom_providers / providers 中名字含 Tokenhub 的条目优先
    for seg in re.split(r"\n(?=\s*- name:)", txt):
        if "tokenhub" in seg[:120].lower():
            m = re.search(r"api_key:\s*(\S+)", seg)
            if m:
                cands.append(m.group(1).strip())
    # 2) 兜底：全文所有 sk- 开头的 key
    cands += re.findall(r"sk-[A-Za-z0-9_\-\.]{12,}", txt)
    seen = list(dict.fromkeys(cands))
    for k in seen:
        try:
            req = urllib.request.Request(
                "https://tokenhub.tencentmaas.com/v1/models",
                headers={"Authorization": "Bearer " + k},
            )
            if urllib.request.urlopen(req, timeout=20).status == 200:
                return k, len(seen)
        except Exception:
            continue
    return None, len(seen)


def find_tencent_creds():
    out = {}
    for p in [
        HOME / ".hermes" / "skills" / "tencent-vod" / ".env",
    ]:
        t = read_text(p)
        for line in t.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def main():
    key, tried = find_tokenhub_key()
    if not key:
        print(f"在 ~/.hermes/config.yaml 的 {tried} 个候选 key 中未找到可用 TokenHub Key。")
        print("请手动创建 app/.env（可复制 app/.env.example），填入你自己的密钥：")
        print("  1) cp app/.env.example app/.env")
        print("  2) 编辑 app/.env，填 TOKENHUB_API_KEY=你的key")
        print("  获取 Key: https://console.cloud.tencent.com/tokenhub")
        sys.exit(1)
    tencent = find_tencent_creds()
    lines = [
        "# 自动生成 by scripts/setup_env.py —— 请勿提交到 git",
        f"TOKENHUB_API_KEY={key}",
    ]
    for k in ["TENCENTCLOUD_SECRET_ID", "TENCENTCLOUD_SECRET_KEY", "TENCENTCLOUD_REGION", "TENCENTCLOUD_VOD_SUB_APP_ID"]:
        if tencent.get(k):
            lines.append(f"{k}={tencent[k]}")
    ENV_OUT.parent.mkdir(parents=True, exist_ok=True)
    ENV_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(ENV_OUT, 0o600)
    print(f"OK: 已写入 {ENV_OUT}")
    print(f"  TOKENHUB_API_KEY = {key[:4]}****（len={len(key)}，实测可用）")
    tc = [k for k in tencent if k.startswith("TENCENTCLOUD")]
    print(f"  腾讯云凭证: {', '.join(tc) if tc else '（未找到）'}")


if __name__ == "__main__":
    main()
