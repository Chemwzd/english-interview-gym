#!/usr/bin/env python3
"""配置助手：把你的 API Key（和可选的接口地址）写入 app/.env（交互式，可选步骤）。

用法：
    python3 scripts/setup_env.py

也可以完全手动配置（等价效果）：
    cp app/.env.example app/.env      # 然后编辑填入 API_KEY

说明：
- app/.env 已被 .gitignore 忽略，不会被提交到任何仓库；
- 脚本只做：收集 → （有地址时）在线验证一次 → 以 600 权限写入 app/.env。
"""
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_OUT = ROOT / "app" / ".env"

MANUAL_HELP = """未收到输入，未做任何修改。你随时可以手动配置：
  1) cp app/.env.example app/.env
  2) 编辑 app/.env，填入 API_KEY=你的key（接口地址可填 API_BASE_URL，
     或写在 app/config.yaml 的 llm.base_url）"""


def validate(base: str, key: str) -> bool:
    try:
        url = base.rstrip("/") + "/models"
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
        return urllib.request.urlopen(req, timeout=20).status == 200
    except Exception:
        return False


def main():
    print("EngTraining 配置助手 —— 写入 app/.env（该文件已被 .gitignore 忽略）")
    try:
        base = input("接口地址（OpenAI 兼容，如 https://your-service.example.com/v1；可留空稍后填）: ").strip()
        key = input("API Key: ").strip()
    except EOFError:
        print(MANUAL_HELP)
        sys.exit(1)
    if not key:
        print(MANUAL_HELP)
        sys.exit(1)
    if base:
        print("正在在线验证 Key …")
        if not validate(base, key):
            print("验证失败（地址、网络或密钥问题）。请检查后重试，或手动写入 app/.env。")
            sys.exit(1)
    else:
        print("（未提供接口地址，跳过在线验证）")
    ENV_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 由 scripts/setup_env.py 生成 —— 请勿提交到 git", f"API_KEY={key}"]
    if base:
        lines.append(f"API_BASE_URL={base}")
    ENV_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(ENV_OUT, 0o600)
    print(f"OK: 已写入 {ENV_OUT}（权限 600，已忽略入库）")
    print("提示：语音接口地址与模型名在 app/config.yaml 的 asr / tts 段配置；也可用本地模式（零成本）。")


if __name__ == "__main__":
    main()
