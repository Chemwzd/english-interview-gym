# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置（Windows / macOS 免安装包）：在仓库根目录执行
#   pip install -r packaging/requirements-build.txt
#   pyinstaller packaging/EnglishInterviewGym.spec --distpath dist --workpath build_win
import os
import sys as _sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821  (SPECPATH 由 PyInstaller 注入)
ICON = os.path.join(SPECPATH, "icon.icns" if _sys.platform == "darwin" else "icon.ico")  # noqa: F821

datas = [
    (os.path.join(ROOT, "app", "web"), "app/web"),
    (os.path.join(ROOT, "app", "config.yaml"), "app"),
    (os.path.join(ROOT, "app", ".env.example"), "app"),
    (os.path.join(ROOT, "materials"), "materials_default"),
]
datas += collect_data_files("imageio_ffmpeg")  # 内置静态 ffmpeg（音频转码用）
datas += collect_data_files("pdfminer")        # PDF 解析引擎资源（CMap，中文等）

hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("server")
    + collect_submodules("pdfminer")
    + ["fastapi", "multipart", "yaml", "requests", "docx", "pypdf"]
)
if _sys.platform == "win32":  # 原生应用窗口（WebView2 外壳）：pywebview 及其资源
    try:
        datas += collect_data_files("webview")
        hiddenimports += collect_submodules("webview") + [
            "clr", "clr_loader", "proxy_tools", "bottle", "typing_extensions",
            "webview.platforms.edgechromium", "webview.platforms.winforms",
        ]
    except Exception:
        pass

a = Analysis(  # noqa: F821
    [os.path.join(SPECPATH, "win_launcher.py")],  # noqa: F821
    pathex=[os.path.join(ROOT, "app")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["mlx_whisper", "tkinter", "matplotlib", "numpy", "PIL"],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EnglishInterviewGym",
    debug=False,
    strip=False,
    upx=False,
    console=(_sys.platform != "win32"),  # Windows：无控制台黑框（GUI 子系统）
    icon=ICON,
)
coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="EnglishInterviewGym",
)
