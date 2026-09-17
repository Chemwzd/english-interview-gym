#!/usr/bin/env python3
"""三条链路一键体检：LLM / ASR / TTS。
用法：.venv/bin/python scripts/check_stack.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from server import asr, config, tts  # noqa: E402
from server.llm import get_llm  # noqa: E402


def check_llm():
    r = get_llm().chat([{"role": "user", "content": "Reply with exactly: OK"}], temperature=0, max_tokens=200)
    print(f"[LLM]  model={config.get('llm.model')} -> {r.strip()[:60]!r}")


def make_sample_audio() -> Path:
    aiff = Path("/tmp/et_check.aiff")
    wav = Path("/tmp/et_check.wav")
    subprocess.run(
        ["say", "-v", config.get("tts.say_voice", "Samantha"), "-o", str(aiff),
         "Hi, this is a quick sound check for the English interview trainer."],
        check=True, capture_output=True,
    )
    subprocess.run([config.ffmpeg_path(), "-y", "-i", str(aiff), "-ar", "16000", "-ac", "1", str(wav)], check=True, capture_output=True)
    return wav


def check_asr():
    res = asr.transcribe(make_sample_audio())
    print(f"[ASR]  driver={res['driver']} dur={res['duration_ms']}ms -> {res['text'][:110]!r}")


def check_tts():
    data = tts.synth("Hello, this is the interviewer voice check.")
    print(f"[TTS]  driver={config.get('tts.driver')} bytes={len(data)}")


if __name__ == "__main__":
    for name, fn in (("LLM", check_llm), ("ASR", check_asr), ("TTS", check_tts)):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] FAIL: {e}")
    print("done.")
