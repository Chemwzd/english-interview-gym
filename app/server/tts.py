"""文本转语音：macOS say（默认，零成本）/ TokenHub MiniMax（控制台开通后付费后可用）。

TokenHub 接口：POST /v1/wand/minimax-tts/sync_tts
  入参：{model, text, voice_setting:{voice_id,...}, audio_setting:{format:'mp3'}, output_format:'hex'}
  出参：data.audio（hex 音频；若 output_format=url 则为 24h 有效链接）
"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

import requests

from . import config


class TTSError(RuntimeError):
    pass


def _cache_path(text: str, tag: str) -> Path:
    h = hashlib.md5((tag + "|" + text).encode("utf-8")).hexdigest()[:16]
    d = config.data_dir() / "audio" / "tts_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{h}.mp3"


def synth_say(text: str) -> bytes:
    voice = config.get("tts.say_voice", "Samantha")
    rate = int(config.get("tts.say_rate", 170))
    tmp = Path(tempfile.mkdtemp(prefix="et_tts_"))
    aiff, mp3 = tmp / "a.aiff", tmp / "a.mp3"
    p = subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], capture_output=True, text=True)
    if p.returncode != 0 or not aiff.exists():
        # 音色不存在时退回系统默认音色
        subprocess.run(["say", "-r", str(rate), "-o", str(aiff), text], check=True, capture_output=True)
    subprocess.run(
        [config.ffmpeg_path(), "-y", "-i", str(aiff), "-codec:a", "libmp3lame", "-qscale:a", "4", str(mp3)],
        check=True,
        capture_output=True,
    )
    return mp3.read_bytes()


def synth_tokenhub(text: str, voice_id: str = None) -> bytes:
    key = config.tokenhub_key()
    r = requests.post(
        "https://tokenhub.tencentmaas.com/v1/wand/minimax-tts/sync_tts",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json={
            "model": config.get("tts.tokenhub_model", "minimax-speech-2.8-turbo"),
            "text": text,
            "voice_setting": {
                "voice_id": voice_id or config.get("tts.tokenhub_voice_id", "English_Graceful_Lady"),
                "speed": 1.0,
            },
            "audio_setting": {"format": "mp3", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
            "output_format": "hex",
        },
        timeout=120,
    )
    if r.status_code != 200:
        raise TTSError(f"TokenHub TTS HTTP {r.status_code}: {r.text[:300]}")
    j = r.json()
    d = j.get("data") or j
    audio = d.get("audio") or ""
    if isinstance(audio, str) and audio.startswith("http"):
        return requests.get(audio, timeout=120).content
    if not audio:
        raise TTSError(f"TTS 返回无音频字段: {str(j)[:300]}")
    return bytes.fromhex(audio)


def synth(text: str, persona: str = None) -> bytes:
    text = (text or "").strip()
    if not text:
        raise TTSError("empty text")
    driver = config.get("tts.driver", "macos_say")
    voice_id = None
    if persona:
        voice_id = (config.get("tts.voices") or {}).get(persona)
    tag = f"{driver}|{voice_id or config.get('tts.tokenhub_voice_id', '') or config.get('tts.say_voice', '')}"
    cache = _cache_path(text, tag)
    if config.get("tts.cache", True) and cache.exists():
        return cache.read_bytes()
    if driver == "tokenhub":
        try:
            data = synth_tokenhub(text, voice_id=voice_id)
        except Exception:
            data = synth_say(text)  # 云端异常时保证可用
    else:
        data = synth_say(text)
    if config.get("tts.cache", True):
        cache.write_bytes(data)
    return data
