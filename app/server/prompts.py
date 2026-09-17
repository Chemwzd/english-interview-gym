"""提示词、人格、题库、示范答案生成。"""
import json
from pathlib import Path

import yaml

from . import config


def load_persona(key: str) -> dict:
    """从 materials/personas/<key>.md 读取：标题、说明、'### system' 后的系统提示。"""
    p = config.materials_dir() / "personas" / f"{key}.md"
    if not p.exists():
        raise FileNotFoundError(f"persona not found: {p}")
    text = p.read_text(encoding="utf-8")
    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    sys_prompt = ""
    marker = "### system"
    if marker in text:
        sys_prompt = text.split(marker, 1)[1].strip()
    return {"key": key, "title": title or key, "system": sys_prompt}


def list_personas() -> list:
    d = config.materials_dir() / "personas"
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("*.md")):
        try:
            out.append(load_persona(p.stem))
        except Exception:
            continue
    return [{"key": x["key"], "title": x["title"]} for x in out]


def load_question_set(key: str) -> dict:
    p = config.materials_dir() / "question-bank" / f"{key}.yml"
    if not p.exists():
        raise FileNotFoundError(f"question set not found: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def list_question_sets() -> list:
    d = config.materials_dir() / "question-bank"
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("*.yml")):
        try:
            j = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            out.append({"key": p.stem, "title": j.get("title", p.stem), "count": len(j.get("questions", []))})
        except Exception:
            continue
    return out


def load_profile() -> str:
    """读取个人资料（materials/profile.md，由首页『我的简历』导入生成）。
    文件不存在/过短 → 视为未提供个人资料（示范答案将只生成通用版，保证零个人信息可用）。"""
    p = config.materials_dir() / "profile.md"
    try:
        t = p.read_text(encoding="utf-8").strip()
        return t if len(t) >= 40 else ""
    except Exception:
        return ""


def load_question_meta() -> dict:
    """题目元信息（每题的中文短标题等展示字段），数据文件：materials/question-bank/meta.json。"""
    p = config.materials_dir() / "question-bank" / "meta.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ---------------------------------------------------------------- 示范答案

def suggestion_messages(question: str, profile: str = "") -> list:
    common = """面试官真正期待的：开口一秒抓住结论；30–45 秒说完；用一个具体证据（方法/数字/结果）支撑；干脆收尾；宁可精炼不啰嗦；不要背稿腔、不要客套铺垫。
共同要求：
- 自然口语化的美式商务英语；纯口语文本：不要 markdown、不要标题、不要动作说明；
- 除方括号占位符外只允许英文，严禁出现中文字符；
- 严禁复述或提及任务说明本身（如"我需要写""候选人资料"等），直接从答案第一句开始。"""
    generic_block = """【generic（通用版）】
- 不依赖具体经历、任何候选人都能直接套用的框架答案，第一人称；
- 50–85 个英文单词，绝不超过 95 词；
- 需替换的个人信息用英文方括号占位，如 [your project]、[a key metric]、[company name]；
- 语气自然、像真人在说，不是模板腔。"""
    if profile:
        sys = f"""你是一位资深外企/商务面试教练。针对同一个面试问题写两版「可直接说出口」的短示范答案。

{common}

【personal（我的经历定制版）】
- 严格基于「候选人资料」中的真实经历与数字，第一人称，像本人临场作答；
- 60–100 个英文单词（口语约 30–45 秒），绝不超过 110 词；
- 结构：直接回应问题 → 一个最相关的具体证据（方法/数字/结果）→ 一句收尾或留出可追问的钩子。

{generic_block}

只输出一个 JSON 对象：{{"personal": "...", "generic": "..."}}"""
        user = f"候选人资料：\n{profile}\n\n面试问题：{question}"
    else:
        sys = f"""你是一位资深外企/商务面试教练。针对一个面试问题写一版「可直接说出口」的短示范答案（通用框架版——用户尚未提供个人资料，不要编造任何具体经历）。

{common}

{generic_block}

只输出一个 JSON 对象：{{"generic": "..."}}"""
        user = f"面试问题：{question}"
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------- 即时反馈

FEEDBACK_SCHEMA = """{
  "verdict": "<总结（中文）：先肯定一个具体优点，再点出最关键的一条改进>",
  "score": <1-10 整数：本回答的综合表现分（内容完整性 × 表达质量 × 流利度整体印象；7=合格、8=良好、9=优秀、10=接近母语面试水准）>,
  "content_gap": "<内容层面缺什么：结构/例子/数字/立场（中文一句；照读模式填 null）>",
  "language_point": {"original": "<候选人原句片段（英文）>", "better": "<更自然或更正确的说法（英文）>", "explain": "<中文讲解 10-40 字>", "type": "grammar|vocab|structure"},
  "upgrade": {"original": "<候选人原句片段（英文）>", "better": "<不装但更高级的说法（英文）>", "explain": "<中文讲解>", "type": "vocab|structure"},
  "polished": "<把整段回答润色为自然的英文口语版：保留信息与观点，修正语法/用词/结构，可直接照着说；自由说模式必填，照读模式填 null>",
  "followup": "<面试官会追问的下一句（英文）；没有就填 null>"
}"""


def feedback_messages(persona: dict, question: str, transcript: str, history: list, mode: str = "free", script: str = "") -> list:
    mode_block = ""
    if mode == "read":
        mode_block = (
            "\n\n【本次为「照读模式」】：候选人是照着下面的示范答案朗读的（可能有漏读/改读）。\n"
            "- content_gap 填 null；不要给内容建议。\n"
            "- 聚焦朗读表现：与脚本的差异（漏读、改读、添词）、发音清晰度、节奏与停顿、语调。\n"
            "- polished 填 null。\n"
            "- verdict 仍要有：先说朗读优点，再给 1 条最关键改进。\n"
            "【示范答案（供对比）】：\n" + (script or "")[:2500]
        )
    sys = f"""你同时扮演两个角色，为同一段面试回答产出一次反馈。

【角色A · 面试官】{persona.get('system', '')}

【角色B · 隐形教练】为一名中文母语的候选人提供英文面试口语训练反馈（目标：技术面试流利自如）。
硬性要求：
- 严格基于候选人原话，不得虚构错误；句子没问题时不要鸡蛋里挑骨头，改为"升级"建议。
- 转写可能含语音识别噪声：若某词只出现一次、形态怪异（例如把标准术语转成了不存在的拼写），不要当作候选人的语言错误（可跳过该点）。
- 字段语言：verdict/explain 用中文；original/better/followup/polished 用英文。
- followup 要贴合岗位语境，追问上一答里最薄弱的一点（缺数字、缺细节、逻辑跳跃等），保持角色A 的口吻；若回答完整且具体，可为 null。
- 只输出一个 JSON 对象，不要解释、不要 markdown 代码块。结构：
{FEEDBACK_SCHEMA}{mode_block}"""
    msgs = [{"role": "system", "content": sys}]
    for h in (history or [])[-6:]:
        msgs.append({"role": "user", "content": f"[面试官] {h.get('question', '')}"})
        msgs.append({"role": "user", "content": f"[候选人·转写] {h.get('transcript', '')}"})
    msgs.append({"role": "user", "content": f"[面试官] {question}\n\n[候选人·转写（ASR 自动识别，可能有转写误差）]\n{transcript}\n\n请按 JSON 输出反馈。"})
    return msgs


# ---------------------------------------------------------------- 收场复盘

def review_messages(persona: dict, qa_list: list) -> list:
    sys = """你是英语面试教练。基于整场会话记录产出复盘报告（中文为主，例句保留英文）。
只输出一个 JSON 对象，结构：
{
 "scores": {"content": 1-5, "structure": 1-5, "grammar": 1-5, "lexical": 1-5, "fluency": 1-5},
 "strengths": ["最多3条"],
 "issues": [{"type": "grammar|vocab|structure|content|delivery", "pattern": "反复出现的问题", "example": "原句（英文）", "fix": "怎么改"}],
 "drills": ["下次训练前要练的 3 件事"],
 "next_focus": "下一次会话重点（一句话）"
}
要求：issues 按出现频率排序、最多 5 条；所有判断必须引用具体句子；不要客套话。"""
    body = []
    for i, qa in enumerate(qa_list, 1):
        dur = (qa.get("duration_ms") or 0) / 1000
        mode = "照读" if qa.get("mode") == "read" else "自由说"
        body.append(f"Q{i}: {qa.get('question', '')}\nA{i}（{mode}）: {qa.get('transcript', '')}\n(用时 {dur:.0f}s)")
    return [{"role": "system", "content": sys}, {"role": "user", "content": "\n\n".join(body)}]


# ---------------------------------------------------------------- 单词速查（Speakey 式点词）

def gloss_messages(word: str, context: str) -> list:
    sys = """你是面向中文母语者的英语学习词典。用户会给你一个单词/短语和它出现的上下文（面试场景）。
输出一个 JSON 对象：
{
 "word": "<原词或短语>",
 "ipa": "<美式音标，不含斜杠>",
 "pos": "<词性简写：n./v./adj./adv./phrase/其他>",
 "zh": "<结合此上下文最贴切的中文释义（10-30 字）>",
 "example_en": "<一个面试场景中的简短英文例句>",
 "example_zh": "<例句中文翻译>",
 "note": "<可选：用法/搭配/易混提醒（中文，20 字内；没有则空字符串）>"
}
只输出 JSON，不要任何解释。"""
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": f"单词：{word}\n上下文（面试回答片段）：{(context or '')[:600]}"},
    ]
