#!/usr/bin/env python3
"""手机访问 TLS 终结器（命令行版）：8443(HTTPS) → 127.0.0.1:8765。

实现已内置到应用（app/server/mobile.py）——界面「⚙️ 设置 → 手机访问」可一键启用；
本脚本供命令行 / 仓库用户使用：

    .venv/bin/python scripts/https_proxy.py [绑定地址] [端口]

默认绑定：检测到 Tailscale 时绑其 IP（仅 tailnet 内可达）；否则 0.0.0.0（局域网）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from server import mobile  # noqa: E402

if __name__ == "__main__":
    bind = sys.argv[1] if len(sys.argv) > 1 else ""
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8443
    mobile.run_forever(bind=bind, port=port)
