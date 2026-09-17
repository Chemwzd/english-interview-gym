"""大模型客户端（OpenAI 兼容）。"""
import json

import requests

from . import config


class LLMError(RuntimeError):
    pass


def extract_json(s: str):
    """从模型输出中提取第一个完整 JSON 对象（容忍 markdown 包裹）。"""
    if not s:
        return None
    t = s.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    start = t.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(t[start : i + 1])
                    except Exception:
                        return None
    return None


class LLM:
    def __init__(self):
        # 接口地址：环境变量 API_BASE_URL 优先，其次 config.yaml（便于开源用户自带服务）
        self.base = (config.env("API_BASE_URL") or config.get("llm.base_url", "")).rstrip("/")
        self.key = config.api_key()
        if not self.base:
            raise LLMError("未配置接口地址：请在 app/.env 设置 API_BASE_URL，或在 app/config.yaml 设置 llm.base_url")
        self.models = [config.get("llm.model")] + list(config.get("llm.fallback_models") or [])
        self.timeout = config.get("llm.timeout_s", 120)

    def _once(self, model, messages, temperature, max_tokens):
        """单模型单次调用。默认关闭思考（更深更快的正文、避免思考内容泄漏）；
        对不认识 thinking 参数的模型自动去掉该参数重试；对只允许 temperature=1 的模型自动修正。
        注意：绝不用 reasoning_content 充当正文——那会把模型的内心草稿当答案输出（历史 bug）。"""
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if config.get("llm.disable_thinking", True):
            body["thinking"] = {"type": "disabled"}
        r = None
        for attempt in range(3):
            r = requests.post(
                self.base + "/chat/completions",
                headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
                json=body,
                timeout=self.timeout,
            )
            if r.status_code == 200:
                break
            text = r.text[:300]
            low = text.lower()
            if attempt < 2 and "thinking" in low and r.status_code == 400 and body.get("thinking"):
                body.pop("thinking", None)  # 该模型不支持 thinking 参数
                continue
            if attempt < 2 and "temperature" in low and "only 1 is allowed" in low:
                body["temperature"] = 1  # kimi-k3 等模型只接受 1
                continue
            raise LLMError(f"HTTP {r.status_code}: {text}")
        j = r.json()
        ch = j["choices"][0]
        content = (ch["message"].get("content") or "").strip()
        if not content:
            fr = ch.get("finish_reason")
            rt = ((j.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens")
            raise LLMError(f"{model}: empty content (finish_reason={fr}, reasoning_tokens={rt})")
        return content

    def chat(self, messages, temperature=None, max_tokens=2000):
        temperature = config.get("llm.temperature", 0.6) if temperature is None else temperature
        last = None
        for m in self.models:
            try:
                out = self._once(m, messages, temperature, max_tokens)
                if out and out.strip():
                    return out
                last = LLMError(f"{m}: empty content")
            except Exception as e:
                last = e
        raise LLMError(f"all models failed: {last}")

    def chat_json(self, messages, temperature=0.2, max_tokens=2400, retries=2):
        msgs = list(messages)
        for _ in range(retries + 1):
            out = self.chat(msgs, temperature=temperature, max_tokens=max_tokens)
            obj = extract_json(out)
            if obj is not None:
                return obj
            msgs = messages + [
                {
                    "role": "user",
                    "content": "上一条输出不是有效 JSON。请只输出一个合法 JSON 对象，不要解释、不要 markdown 代码块。",
                }
            ]
        raise LLMError("JSON parse failed after retries")


_llm = None


def get_llm() -> LLM:
    global _llm
    if _llm is None:
        _llm = LLM()
    return _llm
