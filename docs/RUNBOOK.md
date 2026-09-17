# 运行手册（RUNBOOK）

## 日常使用
0. **最省事（macOS）**：双击项目根目录的 `打开训练系统.command` → 自动启动服务 + 打开浏览器。保持弹出的终端窗口开着；关掉窗口 = 停止服务。
1. 命令行方式：`bash scripts/run_server.sh`，看到 `Uvicorn running on http://127.0.0.1:8765` 即成功。
2. 浏览器打开 http://127.0.0.1:8765 （Chrome 首次会请求麦克风权限，允许）。
3. 流程：选人格 → 点题集进入**题目卡片墙** → 选任意一题开练（或点「继续练习」）→ 「开始录音」（空格键也行）→ 说话 → 「停止」→「提交，看反馈」→ 读反馈 → 下一题 / 回答追问。
4. 结束：点「结束并复盘」→ 看整场复盘；报告文件在 `data/reports/<会话ID>.md`。
5. 每周：`.venv/bin/python scripts/baseline_report.py` 生成训练总览 `data/reports/OVERVIEW.md`。

## 体检
- 三条链路一键测：`.venv/bin/python scripts/check_stack.py`
- 键变更后重新生成：`python3 scripts/setup_env.py`

## 常见问题
| 症状 | 处理 |
|---|---|
| 提交后报 402 / 401007 | TokenHub 语音模型需在控制台开启"后付费"；或把 config.yaml 里 asr.driver 设为 local |
| ASR 提示 mlx-whisper 未安装 | `uv pip install --python .venv/bin/python mlx-whisper`（首次使用会下载模型） |
| 麦克风不可用 | 确认用 http://127.0.0.1 打开；检查 系统设置→隐私与安全性→麦克风 |
| 端口被占 | 改 `app/config.yaml` 的 server.port，并同步 run_server.sh 的 --port |
| 想换考官音色 | `say -v '?'` 查看音色列表，改 config.yaml 的 tts.say_voice |
| 想切 TokenHub 语音 | config.yaml：tts.driver 改 tokenhub；（ASR 已默认优先 tokenhub） |
| 反馈把疑似 ASR 转写噪声当成语言错误 | 以录音为准；提示词已内含防噪指令；开启 TokenHub 转写（Hy-ASR）后质量更高 |
| 手机端使用（后期） | 用 `tailscale serve` 提供 HTTPS 域名后浏览器访问；http 内网 IP 无法调用麦克风 |

## 数据与备份
- 全部数据在 `data/`：`sessions/`（会话 JSONL）、`reports/`、`errorbook.jsonl`（错题本）、`audio/`（录音原件）。
- 备份：直接拷贝 `data/` 目录即可；全部为本地文件。
