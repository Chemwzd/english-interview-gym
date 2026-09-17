# -*- coding: utf-8 -*-
"""Windows 免安装版入口：启动本地服务并自动打开浏览器。

- 数据/配置/素材都放在 exe 旁边的文件夹（首启自动释放默认素材）。
- 若检测到已在运行，则直接打开浏览器，不重复启动。
"""
import socket
import sys
import threading
import time
import webbrowser


def _pick_port(preferred: int = 8765) -> int:
    for p in range(preferred, preferred + 20):
        try:
            with socket.socket() as s:
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    return preferred


def _already_running(port: int = 8765) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1.5) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def main() -> None:
    try:
        sys.stdout.reconfigure(errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    if _already_running():
        url = "http://127.0.0.1:8765"
        print(f"✅ 服务已在运行，直接打开浏览器：{url}")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return

    from server.main import app  # noqa: E402  （导入即完成配置/素材引导）
    import uvicorn  # noqa: E402

    port = _pick_port()
    url = f"http://127.0.0.1:{port}"

    def _open() -> None:
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()
    print("=" * 58)
    print("  英语面试健身房 · 本地服务已启动")
    print(f"  浏览器地址：{url}")
    print("  提示：首次使用请在页面里点「⚙️ 设置」填入接口地址与 API Key。")
    print("  关闭本窗口 = 停止服务；数据保存在本文件夹内。")
    print("=" * 58)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
