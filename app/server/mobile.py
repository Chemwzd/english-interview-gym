"""手机访问（HTTPS 通道）：一键启用 —— 内置证书生成 + TLS 终结器。

背景：iPhone / Android 的浏览器只允许在 HTTPS（安全上下文）下使用麦克风，
而局域网 HTTP 地址一律禁麦。本模块提供：
1. 自签 CA + 服务器证书生成（纯 Python，不依赖 openssl；SAN 覆盖
   Tailscale 域名 / Tailscale IP / 本机局域网 IP / localhost）；
2. TLS 终结器（纯标准库）：8443(HTTPS) → 127.0.0.1:8765。

证书目录：<项目根>/certs（打包模式 = exe 旁）。
默认绑定：检测到 Tailscale 时绑其 IP（仅 tailnet 内可达，最安全）；
          否则绑 0.0.0.0（局域网内可达）。
"""
import ipaddress
import socket
import socketserver
import ssl
import subprocess
import threading
from pathlib import Path

from . import config

_STATE = {"srv": None, "port": None, "thread": None, "bind": None}

_TS_CANDIDATES = [
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
    "tailscale",
    r"C:\Program Files\Tailscale\tailscale.exe",
    r"C:\Program Files (x86)\Tailscale\tailscale.exe",
]


def certs_dir() -> Path:
    return config.root_dir() / "certs"


def ca_path() -> Path:
    return certs_dir() / "ca.crt"


def _server_crt() -> Path:
    return certs_dir() / "server.crt"


def _server_key() -> Path:
    return certs_dir() / "server.key"


# ---------------------------------------------------------------- 环境探测

def tailscale_info() -> dict:
    """返回 {"dns": "...", "ip": "100.x.y.z"}（未安装/未登录则为空串）。"""
    out = {"dns": "", "ip": ""}
    for ts in _TS_CANDIDATES:
        try:
            r = subprocess.run([ts, "status", "--json"], capture_output=True, text=True, timeout=6)
            if r.returncode != 0 or not (r.stdout or "").strip():
                continue
            import json

            d = json.loads(r.stdout)
            self_obj = d.get("Self") or {}
            out["dns"] = (self_obj.get("DNSName") or "").rstrip(".")
            r2 = subprocess.run([ts, "ip", "-4"], capture_output=True, text=True, timeout=6)
            ips = [x.strip() for x in (r2.stdout or "").splitlines() if x.strip()]
            if ips:
                out["ip"] = ips[0]
            if out["dns"] or out["ip"]:
                return out
        except Exception:
            continue
    return out


def lan_ips() -> list:
    ips = set()
    try:
        host = socket.gethostname()
        for fam, _, _, _, sa in socket.getaddrinfo(host, None):
            if fam == socket.AF_INET:
                try:
                    ipaddress.IPv4Address(sa[0])
                    ips.add(sa[0])
                except Exception:
                    pass
    except Exception:
        pass
    ips.discard("127.0.0.1")
    return sorted(ips)


# ---------------------------------------------------------------- 证书生成

def ensure_certs() -> dict:
    """生成自签 CA + 服务器证书（已存在则跳过）。返回 {"created": bool, "sans": [...]}。"""
    if _server_crt().exists() and _server_key().exists() and ca_path().exists():
        return {"created": False, "sans": _cert_dns()}
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime as _dt

    d = certs_dir()
    d.mkdir(parents=True, exist_ok=True)
    ts = tailscale_info()
    sans = []
    if ts["dns"]:
        sans.append(("dns", ts["dns"]))
    sans.append(("dns", "localhost"))
    if ts["ip"]:
        sans.append(("ip", ts["ip"]))
    for ip in lan_ips():
        sans.append(("ip", ip))
    sans.append(("ip", "127.0.0.1"))

    def _gen_key() -> "rsa.RSAPrivateKey":
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)

    now = _dt.datetime.now(_dt.timezone.utc)
    # CA（10 年）
    ca_key_path = d / "ca.key"
    if ca_key_path.exists() and ca_path().exists():
        ca_key = serialization.load_pem_private_key(ca_key_path.read_bytes(), password=None)
        ca_crt = x509.load_pem_x509_certificate(ca_path().read_bytes())
    else:
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "English Interview Gym Local CA")])
        ca_crt = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - _dt.timedelta(days=1))
            .not_valid_after(now + _dt.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(ca_key, hashes.SHA256())
        )
        ca_key_path.write_bytes(
            ca_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
        )
        ca_path().write_bytes(ca_crt.public_bytes(serialization.Encoding.PEM))

    # 服务器证书（825 天）
    key = _gen_key()
    cn = ts["dns"] or (lan_ips()[0] if lan_ips() else "localhost")
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    alt = []
    for kind, val in sans:
        alt.append(x509.DNSName(val) if kind == "dns" else x509.IPAddress(ipaddress.IPv4Address(val)))
    crt = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_crt.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - _dt.timedelta(days=1))
        .not_valid_after(now + _dt.timedelta(days=825))
        .add_extension(x509.SubjectAlternativeName(alt), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True, content_commitment=False,
                                     data_encipherment=False, key_agreement=False, key_cert_sign=False,
                                     crl_sign=False, encipher_only=False, decipher_only=False), critical=False)
        .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    _server_key().write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
    )
    _server_crt().write_bytes(crt.public_bytes(serialization.Encoding.PEM))
    return {"created": True, "sans": [f"{k}:{v}" for k, v in sans]}


def _cert_dns() -> list:
    try:
        import ssl as _ssl

        info = _ssl._ssl._test_decode_cert(str(_server_crt()))
        return [f"{k}:{v}" for k, v in info.get("subjectAltName", [])]
    except Exception:
        return []


# ---------------------------------------------------------------- TLS 终结器

class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            tls = self.server.ctx.wrap_socket(self.request, server_side=True)
            up = socket.create_connection(("127.0.0.1", 8765))
        except Exception:
            return

        def pipe(a, b):
            try:
                while True:
                    data = a.recv(65536)
                    if not data:
                        break
                    b.sendall(data)
            except Exception:
                pass
            finally:
                try:
                    b.shutdown(socket.SHUT_WR)
                except Exception:
                    pass

        t1 = threading.Thread(target=pipe, args=(tls, up), daemon=True)
        t2 = threading.Thread(target=pipe, args=(up, tls), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        try:
            tls.close()
            up.close()
        except Exception:
            pass


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _default_bind() -> str:
    ts = tailscale_info()
    return ts["ip"] or "0.0.0.0"


def start(port: int = 8443, bind: str = "") -> dict:
    """启用手机访问：生成证书（如需）+ 启动 TLS 终结器。已在运行则直接返回状态。"""
    if _STATE["srv"] is not None:
        return {"ok": True, "already": True, **status()}
    info = ensure_certs()
    bind = bind or _default_bind()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(_server_crt()), str(_server_key()))
    try:
        srv = _Server((bind, port), _Handler)
    except OSError as e:
        raise RuntimeError(f"端口 {port} 无法绑定（可能已被占用）：{e}")
    srv.ctx = ctx
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    _STATE.update({"srv": srv, "port": port, "thread": t, "bind": bind})
    try:  # 记住状态：应用下次启动时自动恢复
        config.save_config({"mobile": {"enabled": True, "port": port}})
    except Exception:
        pass
    return {"ok": True, "created_cert": info["created"], **status()}


def stop() -> dict:
    srv = _STATE.get("srv")
    if srv is not None:
        try:
            srv.shutdown()
            srv.server_close()
        except Exception:
            pass
    _STATE.update({"srv": None, "port": None, "thread": None, "bind": None})
    try:
        config.save_config({"mobile": {"enabled": False}})
    except Exception:
        pass
    return status()


def autostart() -> None:
    """应用启动时调用：上次处于启用状态则自动恢复（失败静默——如端口被占用）。"""
    try:
        if config.get("mobile.enabled"):
            start(port=int(config.get("mobile.port", 8443)))
    except Exception:
        pass


def status() -> dict:
    ts = tailscale_info()
    port = _STATE.get("port")
    urls = []
    if port:
        if ts["dns"]:
            urls.append(f"https://{ts['dns']}:{port}")
        if ts["ip"] and _STATE.get("bind") in (ts["ip"], "0.0.0.0"):
            urls.append(f"https://{ts['ip']}:{port}")
        for ip in lan_ips():
            if _STATE.get("bind") in (ip, "0.0.0.0"):
                urls.append(f"https://{ip}:{port}")
    return {
        "enabled": _STATE["srv"] is not None,
        "port": port,
        "bind": _STATE.get("bind"),
        "urls": urls,
        "tailscale": bool(ts["dns"] or ts["ip"]),
        "cert_ready": _server_crt().exists() and _server_key().exists() and ca_path().exists(),
        "ca_url": "/ca.crt",
        "ca_path": str(ca_path()),
    }


def run_forever(bind: str = "", port: int = 8443) -> None:
    """命令行入口（scripts/https_proxy.py）：阻塞式前台运行。"""
    r = start(port=port, bind=bind)
    print(f"🔒 HTTPS {r.get('bind')}:{r.get('port')} → http://127.0.0.1:8765（Ctrl+C 退出）")
    for u in r.get("urls", []):
        print(f"📱 手机浏览器打开：{u}")
    print(f"   证书下发页（手机首次安装用）：<上述地址>/ca.crt")
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        stop()
