<p align="center">
  <img src="docs/icon.png" width="110" alt="English Interview Gym — logo">
</p>

<h1 align="center">English Interview Gym</h1>

<p align="center">
  <b>Speak with AI interviewers for 20 minutes a day — turn everyday English into interview fluency.</b><br>
  <b>Voice mock interviews · live hints · click-to-lookup · instant corrections · streaks &amp; stats — 100% local, your data never leaves your computer.</b>
</p>

<p align="left">
  <a href="README_en.md"><b>English</b></a> | <a href="README.md"><b>中文</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg" alt="Python 3.12">
  <img src="https://img.shields.io/badge/BYOK-bring%20your%20own%20API%20key-orange.svg" alt="BYOK">
  <img src="https://img.shields.io/badge/Data-100%25%20local-brightgreen.svg" alt="Local data">
</p>

<p align="center">
  <img src="docs/overview.png" width="1100" alt="Overview: mock interviews · live hints · tap-to-translate · feedback reports · streaks">
</p>

## Contents

- [What is this](#what-is-this)
- [Quick start](#quick-start)
- [Model requirements & recommendations](#model-requirements--recommendations)
- [Feature guide](#feature-guide)
  - [Mock interviews](#mock-interviews)
  - [Sample answers &amp; hints](#sample-answers--hints)
  - [Click-to-lookup](#click-to-lookup)
  - [Instant feedback &amp; scoring](#instant-feedback--scoring)
  - [Session review &amp; errorbook](#session-review--errorbook)
  - [Streaks &amp; progress](#streaks--progress)
  - [Favourites &amp; daily review](#favourites--daily-review)
  - [Question card wall](#question-card-wall)
  - [Resume import](#resume-import)
- [Configuration](#configuration)
- [Customize &amp; extend](#customize--extend)
- [Project structure](#project-structure)
- [Privacy](#privacy)
- [Content sources & disclaimer](#content-sources--disclaimer)
- [FAQ](#faq)
- [License](#license)

## What is this

A self-hosted English interview trainer that runs on your own computer. The core loop is one thing only — **speaking out loud**:

> The AI interviewer asks (voice) → you answer out loud (transcribed) → instant corrections, a score, and a better way to say it → follow-up or next question

Every session feeds your streaks and stats; every question keeps a history, so you can re-practice it and watch a real improvement curve. Built for three common problems:

- **No one to practice with** — 3 AI interviewer personas × 82 curated questions (HR screen / technical / stress interview), available any time;
- **You don't know what to say** — every question ships with a 30–45 s sample answer (a **generic framework** version out of the box; import your resume to unlock a **personalized** version), every word across the app is one tap away from a definition, and a **read-aloud mode** covers the "I'm completely stuck" case;
- **No feedback after practice** — each answer gets Correction / Upgrade / Revision cards plus a 1–10 score; each session ends with a five-dimension review report and an errorbook.

| Feature | What it does | Where |
|---|---|---|
| 🎙️ Mock interviews | 3 personas × 3 question sets, voice Q&A with natural follow-ups | Home → "Choose your AI tutor" |
| 💡 Sample answers | A 30–45 s model answer per question: generic / personalized | Chat → "📖 Sample answer" |
| 🔍 Click-to-lookup | IPA · contextual meaning · examples · pronunciation · favourites | Any word, anywhere |
| ✍️ Instant feedback | Correction / Upgrade / Revision + 1–10 score | Automatic after each answer |
| 📋 Review report | Five-dimension scoring + next-focus + errorbook | Top-right "Review" |
| 🔥 Streaks & progress | Streak days · daily goal ring · review progress · 14-day calendar | Home check-in panel |
| ⭐ Favourites & daily review | Paged word library (sort / delete) + ratio-based daily recall | Home → "⭐ Favourites" |
| 🗂 Question card wall | 82 cards: status / best score / trend / per-question history | Home → "Choose a question set" |
| 📄 Resume import | Unlocks personalized answers grounded in your real experience | "📄 My resume" |

## Quick start

> 📖 **UI &amp; usage guide** (17 pages, full screenshots — follow along): [DOCX](docs/USER-GUIDE.docx) · [PDF](docs/USER-GUIDE.pdf)

**Requirements**: macOS (Apple Silicon recommended) + Python 3.12 + `ffmpeg` (`brew install ffmpeg`) + an API key (bring your own — any OpenAI-compatible service: official APIs or aggregator gateways). **On Windows, no Python is needed — use the portable build (section 7).**

### 1. Clone &amp; install

```bash
git clone https://github.com/KumquatYZ/english-interview-gym.git
cd english-interview-gym
python3 -m venv .venv            # or with uv: uv venv .venv --python 3.12
.venv/bin/pip install -r app/requirements.txt
```

### 2. Add your API key

```bash
cp app/.env.example app/.env     # then set API_KEY=your-key and API_BASE_URL=your-service-url
                                 # (the base URL can also live in app/config.yaml -> llm.base_url)
                                 # (one key covers the LLM + speech recognition + speech synthesis)
```

Or run the interactive setup helper (validates the key online before saving):

```bash
python3 scripts/setup_env.py
```

> Which models do you need (chat / speech recognition / speech synthesis), which are recommended, and what do they cost? → [Model requirements & recommendations](#model-requirements--recommendations)

### 3. Launch

```bash
bash scripts/run_server.sh       # or double-click "打开训练系统.command" on macOS
```

Open http://127.0.0.1:8765 (allow microphone access in your browser on first use).

### 4. Your first session (~10 minutes)

1. Home → "Choose your AI tutor" → preview voices and pick a persona;
2. "Choose a question set" → start with `baseline-8` (8 warm-up questions);
3. Open any card → "🎙 Practise from this question" → click the mic (or press Space) and speak;
4. Click the mic again to stop → read the transcript, feedback cards and score → next question;
5. When done, click "Review" (top-right) to generate the session report.

### 5. Health check &amp; weekly report (optional)

```bash
.venv/bin/python scripts/check_stack.py       # verify every pipeline: LLM / ASR / TTS
.venv/bin/python scripts/baseline_report.py   # practice weekly report
```

### 6. Use it on your phone (optional)

**Easiest path (recommended)**: open "**⚙️ 设置 (Settings) → 📱 手机访问 (Mobile access) → Enable**" — the app generates certificates and starts the HTTPS channel automatically, then shows the phone URL plus step-by-step setup (works for the macOS / Windows portable builds too).

To reach your computer from **any network** (not just the same Wi-Fi), install [Tailscale](https://tailscale.com/download) on both machines (free, private mesh; sign in with the same account) — when detected, mobile access binds to your tailnet only.

**One-time phone setup**:

- Install the CA: open the URL shown in Settings in Safari (accept the certificate warning) → then open `<that-url>/ca.crt` to download the profile → Settings → General → VPN & Device Management → install → then Settings → General → About → Certificate Trust Settings → enable full trust;
- Open the same URL in Safari → Share → **Add to Home Screen** — it then launches full-screen like an app.

> Note: the phone is a thin client — sessions and data stay on the computer running the app (keep it awake and online). CLI users can still use `bash scripts/gen_https_cert.sh` + `scripts/https_proxy.py` (equivalent to the in-app one-click flow).

### 7. Windows portable build (optional)

No Python required: grab `EnglishInterviewGym-win64.zip` from [**Releases**](https://github.com/KumquatYZ/english-interview-gym/releases/latest) → unzip → double-click `EnglishInterviewGym.exe` → the browser opens automatically → click "⚙️ 设置 (Settings)" and fill in your API base URL + key (config and data stay inside the app folder — fully portable, delete the folder to uninstall).

> Windows 10/11 (64-bit); an FFmpeg transcoding component is bundled. Mic permission is requested by the browser on first recording.

### 8. macOS portable build (optional: Apple Silicon)

Download `EnglishInterviewGym-macos.zip` from [**Releases**](https://github.com/KumquatYZ/english-interview-gym/releases/latest) → unzip → double-click 启动.command (if macOS blocks it the first time: right-click → Open) → the browser opens → configure via "⚙️ 设置". Config and data stay inside the folder — fully portable.

> macOS 12+, Apple Silicon (M-series); mobile access can be enabled from Settings with one click.

## Model requirements &amp; recommendations

A full session uses **three kinds of models** — not just a chat model. All three are called with the **single API key** you bring in `app/.env` (any OpenAI-compatible service: official APIs or aggregator gateways):

| Role | Where it's used | Recommended models (examples) | Reference price (CNY, pay-as-you-go) |
|---|---|---|---|
| 💬 Chat model | Follow-ups, sample answers, corrections & scoring, review reports, word glosses | **DeepSeek-V4.1-Flash** (`deepseek/deepseek-flash`, default); alternative **GLM-5.3-Flash** (`glm-5.3-flash`) | DeepSeek: ¥1–2 in / ¥4–8 out; GLM: ¥0.8 / ¥2.8 (per million tokens, off-peak/peak) |
| 🎙️ Speech recognition (ASR) | Transcribing your spoken answers | **Hy-ASR-3.0-Preview** (`hy-asr-3.0-preview`, default); alternative `wand-asr-v1` | Hy-ASR: ¥0.00022/s (~¥0.79/h); WAND: ¥0.0005/s |
| 🔊 Speech synthesis (TTS) | The interviewer's voice | **MiniMax-Speech-2.8-Turbo** (`minimax-speech-2.8-turbo`, default, 4 English voices included); `-hd` for higher quality | Turbo: ¥2 / 10k characters; HD: ¥3.5 / 10k characters |

**Cost estimate (20 min/day, everything in the cloud)**: chat ≈ ¥0.1/day + ASR ≈ ¥0.26/day + TTS ≈ ¥0.2–0.4/day ≈ **¥0.6–0.8/day, about ¥20/month** (pay-as-you-go; your actual bill depends on your provider. Evening practice usually falls into off-peak windows, where prices are lower).

**Both speech legs can run for free locally (macOS)**:

- `asr.driver: local` — on-device recognition with mlx-whisper (Apple Silicon, free);
- `tts.driver: macos_say` — macOS built-in `say` (free, robotic voice).

With both enabled, the only cost left is the chat model: **≈ ¥0.1/day**.

**Notes**:

- If a speech call returns `402 / 401007`: your provider likely hasn't enabled the speech models (commonly a "postpaid billing" toggle) — follow its console prompt once;
- Pricing is set by your provider (DeepSeek models commonly charge 2x during weekday 9:00–12:00 and 14:00–18:00 Beijing time; other hours are off-peak);
- The default fallback chain includes `kimi-k3` (pricier; only used if the primary model fails) — adjust `llm.fallback_models` if you care about cost.

To switch models, edit `app/config.yaml`: `llm.model` / `asr.model` / `tts.cloud_model` (all support fallback chains).

## Feature guide

### Mock interviews

**What it does**: a real back-and-forth conversation — the interviewer speaks a question, you answer out loud, and your speech is transcribed automatically before the follow-up or next question.

- 3 personas (`materials/personas/`): `hr-friendly` (corporate HR screen), `tech-lead` (technical deep-dive), `stress` (pressure round); each ships with its positioning, evaluation focus, probing strategy and a realistic interview-dialogue few-shot — adapt them to your own target role;
- 3 question sets: `baseline-8` (8 warm-up questions), `interview-core` (14 core questions), `mnc-60` (60 high-frequency big-tech questions).

**How to use**: pick a persona → pick a set → "🎙 Practise from this question" → click the mic (or press Space) → click again to finish → read the feedback → next question. Two answering modes are available in the chat header ("speak freely / read the sample aloud"); you can skip a question or end the session with "Review" at any time.

**How to configure**:
- Max answer length: `app/config.yaml` → `session.max_answer_seconds` (default 120 s);
- Voices: `app/config.yaml` → `tts.voices` (one voice per persona);
- Your own questions/sets: see [Customize &amp; extend](#customize--extend).

### Sample answers &amp; hints

**What it does**: before answering any question, see how it *could* be answered — a 30–45 s (about 60–100 words) model answer **benchmarked to real corporate-interview expectations** (lead with the answer, back it with evidence and numbers, no flattery or student-speak):

- **🧩 Generic version**: works out of the box, with `[bracketed]` placeholders you replace with your own details;
- **🎯 Personalized version**: unlocked after importing your resume — built from your real experience and numbers (see [Resume import](#resume-import)).

**How to use**: in the chat, click "📖 Sample answer" → switch between the two tabs → click "🎧 Read this aloud" to enter read-aloud mode.

**How to configure**: none needed; the personalized version depends on whether you imported a resume.

### Click-to-lookup

**What it does**: tap **any English word** in the conversation, sample answers, feedback cards or review reports and get IPA, part of speech, a **context-aware** meaning, an example sentence and pronunciation; one click saves it to your vocabulary. The same word gets different glosses in different contexts.

**How to use**: click a word → read the card → 🔊 hear it → ⭐ save it. Saved words go to "⭐ Favourites" where they can be reviewed daily and managed.

**How to configure**: none needed; lookups are cached in `data/gloss_cache.json`, so repeat lookups are instant.

### Instant feedback &amp; scoring

**What it does**: every answer automatically gets three cards:

- **Correction** — grammar / word choice / tense fixes;
- **Upgrade** — turns casual English into the polished phrasing interviewers expect;
- **Revision** — a full polished rewrite you can read back.

Plus a 1–10 overall score. In read-aloud mode you also get a **reading accuracy** score (word-level missed / extra words against the script).

**How to use**: it appears automatically after each answer; words inside the cards are clickable and savable too.

**How to configure**: none.

### Session review &amp; errorbook

**What it does**: end a session to generate a "Review": scores across content / structure / grammar / vocabulary / fluency, a next-focus suggestion and a drill list; mistakes that keep recurring are collected into an errorbook for focused re-practice.

**How to use**: top-right "Review" → the report takes 10–20 s to generate (also saved to `data/reports/`).

**How to configure**: none.

### Streaks &amp; progress

**What it does**: tracks your "speaking volume" like a fitness app: streak days, a daily goal ring (20 minutes by default), a 14-day minutes calendar and stat cards; hitting 3 / 7 / 14 / 30 / 50 / 100 consecutive days triggers a celebration.

**How to use**: the check-in panel on the home page updates automatically; every finished session counts toward today.

**How to configure**: change `app/config.yaml` → `session.daily_goal_minutes` (default 20).

### Favourites &amp; daily review

**What it does**: saved words live in a dictionary-style library — 8 entries a page with paging, a "Newest / A–Z" sort toggle and two-step delete. The "🔁 Daily review" tab draws a batch of words every day at a configurable ratio, prioritising words never reviewed, failed last time, or long unseen. Recall first, then reveal the meaning, then mark "😵 missed / 😎 got it"; missed words come back for a second pass in the same session and are scheduled first for tomorrow. Progress feeds the check-in panel's "Today's review x/y" line.

**How to use**: home → "⭐ Favourites" → "📚 Library" to browse / sort / delete / look up words; "🔁 Daily review" → Start → recall → reveal → mark.

**How to configure**: `app/config.yaml` → `review.ratio` (daily share of your saved words, default 0.3), `review.min_per_day` (default 5), `review.max_per_day` (default 30).

### Question card wall

**What it does**: each question set opens as a wall of illustrated cards (title, status, best score). Open a card for its **per-question history** — date, mode (free / read-aloud), duration, speaking rate (WPM), score — with a score trend line; you can restart practice from any question.

**How to use**: home → "Choose a question set" → card wall; the "▶ Continue" button jumps to your first unpractised question (it becomes "▶ Practise again" once the set is finished).

**How to configure**: drop a PNG at `materials/question-bank/images/<set>/<question-id>.png` and it shows up on the card wall (the bundled sets already include illustrations).

### Resume import

**What it does**: upload your resume (`.docx` / `.pdf` / paste text) to unlock the **🎯 personalized** sample answers, built from your real experience, projects and numbers. The resume is stored on your machine only.

**How to use**: top-right "📄 My resume" → choose a file or paste text → save; delete it any time (you simply fall back to generic versions).

**How to configure**: you can also edit `materials/profile.md` by hand (see `materials/profile.example.md` for the format).

## Configuration

### Environment variables (`app/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `API_KEY` | ✅ | One key for LLM + speech recognition + speech synthesis (bring your own) |
| `API_BASE_URL` | – | Override the API base URL (your OpenAI-compatible service) |

### App settings (`app/config.yaml`)

| Setting | Default | Notes |
|---|---|---|
| `llm.base_url` | empty | Your OpenAI-compatible base URL (or use `API_BASE_URL`) |
| `llm.model` | `deepseek/deepseek-flash` | Main chat model |
| `llm.fallback_models` | see file | Fallback chain if the main model fails |
| `asr.driver` | `auto` | `auto` / `cloud` (cloud ASR) / `local` (mlx-whisper, macOS only) |
| `asr.endpoint` / `tts.endpoint` | empty | Cloud speech endpoints; when empty, local mode is used |
| `tts.driver` | `cloud` | `cloud` / `macos_say` (offline fallback) |
| `tts.voices` | see file | One voice per persona |
| `review.ratio` | `0.3` | Daily review share (= saved words × this ratio) |
| `review.min_per_day` / `review.max_per_day` | `5` / `30` | Daily review floor / ceiling |
| `session.daily_goal_minutes` | `20` | Daily goal (minutes), drives the check-in ring |
| `session.max_answer_seconds` | `120` | Max length of one answer |
| `server.port` | `8765` | Server port |
| `tools.ffmpeg` | `ffmpeg` | Path to the ffmpeg binary |

### Runtime data (`data/`, local only)

| Path | Contents |
|---|---|
| `data/sessions/*.jsonl` | Per-round records of every session (with scores) |
| `data/reports/` | Review reports |
| `data/errorbook.jsonl` | Errorbook |
| `data/favorites.jsonl` | Saved words &amp; sentences |
| `data/reviews.jsonl` | Word review records (daily recall answers) |
| `data/review_decks.json` | Daily review plan cache (fixed per day) |
| `data/gloss_cache.json` | Click-to-lookup cache |
| `data/audio/` | Recordings |

## Customize &amp; extend

- **Questions / question sets** — plain YAML; edit or add files under `materials/question-bank/`:

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

- **Question illustrations** — drop a PNG at `materials/question-bank/images/<set>/<question-id>.png` and it appears on the card wall;
- **Interviewer personas** — `materials/personas/*.md` (the built-in three include positioning, evaluation focus and a realistic dialogue few-shot — edit them for your own role);
- **Story bank** — copy `materials/stories/template.md` to build 5–8 polished personal stories that make your answers concrete.

## Project structure

```text
english-interview-gym/
├── 打开训练系统.command          # one-click launcher (macOS double-click)
├── app/
│   ├── config.yaml              # app settings (models / speech / daily goal)
│   ├── .env.example             # env template (copy to .env and add your key)
│   ├── requirements.txt
│   ├── server/                  # FastAPI backend: sessions · LLM · ASR · TTS · reports
│   └── web/                     # single-page frontend (no build step)
├── materials/
│   ├── personas/                # 3 interviewer personas
│   ├── question-bank/           # 3 question sets (YAML) + illustrations + meta
│   ├── stories/                 # personal story bank (template + guide)
│   ├── wordlist/                # word list
│   └── profile.example.md       # resume template (copy to profile.md and edit)
├── scripts/                     # setup_env · run_server · check_stack · baseline_report
├── data/                        # runtime data (local only, gitignored)
└── docs/                        # RUNBOOK · PRACTICE-PLAN · image assets
```

## Privacy

- **100% local**: the server only listens on `127.0.0.1`; all training data (recordings, transcripts, reports, vocabulary) lives in `data/` on your machine and is never uploaded to any third party;
- **Minimal outbound calls**: audio and text of your answers are sent only to the API endpoint **you** configured (for transcription and feedback); your key stays in `app/.env` on your machine;
- **No telemetry**: no analytics, no accounts;
- **Zero personal data in the public repo**: `app/.env`, `materials/profile.md` and `data/` are gitignored and never shipped.

## Content sources & disclaimer

- **Sources**: the question banks (`materials/question-bank/`) are compiled from **public internet sources** (community interview write-ups, public question round-ups, public job postings and requirements). Wording was generalized during compilation; the per-question analysis and hints are written by this project;
- **No claims**: this project claims no rights over the original sources and does not guarantee any correspondence to the actual question banks of any specific company;
- **Usage**: the question text is for **personal study** only — please don't use it commercially. The code is open-sourced under MIT;
- **Takedown**: if you believe any content in this repository (questions, illustrations, etc.) infringes your rights, please contact us via [Issues](../../issues) — we will verify and **take the relevant content down promptly**.

## FAQ

| Symptom | Fix |
|---|---|
| `402 / 401007` on submit | Your provider hasn't enabled the speech models (usually a "postpaid billing" toggle); or set `asr.driver: local` |
| Microphone unavailable | Open via `http://127.0.0.1` (not a LAN IP); allow microphone permission in the browser |
| Port in use | Change `server.port` in `app/config.yaml` and the `--port` flag in `scripts/run_server.sh` |
| Different voices / LLM | Voices: `tts.voices` · Model: `API_BASE_URL` + `llm.model` for any OpenAI-compatible service |
| Want it (mostly) free / fully local | Local speech: `asr.driver: local` + `tts.driver: macos_say` (macOS only, free); the chat model still needs an OpenAI-compatible service (cloud or a local inference server) |

## License

MIT — see [LICENSE](LICENSE). Content sources and usage terms: see [Content sources & disclaimer](#content-sources--disclaimer).
