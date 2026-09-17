"""语音识别：TokenHub Hy-ASR（主）/ 本地 mlx-whisper（兜底）。

TokenHub 接口：POST /v1/wand/asrproxy/sync_transcribe
  入参：{model, data(音频base64) | input_url, source, voice_encode_format}
  出参：output.{text, duration_ms, sentences:[{begin_ms,end_ms,text}], source}
注意：TokenHub 语音模型需先在控制台开启"后付费"（或领取免费体验包），
      否则会返回 402/401007；此时 auto 模式会自动退到本地模型。
"""
import base64
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import requests

from . import config


class ASRError(RuntimeError):
    pass


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise ASRError(f"cmd failed: {' '.join(cmd)}\n{(p.stderr or '')[:400]}")


def to_wav(src: Path) -> Path:
    """浏览器录音（webm/mp4/…）→ 16k 单声道 wav。"""
    dst = Path(tempfile.mkdtemp(prefix="et_asr_")) / "audio.wav"
    ff = config.ffmpeg_path()
    if not (shutil.which(ff) or Path(ff).exists()):
        raise ASRError(f"ffmpeg 不可用: {ff}")
    _run([ff, "-y", "-i", str(src), "-ar", "16000", "-ac", "1", "-f", "wav", str(dst)])
    return dst


def _wav_duration_ms(p: Path) -> int:
    try:
        with wave.open(str(p), "rb") as w:
            return int(w.getnframes() / w.getframerate() * 1000)
    except Exception:
        return 0


def transcribe_tokenhub(wav: Path, model: str = None) -> dict:
    key = config.tokenhub_key()
    model = model or config.get("asr.model", "hy-asr-3.0-preview")
    b64 = base64.b64encode(wav.read_bytes()).decode()
    r = requests.post(
        config.get("asr.endpoint"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json={
            "model": model,
            "data": b64,
            "source": config.get("asr.source", "en"),
            "voice_encode_format": "wav",
        },
        timeout=config.get("asr.timeout_s", 180),
    )
    if r.status_code != 200:
        raise ASRError(f"TokenHub ASR HTTP {r.status_code}: {r.text[:300]}")
    j = r.json()
    out = j.get("output") or {}
    return {
        "driver": "tokenhub",
        "text": (out.get("text") or "").strip(),
        "duration_ms": out.get("duration_ms") or _wav_duration_ms(wav),
        "sentences": out.get("sentences") or [],
        "source": out.get("source"),
        "usage": j.get("usage"),
        "model": model,
    }


def transcribe_local(wav: Path) -> dict:
    try:
        import mlx_whisper  # type: ignore
    except Exception as e:
        raise ASRError(f"本地 ASR 不可用（未安装 mlx-whisper）: {e}")
    model = config.get("asr.local_model", "mlx-community/whisper-large-v3-turbo")
    try:
        res = mlx_whisper.transcribe(str(wav), path_or_hf_repo=model, language="en")
    except Exception:
        model = config.get("asr.local_fallback_model", "mlx-community/whisper-small")
        res = mlx_whisper.transcribe(str(wav), path_or_hf_repo=model, language="en")
    segs = res.get("segments") or []
    sentences = [
        {
            "begin_ms": int(s.get("start", 0) * 1000),
            "end_ms": int(s.get("end", 0) * 1000),
            "text": (s.get("text") or "").strip(),
        }
        for s in segs
    ]
    return {
        "driver": "local",
        "text": (res.get("text") or "").strip(),
        "duration_ms": _wav_duration_ms(wav),
        "sentences": sentences,
        "source": "en",
        "usage": None,
        "model": model,
    }


def transcribe(audio_path) -> dict:
    """driver=auto：云端多引擎逐个尝试（hy → wand）→ 本地兜底。"""
    driver = config.get("asr.driver", "auto")
    wav = to_wav(Path(audio_path))
    errors = []
    if driver in ("auto", "tokenhub"):
        models = [config.get("asr.model", "hy-asr-3.0-preview")] + list(config.get("asr.fallback_models") or [])
        for m in models:
            try:
                return transcribe_tokenhub(wav, model=m)
            except Exception as e:  # noqa: BLE001
                errors.append(f"tokenhub/{m}: {e}")
    if driver in ("auto", "local"):
        try:
            return transcribe_local(wav)
        except Exception as e:  # noqa: BLE001
            errors.append(f"local: {e}")
    raise ASRError(" | ".join(errors))
