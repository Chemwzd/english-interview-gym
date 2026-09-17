#!/usr/bin/env bash
# 生成手机访问用的「本地 CA + 服务器证书」（自签；纯 Python 实现，不依赖 openssl）。
# 说明：应用已内置一键启用（界面「⚙️ 设置 → 手机访问」）；本脚本供命令行 / 仓库用户使用。
set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

"$PY" - <<'PYEOF'
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "app"))
from server import mobile  # noqa: E402

info = mobile.ensure_certs()
st = mobile.status()
print("✅ 证书：" + ("刚生成" if info.get("created") else "已存在（未重新生成）"))
print("   CA（安装到手机）: " + st["ca_path"])
print("   SAN: " + ", ".join(info.get("sans", [])))
PYEOF
