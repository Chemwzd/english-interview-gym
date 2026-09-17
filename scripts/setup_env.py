#!/usr/bin/env python3
"""配置助手：把你的 API Key 写入 app/.env（交互式，可选步骤）。

用法：
    python3 scripts/setup_env.py

也可以完全手动配置（等价效果）：
    cp app/.env.example app/.env      # 然后编辑填入 TOKENHUB_API_KEY

说明：
- app/.env 已被 .gitignore 忽略，不会被提交到任何仓库；
- 脚本只做一件事：收集 Key → 在线验证一次 → 以 600 权限写入 app/.env。
"""
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_OUT = ROOT / "app" / ".env"
MODELS_URL = "https://tokenhub.tencentmaas.com/v1/models"

MANUAL_HELP = """未收到输入，未做任何修改。你随时可以手动配置：
  1) cp app/.env.example app/.env
  2) 编辑 app/.env，填入 TOKENHUB_API_KEY=你的key
  获取 Key: https://console.cloud.tencent.com/tokenhub"""


def validate(key: str) -> bool:
    try:
        req = urllib.request.Request(MODELS_URL, headers={"Authorization": "Bearer " + key})
        return urllib.request.urlopen(req, timeout=20).status == 200
    except Exception:
        return False


def main():
    print("EngTraining 配置助手 —— 写入 app/.env（该文件已被 .gitignore 忽略）")
    print("获取 API Key: https://console.cloud.tencent.com/tokenhub")
    try:
        key = input("请粘贴 TOKENHUB_API_KEY（sk- 开头）: ").strip()
    except EOFError:
        print(MANUAL_HELP)
        sys.exit(1)
    if not key:
        print(MANUAL_HELP)
        sys.exit(1)
    print("正在在线验证 Key …")
    if not validate(key):
        print("Key 验证失败（网络异常或密钥无效）。请检查后重试，或手动写入 app/.env。")
        sys.exit(1)
    ENV_OUT.parent.mkdir(parents=True, exist_ok=True)
    ENV_OUT.write_text(
        "# 由 scripts/setup_env.py 生成 —— 请勿提交到 git\n"
        f"TOKENHUB_API_KEY={key}\n",
        encoding="utf-8",
    )
    os.chmod(ENV_OUT, 0o600)
    print(f"OK: 已写入 {ENV_OUT}（权限 600，已忽略入库）")
    print("提示：语音模型需在控制台开通“后付费”，否则提交时会返回 402。")


if __name__ == "__main__":
    main()
