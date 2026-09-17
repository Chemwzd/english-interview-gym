#!/usr/bin/env bash
# 启动 EngTraining 本地服务：http://127.0.0.1:8765
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "未找到 .venv，先执行：uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r app/requirements.txt"
  exit 1
fi
cd app
exec ../.venv/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port 8765 "$@"
