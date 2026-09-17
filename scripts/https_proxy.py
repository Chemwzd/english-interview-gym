#!/usr/bin/env python3
"""手机访问用的 TLS 终结器：8443(HTTPS) → 127.0.0.1:8765(HTTP)。

背景：iPhone 的麦克风只在 HTTPS（安全上下文）下可用。当 Tailscale 的
Let's Encrypt 证书因本地网络不可达而无法签发时，用「本地 CA 自签证书 + 本代理」
替代：手机安装并信任 certs/ca.crt 后，访问 https://<域名或Tailscale IP>:8443
即获得安全上下文，麦克风可正常使用。

用法: .venv/bin/python scripts/https_proxy.py [绑定地址] [端口]
默认绑定本机 Tailscale IP（仅 Tailscale 内可达，更安全）；读不到则退回 0.0.0.0。
"""
import socket
import socketserver
import ssl
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERT = ROOT / "certs" / "server.crt"
KEY = ROOT / "certs" / "server.key"
UPSTREAM = ("127.0.0.1", 8765)


def default_bind() -> str:
    for ts in ("/Applications/Tailscale.app/Contents/MacOS/Tailscale", "tailscale"):
        try:
            out = subprocess.run([ts, "ip", "-4"], capture_output=True, text=True, timeout=5)
            ip = [x.strip() for x in (out.stdout or "").splitlines() if x.strip()]
            if ip:
                return ip[0]
        except Exception:
            pass
    return "0.0.0.0"


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            tls = self.server.ctx.wrap_socket(self.request, server_side=True)
            up = socket.create_connection(UPSTREAM)
        except Exception:
            return

        def pipe(a, b):
            try:
                while True:
                    d = a.recv(65536)
                    if not d:
                        break
                    b.sendall(d)
            except Exception:
                pass
            finally:
                try:
                    b.shutdown(socket.SHUT_WR)
                except Exception:
                    pass

        a = threading.Thread(target=pipe, args=(tls, up), daemon=True)
        b = threading.Thread(target=pipe, args=(up, tls), daemon=True)
        a.start()
        b.start()
        a.join()
        b.join()
        try:
            tls.close()
            up.close()
        except Exception:
            pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def cert_dns() -> str:
    """从服务器证书里读出第一个 DNS 名（用于打印手机可访问地址）。"""
    try:
        import ssl as _ssl

        d = _ssl._ssl._test_decode_cert(str(CERT))
        names = [v for k, v in d.get("subjectAltName", []) if k == "DNS"]
        return names[0] if names else ""
    except Exception:
        return ""


def main():
    if not (CERT.exists() and KEY.exists()):
        sys.exit("缺少证书：先运行 bash scripts/gen_https_cert.sh")
    bind = sys.argv[1] if len(sys.argv) > 1 else default_bind()
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8443
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(CERT), str(KEY))
    srv = Server((bind, port), Handler)
    srv.ctx = ctx
    print(f"🔒 HTTPS {bind}:{port} → http://127.0.0.1:8765（手机访问用，Ctrl+C 退出）")
    dns = cert_dns()
    if dns:
        print(f"📱 手机浏览器打开:  https://{dns}:{port}")
    print(f"   备用地址（Tailscale IP）:  https://{bind}:{port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
