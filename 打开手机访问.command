#!/usr/bin/env bash
# 双击本文件 = 让手机（iPhone/Safari）通过 HTTPS 使用本系统（麦克风需要 HTTPS）。
# 前置：① 本机服务已在运行（双击「打开训练系统.command」）② 首次使用先生成证书（见 README「在手机上使用」）。
# 规则：保持这个终端窗口开着；关掉窗口 = 手机访问停止。
cd "$(dirname "$0")"

if [ ! -f certs/server.crt ]; then
  echo "⚠️ 还没生成证书。首次使用请先运行：bash scripts/gen_https_cert.sh"
  echo "   （完整说明见 README 的「在手机上使用」一节）"
  exit 1
fi

if ! curl -s -m 2 "http://127.0.0.1:8765/api/health" >/dev/null 2>&1; then
  echo "⚠️ 本机服务未在运行：请先双击「打开训练系统.command」启动服务。"
  exit 1
fi

echo "📱 手机访问已开启（HTTPS）——保持本窗口开着，Ctrl+C 退出。"
echo
exec .venv/bin/python scripts/https_proxy.py
