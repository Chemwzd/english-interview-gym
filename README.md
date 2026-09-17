<p align="center">
  <img src="docs/logo.png" width="104" alt="English Interview Gym — logo">
</p>

<h1 align="center">English Interview Gym<br>英语面试健身房</h1>

<p align="center">
  <b>Self-hosted AI English interview trainer — voice mock interviews, instant corrections, click-to-lookup vocabulary, and progress you can actually see.</b><br>
  <b>本地部署的 AI 英语面试训练系统：语音模拟面试 · 即时纠错 · 点词速查 · 看得见的进步。</b>
</p>

<p align="center">
  <a href="#english"><b>🇬🇧 English</b></a> · <a href="#chinese"><b>🇨🇳 简体中文</b></a><br><br>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg" alt="Python 3.12">
  <img src="https://img.shields.io/badge/BYOK-bring%20your%20own%20API%20key-orange.svg" alt="BYOK">
  <img src="https://img.shields.io/badge/Data-100%25%20local-brightgreen.svg" alt="Local data">
</p>

<p align="center">
  <img src="docs/hero.png" width="860" alt="Speaking into a microphone while the AI interviewer replies, gives corrections and tracks progress">
</p>

---

<a id="english"></a>

# 🇬🇧 English

## What is this?

**English Interview Gym** is a personal training system that runs entirely on **your own computer**. It turns the classic interview-prep routine ("practice speaking, get feedback, repeat") into a turn-based voice loop with an AI interviewer:

**AI interviewer asks → you answer out loud → instant feedback & a polished revision → next question** — and every answer is scored, logged, and visualized so you can watch yourself improve week over week.

It was built for the "daily English → fluent business / interview English" journey: daily 20-minute sessions, one question at a time. All data (recordings, transcripts, reports, your resume) stays **local**, and you bring **your own API key**.

## ✨ Features

<p align="center"><img src="docs/features.png" width="860" alt="Feature overview: microphone (mock interview), feedback bubble (instant corrections), magnifying glass over a word card (click-word lookup), rising chart with flame (history & streaks)"></p>

| | Feature | What it does |
|---|---|---|
| 🎙️ | **Voice mock interviews** | 3 AI interviewer personas (friendly HR / technical lead / stress interviewer). The interviewer speaks (TTS), you answer out loud (speech recognition), with natural follow-up questions. |
| 📖 | **Sample answers, two versions** | Every question generates a lean 30–45 s business answer: a **generic framework version** out of the box; import your resume on the home page to unlock a **personalized version** grounded in your real experience. |
| 🔍 | **Click-word lookup** | Tap any English word in the conversation — see IPA, context-aware meaning, an example sentence and pronunciation; one click to save it to your vocabulary collection. |
| ✍️ | **Instant feedback** | Every answer gets **Correction / Upgrade / Revision** cards plus a 1–10 score. In reading mode you also get word-level accuracy against the script. |
| 🗂 | **Question card wall** | Each question set opens as a wall of illustrated cards (title, status, best score). Open any card to see **per-question history** — date, mode, duration, WPM, score — with a **trend line** of your scores over time. Start from any question, never from the top again. |
| 📅 | **Streaks & stats** | Duolingo-style streak panel: consecutive days, daily goal ring (minutes spoken), 7-day calendar with per-day bars, and milestone celebrations. |
| 📚 | **Session review & errorbook** | End a session to get a scored review report (content / structure / grammar / vocabulary / fluency) plus drills for next time. Recurring mistakes are auto-collected into an errorbook. |

## 📸 Screenshots

| | |
|---|---|
| ![Home: streak panel, tutors and question sets](docs/ui-home.png) | ![Question card wall with AI-generated illustrations](docs/ui-set.png) |
| ![Per-question history with score trend](docs/ui-qdetail.png) | ![Click-word lookup card](docs/ui-gloss.png) |
| ![Import your resume to unlock personalized answers](docs/ui-profile.png) | ![Streak milestone celebration](docs/ui-milestone.png) |

## 🚀 Quick Start

**Prerequisites**: Python 3.12, [`uv`](https://docs.astral.sh/uv/) (or pip), `ffmpeg` on PATH. macOS is the first-class platform (optional local fallbacks use macOS `say` / `mlx-whisper`); on other systems the cloud pipeline works the same.

```bash
# 1) Clone & install
git clone https://github.com/Chemwzd/english-interview-gym.git
cd english-interview-gym
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r app/requirements.txt

# 2) Configure YOUR OWN API key (never committed — .env is gitignored)
cp app/.env.example app/.env
#    Then edit app/.env and set TOKENHUB_API_KEY=your-key
#    Get a key at https://console.cloud.tencent.com/tokenhub
#    (LLM + speech recognition + TTS share one key. Voice models require
#     enabling "postpaid billing" in the console, otherwise you'll get a 402.)

# 3) Run
bash scripts/run_server.sh            # then open http://127.0.0.1:8765
# macOS: or just double-click `打开训练系统.command` in the project root
```

Health check for all three pipelines (LLM / ASR / TTS):

```bash
.venv/bin/python scripts/check_stack.py
```

> 💡 **Use any OpenAI-compatible gateway**: set `TOKENHUB_BASE_URL` in `app/.env` and change `llm.model` in `app/config.yaml`.
> 💡 **Fully offline speech**: set `asr.driver: local` (needs `mlx-whisper`, macOS) and `tts.driver: macos_say` in `app/config.yaml`.

## ⚙️ Configuration

### Environment variables (`app/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `TOKENHUB_API_KEY` | ✅ | One key for LLM + ASR + TTS (Tencent Cloud TokenHub, or any compatible gateway) |
| `TOKENHUB_BASE_URL` | – | Override the API base URL (any OpenAI-compatible gateway) |
| `TENCENTCLOUD_SECRET_ID` / `SECRET_KEY` | – | Only for the optional VOD image-generation scripts |
| `TENCENTCLOUD_REGION` | – | Default `ap-guangzhou` |
| `TENCENTCLOUD_VOD_SUB_APP_ID` | – | Only for VOD image generation |

### `app/config.yaml` highlights

- `llm.model` / `llm.fallback_models` — the models used for feedback & sample answers (default `deepseek/deepseek-flash`);
- `asr.driver` / `asr.model` — `auto` (cloud-first with local fallback), or pin `tokenhub` / `local`;
- `tts.driver` / `tts.voices` — cloud TTS voice per interviewer persona, or macOS `say` fallback;
- `session.daily_goal_minutes`, `session.max_answer_seconds` — training parameters;
- `tools.ffmpeg` — ffmpeg path if it's not on your PATH.

## 🎯 Make it yours

- **Question banks** — plain YAML, edit or add files under `materials/question-bank/`:

  ```yaml
  key: my-bank
  title: My question set
  questions:
    - id: q1
      round: HR screen
      category: Intro
      text: "Tell me about yourself."
      intent: Why they ask this.
      hint: How to structure your answer.
      followups:
        - "What's the one thing you want me to remember?"
  ```

- **Interviewer personas** — `materials/personas/*.md`; write your own character in the `### system` block.
- **Your story bank** — copy `materials/stories/template.md` to start a private bank of 5–8 polished personal stories (the strongest interview asset you can have).
- **Question illustrations** — already included for the bundled banks. To generate more with Tencent VOD AIGC: `python3 scripts/gen_question_meta.py` then `python3 scripts/gen_question_images.py` (optional; needs Tencent Cloud credentials and the `tencent-vod` image script, configurable via `VOD_IMAGE_SCRIPT`). Cards without images simply show a placeholder — nothing else depends on this.

## 🔒 Privacy

- `app/.env` (your keys), `materials/profile.md` (your imported resume) and `data/` (recordings, transcripts, reports) are **gitignored and never uploaded anywhere**;
- The resume you import is stored as a local file and is only sent to the AI endpoint **you** configured;
- This public repository itself contains **no personal data** of any kind.

## 🗂 Project structure

```
app/        FastAPI server (server/) + single-page frontend (web/)
materials/  personas · question-bank (+images) · stories template · wordlist · profile.example
scripts/    run_server · check_stack · baseline_report · question meta & image generation
data/       runtime data (local only): sessions · reports · audio · errorbook
docs/       RUNBOOK · PRACTICE-PLAN · screenshots
```

## ❓ FAQ

| Symptom | Fix |
|---|---|
| `402 / 401007` on submit | Voice models need "postpaid billing" enabled in the TokenHub console; or set `asr.driver: local` |
| Microphone unavailable | Open via `http://127.0.0.1` (not LAN IP); allow mic permission in browser |
| Port already in use | Change `server.port` in `app/config.yaml` and `--port` in `scripts/run_server.sh` |
| Want different voices | Cloud: `tts.voices` in config; local: `say -v '?'` + `tts.say_voice` |
| Want a different LLM | Set `TOKENHUB_BASE_URL` + `llm.model` to any OpenAI-compatible endpoint |

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<a id="chinese"></a>

# 🇨🇳 简体中文

## 这是什么？

**英语面试健身房**是一个完全跑在**你自己电脑上**的 AI 英语面试训练系统。它把"开口练 → 拿反馈 → 再练"的经典备考流程，变成一个和 AI 面试官之间的回合制语音循环：

**面试官提问 → 你开口回答 → 即时反馈 + 润色修订 → 下一题** —— 每次作答都会被评分、记录、可视化，让你每周都看得到自己的进步曲线。

它面向"日常英语 → 商务 / 英文面试流利"的进阶路线：每天 20 分钟，一次一题。所有数据（录音、转写、报告、简历）**只留在本机**，API Key **完全用你自己的**。

## ✨ 功能

<p align="center"><img src="docs/features.png" width="860" alt="功能总览：麦克风（模拟面试）、反馈气泡（即时纠错）、单词放大镜（点词速查）、趋势火焰（历史与打卡）"></p>

| | 功能 | 说明 |
|---|---|---|
| 🎙️ | **语音模拟面试** | 3 种 AI 面试官人格（友善 HR / 技术官 / 压力面）：面试官语音提问，你开口作答（语音识别转写），带自然的追问环节。 |
| 📖 | **示范答案 · 双版本** | 每题生成 30–45 秒的商务短答：开箱即用的 **🧩 通用框架版**；在首页导入简历后，额外解锁基于你真实经历的 **🎯 个人定制版**。 |
| 🔍 | **点词速查** | 对话中任意英文单词可点击：音标、结合语境的释义、例句、发音；一键收藏到生词本。 |
| ✍️ | **即时反馈** | 每次作答给出 **Correction / Upgrade / Revision** 三段卡片 + 1–10 综合分；照读模式还有逐词比对准确率。 |
| 🗂 | **题目卡片墙** | 题集以"卡片墙"展开（配图 + 中文短标题 + 练习状态 + 最高分）；点开任意一题可看**每次练习历史**（日期/模式/时长/语速/分数）与**分数趋势曲线**——从任意一题开练，再也不用从头刷。 |
| 📅 | **打卡与统计** | Duolingo 式打卡面板：连续天数、每日目标环（开口分钟数）、7 天日历柱状图、连胜里程碑庆祝。 |
| 📚 | **整场复盘 & 错题本** | 结束一场训练生成评分报告（内容/结构/语法/词汇/流利度）+ 下次练习清单；反复出现的问题自动进错题本。 |

## 📸 界面截图

| | |
|---|---|
| ![首页：打卡面板、导师选题集](docs/ui-home.png) | ![题目卡片墙（AI 生成插画）](docs/ui-set.png) |
| ![单题历史与分数趋势](docs/ui-qdetail.png) | ![点词查释义](docs/ui-gloss.png) |
| ![导入简历解锁定制版回答](docs/ui-profile.png) | ![连胜里程碑庆祝](docs/ui-milestone.png) |

## 🚀 快速开始

**环境要求**：Python 3.12、[`uv`](https://docs.astral.sh/uv/)（或 pip）、PATH 里有 `ffmpeg`。macOS 是一等平台（本地兜底方案用 macOS 的 `say` / `mlx-whisper`）；其他系统直接用云端链路即可。

```bash
# 1) 克隆并安装依赖
git clone https://github.com/Chemwzd/english-interview-gym.git
cd english-interview-gym
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r app/requirements.txt

# 2) 配置你自己的 API Key（永不入库——.env 已被 gitignore）
cp app/.env.example app/.env
#    编辑 app/.env，填入 TOKENHUB_API_KEY=你的key
#    申请入口: https://console.cloud.tencent.com/tokenhub
#    （LLM/语音识别/语音合一共用一个 Key；语音模型需在控制台开通"后付费"，否则会报 402）

# 3) 启动
bash scripts/run_server.sh            # 然后打开 http://127.0.0.1:8765
# macOS 也可以直接双击项目根目录的 `打开训练系统.command`
```

三条链路体检（LLM / 语音识别 / 语音合成）：

```bash
.venv/bin/python scripts/check_stack.py
```

> 💡 **换任何 OpenAI 兼容网关**：`app/.env` 里设置 `TOKENHUB_BASE_URL`，并改 `app/config.yaml` 的 `llm.model`。
> 💡 **完全离线语音**：`app/config.yaml` 里把 `asr.driver` 设为 `local`（需 `mlx-whisper`，限 macOS）、`tts.driver` 设为 `macos_say`。

## ⚙️ 配置说明

### 环境变量（`app/.env`）

| 变量 | 必填 | 用途 |
|---|---|---|
| `TOKENHUB_API_KEY` | ✅ | LLM + 语音识别 + 语音合成共用一个 Key（腾讯云 TokenHub，或任何兼容网关） |
| `TOKENHUB_BASE_URL` | – | 覆盖接口地址（指向任意 OpenAI 兼容网关） |
| `TENCENTCLOUD_SECRET_ID` / `SECRET_KEY` | – | 仅"VOD 生图脚本"等可选功能需要 |
| `TENCENTCLOUD_REGION` | – | 默认 `ap-guangzhou` |
| `TENCENTCLOUD_VOD_SUB_APP_ID` | – | 仅 VOD 生图需要 |

### `app/config.yaml` 要点

- `llm.model` / `llm.fallback_models` —— 反馈与示范答案使用的模型（默认 `deepseek/deepseek-flash`）；
- `asr.driver` / `asr.model` —— `auto`（云端优先、本地兜底），也可固定 `tokenhub` / `local`；
- `tts.driver` / `tts.voices` —— 每个面试官人格的云端音色，或 macOS `say` 兜底；
- `session.daily_goal_minutes`、`session.max_answer_seconds` —— 训练参数；
- `tools.ffmpeg` —— ffmpeg 不在 PATH 时填绝对路径。

## 🎯 定制你自己的版本

- **题库**——普通 YAML，直接改 / 加 `materials/question-bank/` 下的文件：

  ```yaml
  key: my-bank
  title: 我的题库
  questions:
    - id: q1
      round: HR 初面
      category: 开场
      text: "Tell me about yourself."
      intent: 考察意图（为什么问这题）
      hint: 答题思路（怎么组织回答）
      followups:
        - "What's the one thing you want me to remember?"
  ```

- **面试官人格**——`materials/personas/*.md`，在 `### system` 块里写你自己的角色。
- **你的故事库**——复制 `materials/stories/template.md`，攒 5–8 个打磨过的个人故事（面试最强资产）。
- **题目配图**——内置题库已附带。想用腾讯云 VOD AIGC 继续生成：先跑 `python3 scripts/gen_question_meta.py`，再跑 `python3 scripts/gen_question_images.py`（完全可选；需腾讯云凭证与对应生图脚本，可用环境变量 `VOD_IMAGE_SCRIPT` 指定路径）。没有配图的题会显示首字占位，不影响任何其他功能。

## 🔒 隐私说明

- `app/.env`（你的密钥）、`materials/profile.md`（导入的简历）、`data/`（录音、转写、报告）**全部被 .gitignore 忽略，绝不入库、不上传**；
- 导入的简历只存本机文件，除了调用**你自己配置的** AI 接口外不经过任何第三方；
- 本公开仓库中不含任何个人信息。

## 🗂 目录结构

```
app/        FastAPI 服务（server/）+ 单页前端（web/）
materials/  personas 人格 · question-bank 题库（含配图）· stories 故事模板 · wordlist 词表 · profile.example
scripts/    启动 / 体检 / 周报 / 题目元信息与配图生成
data/       运行数据（仅本地）：sessions · reports · audio · errorbook
docs/       RUNBOOK 运行手册 · PRACTICE-PLAN 练习计划 · 界面截图
```

## ❓ 常见问题

| 症状 | 处理 |
|---|---|
| 提交后报 `402 / 401007` | TokenHub 语音模型需在控制台开启"后付费"；或把 `asr.driver` 设为 `local` |
| 麦克风不可用 | 必须用 `http://127.0.0.1` 打开（局域网 IP 不行）；浏览器里允许麦克风权限 |
| 端口被占用 | 改 `app/config.yaml` 的 `server.port`，同步改 `scripts/run_server.sh` 的 `--port` |
| 想换考官音色 | 云端：改 config 的 `tts.voices`；本地：`say -v '?'` 查看 + `tts.say_voice` |
| 想换大模型 | 设 `TOKENHUB_BASE_URL` + 改 `llm.model`，任何 OpenAI 兼容接口都行 |

## 📄 License

MIT —— 见 [LICENSE](LICENSE)。
