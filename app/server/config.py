"""配置加载：app/config.yaml + app/.env。"""
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # EngTraining/
_ENV = {}


def _load_env_file():
    p = ROOT / "app" / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        _ENV[k.strip()] = v.strip().strip('"').strip("'")


_load_env_file()
_CFG = None


def load():
    global _CFG
    if _CFG is None:
        p = ROOT / "app" / "config.yaml"
        _CFG = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return _CFG


def get(path, default=None):
    d = load()
    for part in str(path).split("."):
        if not isinstance(d, dict) or part not in d:
            return default
        d = d[part]
    return d


def env(name, default=None):
    """进程环境变量优先，其次 app/.env 文件。"""
    return os.environ.get(name) or _ENV.get(name) or default


def api_key():
    return env("API_KEY", "")


def data_dir() -> Path:
    d = ROOT / get("paths.data_dir", "data")
    d.mkdir(parents=True, exist_ok=True)
    return d


def materials_dir() -> Path:
    return ROOT / get("paths.materials_dir", "materials")


def ffmpeg_path() -> str:
    return get("tools.ffmpeg") or "ffmpeg"
