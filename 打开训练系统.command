#!/usr/bin/env bash
# 双击本文件 = 打开「英文面试健身房」
# 规则：保持这个终端窗口开着（它就是服务器）；关掉窗口 = 停止服务。
cd "$(dirname "$0")"
URL="http://127.0.0.1:8765"

# 已在运行？直接打开浏览器
if curl -s -m 2 "$URL/api/health" >/dev/null 2>&1; then
  echo "✅ 服务已在运行，打开浏览器…"
  open "$URL"
  exit 0
fi

echo "🚀 正在启动服务（首次启动需数秒）…"
cd app
../.venv/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port 8765 &
SERVER_PID=$!
cd ..

for i in $(seq 1 40); do
  if curl -s -m 2 "$URL/api/health" >/dev/null 2>&1; then break; fi
  sleep 0.5
done

if curl -s -m 2 "$URL/api/health" >/dev/null 2>&1; then
  echo "✅ 已就绪 → 打开浏览器 $URL"
  echo "   （练习结束想关服务：关掉本窗口，或按 Ctrl+C）"
  open "$URL"
else
  echo "❌ 启动超时：请检查上方日志排错（常见原因：依赖未安装 / .env 未配置 / 端口被占）"
fi

wait $SERVER_PID
