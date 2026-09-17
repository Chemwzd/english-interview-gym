"""口语指标计算（基于 ASR 文本 + 分句时间戳）。"""
import re

FILLERS = re.compile(r"\b(um+|uh+|er+|ah+|hmm+|you know|i mean)\b", re.I)


def compute(text: str, duration_ms: int, sentences: list) -> dict:
    text = text or ""
    words = len(re.findall(r"[A-Za-z']+", text))
    dur_s = max((duration_ms or 0) / 1000.0, 0.1)
    wpm = round(words / dur_s * 60, 1) if words else 0.0
    fillers = FILLERS.findall(text)
    filler_per_min = round(len(fillers) / dur_s * 60, 1) if fillers else 0.0
    long_pauses = 0
    ss = sentences or []
    for a, b in zip(ss, ss[1:]):
        gap = (b.get("begin_ms") or 0) - (a.get("end_ms") or 0)
        if gap >= 2000:
            long_pauses += 1
    lead_pause = (ss[0].get("begin_ms") or 0) if ss else 0
    return {
        "words": words,
        "duration_s": round(dur_s, 1),
        "wpm": wpm,
        "fillers": len(fillers),
        "fillers_per_min": filler_per_min,
        "long_pauses": long_pauses,
        "lead_pause_ms": lead_pause,
    }


_NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion",
}


def script_diff(transcript: str, script: str) -> dict:
    """照读模式：转写与脚本的词级对齐（准确率 + 漏读/多读清单）。
    数字词与阿拉伯数字容易互相转写（two thousand ↔ 2,000），对齐时从两侧剔除，避免误报。"""
    from difflib import SequenceMatcher

    def norm(s):
        return [w.lower() for w in re.findall(r"[A-Za-z']+", s or "") if w.lower() not in _NUMBER_WORDS]

    a, b = norm(script), norm(transcript)
    if not a:
        return {}
    sm = SequenceMatcher(None, a, b)
    matched = sum(bl.size for bl in sm.get_matching_blocks())
    missed, extra = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            missed += a[i1:i2]
        if tag in ("insert", "replace"):
            extra += b[j1:j2]
    return {
        "accuracy": round(matched / len(a) * 100, 1),
        "script_words": len(a),
        "spoken_words": len(b),
        "missed": missed[:40],
        "extra": extra[:40],
    }
