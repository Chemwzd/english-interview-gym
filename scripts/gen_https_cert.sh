#!/usr/bin/env bash
# 生成手机访问用的「本地 CA + 服务器证书」（自签）。
# 用途：iPhone 麦克风只在 HTTPS（安全上下文）下可用；当 Tailscale 的
# Let's Encrypt 证书因网络不可达无法签发时，用本方案替代（不依赖外网）。
# 用法: bash scripts/gen_https_cert.sh [域名] [额外IP]
#   域名缺省 = 本机 Tailscale 域名（形如 my-mac.tailXXXX.ts.net）；IP 缺省 = 本机 Tailscale IP。
set -euo pipefail
cd "$(dirname "$0")/.."

TS_BIN="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
DOMAIN="${1:-}"
TSIP="${2:-}"

if [ -z "$DOMAIN" ] && [ -x "$TS_BIN" ]; then
  DOMAIN="$("$TS_BIN" status --json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' || true)"
fi
if [ -z "$TSIP" ] && [ -x "$TS_BIN" ]; then
  TSIP="$("$TS_BIN" ip -4 2>/dev/null | head -1 || true)"
fi
if [ -z "$DOMAIN" ]; then
  echo "用法: bash scripts/gen_https_cert.sh <域名> [额外IP]" >&2
  exit 1
fi

SAN="DNS:${DOMAIN},DNS:localhost"
[ -n "$TSIP" ] && SAN="${SAN},IP:${TSIP}"
SAN="${SAN},IP:127.0.0.1"

mkdir -p certs

# CA（10 年，仅用于给本机服务器证书签名；ca.crt 需要安装到手机并信任）
if [ ! -f certs/ca.key ]; then
  openssl genrsa -out certs/ca.key 4096 2>/dev/null
  openssl req -x509 -new -key certs/ca.key -sha256 -days 3650 \
    -subj "/CN=English Interview Gym Local CA" -out certs/ca.crt 2>/dev/null
  echo "· 已生成新 CA：certs/ca.crt（10 年）"
else
  echo "· 沿用已有 CA：certs/ca.crt"
fi

# 服务器证书（825 天）
openssl genrsa -out certs/server.key 2048 2>/dev/null
openssl req -new -key certs/server.key -subj "/CN=${DOMAIN}" -out certs/server.csr 2>/dev/null
printf "subjectAltName=%s\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n" "$SAN" > certs/server.ext
openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -days 825 -sha256 -extfile certs/server.ext -out certs/server.crt 2>/dev/null
rm -f certs/server.csr certs/server.ext

echo "✅ 完成："
echo "   域名: ${DOMAIN}    SAN: ${SAN}"
echo "   iPhone 安装用（可 AirDrop 或访问 /ca.crt）: $(pwd)/certs/ca.crt"
echo "   服务器证书: certs/server.crt + certs/server.key（勿分发/入库）"
