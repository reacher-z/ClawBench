# ClawBench

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

[English](README.md) | **中文**

> **TL;DR：** ClawBench 直接跑在**你的本机**上。只要执行 `./run.sh` 并跟着首次启动向导走 — 它会自动构建 Docker/Podman 镜像，并为每个测试用例自动启动一个容器。你**不需要**自己进容器里跑任何东西。

ClawBench 是一个用于在真实浏览器环境中评测 Web 智能体的基准测试框架。它会记录用户/智能体的交互、HTTP 请求、动作截图，以及每次会话的完整 MP4 录像。

每个测试用例都运行在一个隔离的容器（Docker 或 Podman）中,容器内包含 Chrome 浏览器、自定义的录制扩展以及一个 AI 智能体。框架会捕获智能体的所有操作,并通过请求拦截器来检测任务完成。

## 目录

- [快速开始](#快速开始)
- [它是怎么工作的](#它是怎么工作的30-秒速览)
- [什么是 model name](#什么是-model-name)
- [完整示例](#完整示例)
- [手动配置](#手动配置)
- [依赖](#依赖)
- [架构](#架构)
- [数据输出](#数据输出)
- [构建容器](#构建容器)
- [API 端点](#api-端点)
- [OpenClaw 智能体集成](#openclaw-智能体集成)
- [合成用户档案](#合成用户档案)
- [工具限制](#工具限制)
- [请求拦截器](#请求拦截器)
- [测试驱动器](#测试驱动器)
- [人工模式](#人工模式)
- [许可证](#许可证)
- [致谢](#致谢)

## 快速开始

```bash
git clone https://github.com/reacher-z/ClawBench.git
cd ClawBench
./run.sh   # 剩下的事情交给首次启动向导
```

向导会从模板创建 `.env`、提示你输入 PurelyMail 的 API key 和域名（用于为每个测试用例生成一次性邮箱），并带你添加第一个模型。完成后会进入主菜单 — 选 **"1. Single run"**、挑一个模型、挑一个测试用例。ClawBench 会自动构建容器镜像（仅首次）并启动容器；结果输出到 `test-output/`。

想自己手动配置而不用向导？看 [手动配置](#手动配置)。

## 它是怎么工作的（30 秒速览）

| 层级 | 做什么 | 跑在哪里 |
|---|---|---|
| `./run.sh` | 一行 bash，exec 启动 TUI | **你的本机** |
| `test-driver/tui.py` | 交互式菜单（纯 Python `input()`） | **你的本机** |
| `test-driver/run.py` | 构建镜像，每个用例启动**一个**容器 | **你的本机** |
| `test-driver/batch.py` | 用 `asyncio.Semaphore` **并行启动 N 个容器**（可配置） | **你的本机** |
| 容器（Chromium + 扩展 + 智能体） | 真正跑测试用例的地方 | **Docker/Podman 内部** |

所以：

- **Single run** = 1 个容器。
- **Batch run** = 多个容器并行运行。默认并发数根据你的 CPU/内存推算；可在 TUI 中或通过 `--max-concurrent` 调整。
- 容器引擎会自动检测（Docker 或 Podman）。设置 `CONTAINER_ENGINE=docker` 或 `CONTAINER_ENGINE=podman` 可强制指定。

## 什么是 "model name"？

`MODEL_NAME` **就是你在 `models/models.yaml` 里自己取的 YAML key**。它**不需要**对应真实的模型版本号 — 它只是一个标签，会解析成完整的提供商配置（`base_url`、`api_type`、`api_key`、`thinking_level`）：

```yaml
# models/models.yaml
my-claude:                            # ← 这就是 TUI 里显示的 MODEL_NAME
  api_key: "sk-ant-..."
  base_url: https://api.anthropic.com
  api_type: anthropic-messages
  thinking_level: medium

gpt5-via-openrouter:                  # ← 另一个 MODEL_NAME
  api_key: "sk-or-v1-..."
  base_url: https://openrouter.ai/api/v1
  api_type: openai-completions
```

`api_type` 可以是 `openai-completions`、`openai-responses`、`anthropic-messages` 或 `google-generative-ai` 之一。可以加任意多个条目 — TUI 的模型选择列表里会列出所有条目。从命令行直接调用：

```bash
uv run --project test-driver test-driver/run.py \
  test-cases/886-entertainment-hobbies-experience-topgolf my-claude
```

## 完整示例

向导跑完之后，再次执行 `./run.sh`，选 **"1. Single run"**，挑你的模型，然后在用例提示符下输入 `886`（数字 ID 可以直接用，因为测试用例目录都是 ID 前缀）。ClawBench 会：

1. 构建 `clawbench` Docker/Podman 镜像（仅首次）
2. 通过 PurelyMail 创建一个像 `cba1b2c3d4e5f6@<your-domain>` 这样的一次性邮箱
3. 启动一个容器，挂载评测 schema 和合成用户档案，启动智能体
4. 等待请求拦截器命中（或时间限制到期）
5. 把 `/data` 从容器里复制出来，写入：

```
test-output/my-claude/886-entertainment-hobbies-experience-topgolf-my-claude-<时间戳>/
  data/
    actions.jsonl          # 所有浏览器动作
    requests.jsonl         # 所有 HTTP 请求
    agent-messages.jsonl   # 智能体完整对话记录（思考 + 工具调用）
    screenshots/           # 每个动作一张 PNG
    recording.mp4          # 整个会话视频
    interception.json      # 触发停止的请求，或停止原因
  run-meta.json            # 模型、时长、intercepted=true/false
  eval-schema.json         # 本次运行使用的 schema
```

如果要批量评测所有模型 × 用例 1-50，在 TUI 里选 **"2. Batch run"**，或者直接命令行：

```bash
uv run --project test-driver test-driver/batch.py --all-models --case-range 1-50 --max-concurrent 3
```

## 手动配置

如果你想跳过向导，全部手动配置：

```bash
# 1. PurelyMail 凭证
cp .env.example .env
# 编辑 .env → 填入 PURELY_MAIL_API_KEY 和 PURELY_MAIL_DOMAIN

# 2. 至少配置一个模型
cp models/models.example.yaml models/models.yaml
# 编辑 models/models.yaml → 填入 api_key

# 3. 启动
./run.sh
```

`./run.sh` 检测到 `.env` 和 `models/models.yaml` 已存在时会跳过向导，直接进入主菜单。

## 依赖

- [Python](https://www.python.org/) 3.11+
- [uv](https://docs.astral.sh/uv/)（Python 包管理器 — 自动安装所有 Python 依赖）
- [Docker](https://www.docker.com/) 或 [Podman](https://podman.io/)（容器运行时）

Python 依赖（`fpdf2`、`huggingface_hub`、`pyyaml`）由 `uv` 管理,首次运行时会自动安装。

## 架构

```
┌─────────────────────────────────────────────────┐
│  容器（Docker / Podman）                         │
│                                                 │
│  ┌───────────┐   DOM 事件    ┌──────────────┐   │
│  │ content.js├──────────────►│ background.js│   │
│  │ (每个标签)│               │  (service    │   │
│  └───────────┘               │   worker)    │   │
│                              └──┬──────┬────┘   │
│                                 │      │        │
│                            动作 │      │ 截图   │
│                                 │      │        │
│  ┌──────────┐            ┌──────▼──────▼────┐   │
│  │  Xvfb    │◄──ffmpeg──►│  FastAPI Server  │   │
│  │ :99      │  x11grab   │  :7878           │   │
│  └──────────┘            └──────────────────┘   │
│                                  │              │
│  ┌──────────┐            ┌───────▼─────────┐    │
│  │ Chromium │            │     /data       │    │
│  │ :9222 CDP│            │  actions.jsonl  │    │
│  └──────────┘            │  requests.jsonl │    │
│                          │  screenshots/   │    │
│                          │  recording.mp4  │    │
│                          └─────────────────┘    │
└─────────────────────────────────────────────────┘
```

## 数据输出

所有数据都存储在容器内的 `/data` 目录下：

```
/data/
  actions.jsonl          # 每行一个 JSON 对象，记录所有 DOM 事件
  requests.jsonl         # 每行一个 JSON 对象，记录所有 HTTP 请求
  agent-messages.jsonl   # OpenClaw 对话记录（思考、文本、工具调用）
  screenshots/           # 带时间戳的 PNG 文件，每个动作一张
    1710000001234.png
    1710000002345.png
  recording.mp4          # 整个会话的视频（H.264, 15fps）
  interception.json      # 拦截器拦截到的请求详情（如适用）
```

### 动作格式（JSONL）

每行都是一个 JSON 对象：

```json
{"type": "click", "timestamp": 1710000001234, "url": "https://example.com/", "target": {"tagName": "A", "id": "", "className": "btn", "textContent": "Submit", "xpath": "/html[1]/body[1]/div[1]/a[1]"}, "x": 255, "y": 245}
{"type": "keydown", "timestamp": 1710000002345, "url": "https://example.com/", "target": {...}, "key": "Enter"}
{"type": "input", "timestamp": 1710000003456, "url": "https://example.com/", "target": {...}, "value": "search query"}
{"type": "pageLoad", "timestamp": 1710000004567, "url": "https://example.com/results", "title": "Results"}
```

捕获的事件类型：`pageLoad`、`click`、`keydown`、`keyup`、`input`、`scroll`、`change`、`submit`。

### 智能体消息格式（JSONL）

`agent-messages.jsonl` 包含完整的 OpenClaw 对话记录。每行都是一个 JSON 对象：

- **`type: "session"`** — 会话元数据（版本、id、时间戳）
- **`type: "message"`** — 对话轮次,带有 `message.role` 和 `message.content[]`：

| `message.role` | 内容类型                          | 描述                              |
| -------------- | --------------------------------- | --------------------------------- |
| `user`         | `text`                            | 指令提示                          |
| `assistant`    | `text`、`thinking`、`toolCall`    | 模型回复、推理、动作              |
| `toolResult`   | `text`                            | 工具执行结果                      |

### HTTP 请求格式（JSONL）

`requests.jsonl` 记录会话期间浏览器发出的所有 HTTP 请求（不包括内部扩展/服务器流量）。每行：

```json
{"timestamp": 1710000001.234, "url": "https://example.com/api?q=test", "method": "POST", "headers": {"Content-Type": "application/json"}, "body": {"action": "send"}, "query_params": {"q": "test"}, "resource_type": "XHR"}
```

| 字段            | 描述                                                               |
| --------------- | ------------------------------------------------------------------ |
| `timestamp`     | Unix 时间戳（浮点数）                                              |
| `url`           | 完整请求 URL                                                       |
| `method`        | HTTP 方法（GET、POST 等）                                          |
| `headers`       | 请求头（对象）                                                     |
| `body`          | 解析后的请求体（JSON 对象、表单字典、原始字符串或 null）          |
| `query_params`  | 解析后的 URL 查询参数（对象）                                     |
| `resource_type` | 资源类型：Document、Script、Stylesheet、XHR、Fetch、Image、Font 等 |

到 `localhost:7878`（扩展服务器）和 `chrome-extension://` URL 的请求会被过滤掉。

## 构建容器

### 容器引擎

框架同时支持 Docker 和 Podman（无需 root 权限即可运行）。设置 `CONTAINER_ENGINE` 环境变量来强制指定其中一个：

```bash
export CONTAINER_ENGINE=podman  # 或 docker
```

如果未设置,会自动检测系统上可用的引擎。

### 构建

```bash
# 使用 docker：
docker build -t clawbench .

# 使用 podman（无需 sudo）：
podman build -t clawbench .
```

### 端口

| 端口 | 服务            | 用途                                          |
| ---- | --------------- | --------------------------------------------- |
| 7878 | FastAPI server  | 动作/截图 API,会话控制                        |
| 9223 | CDP（通过 socat）| Playwright/DevTools 连接到 Chromium           |

## API 端点

| 方法   | 路径                  | 描述                                          |
| ------ | --------------------- | --------------------------------------------- |
| GET    | `/api/status`         | 健康检查                                      |
| POST   | `/api/action`         | 记录浏览器动作（JSON body）                   |
| POST   | `/api/screenshot`     | 存储截图（JSON 中的 base64 PNG）              |
| POST   | `/api/stop`           | 通知会话停止,完成收尾工作                     |
| POST   | `/api/stop-recording` | 停止 ffmpeg 录制,生成最终 MP4                 |


## OpenClaw 智能体集成

容器使用 [OpenClaw](https://github.com/openclaw/openclaw) 作为智能体驱动器,通过 CDP 在容器内的 Chromium 浏览器上执行操作。所有智能体动作都会被现有的扩展和服务器基础设施透明地记录下来。

### 环境变量

| 变量                              | 示例                                                   | 描述                                                  |
| --------------------------------- | ------------------------------------------------------ | ----------------------------------------------------- |
| `MODEL_NAME`                      | `claude-sonnet-4-6`、`gemini-3-flash-preview`          | 模型标识                                              |
| `BASE_URL`                        | `https://api.openai.com/v1`                            | API 基础 URL                                          |
| `API_TYPE`                        | `openai-completions`                                   | API 类型（`openai-completions`、`anthropic-messages` 等）|
| `API_KEY`                         | `sk-ant-...`、`AIza...`                                | API 密钥                                              |
| `INSTRUCTION`                     | `"Go to example.com and…"`                             | 给智能体的任务提示                                    |
| `TIME_LIMIT_S`                    | `300`                                                  | 看门狗超时秒数（默认：600）                           |
| `THINKING_LEVEL`                  | `high`、`low`、`off`                                   | 推理深度（默认：`medium`）                            |
| `TEMPERATURE`                     | `0.5`                                                  | 采样温度（可选）                                      |
| `MAX_TOKENS`                      | `4096`                                                 | 最大输出 token 数（可选）                             |

### OpenClaw 容器生命周期

入口脚本（`entrypoint.sh`）按以下顺序编排执行：

1. **Xvfb** — 虚拟显示在 `:99`（1920x1080）
2. **FastAPI 服务器** — 数据收集 API 在 7878 端口,启动 ffmpeg 录屏
3. **Chromium** — 加载 Chrome 扩展,CDP 在 9222 端口
4. **socat** — 将 9223 端口（外部）转发到 9222（内部 CDP）
5. **setup-openclaw.sh** — 根据环境变量生成 `~/.openclaw/openclaw.json` 和认证凭证
6. **CDP 健康检查** — 轮询 `http://127.0.0.1:9222/json/version` 直到 Chrome 就绪
7. **OpenClaw gateway** — 本地模式,管理智能体执行和浏览器工具
8. **OpenClaw 智能体** — 运行 `openclaw agent --session-id clawbench --message "$INSTRUCTION" --local`
9. **看门狗** — 监控 `/data/actions.jsonl`；当评测拦截器命中（通过 `/data/.stop-requested`）、连续 900 秒没有新动作、或达到 `TIME_LIMIT_S` 时停止
10. **清理** — 杀掉 OpenClaw 进程,调用 `POST /api/stop` 完成收尾,等待 15 秒宽限期让录制捕获最终结果,调用 `POST /api/stop-recording` 生成最终 MP4,然后退出

### OpenClaw 配置

`setup-openclaw.sh` 在运行时生成两个文件：

- **`~/.openclaw/openclaw.json`** — gateway 配置（本地模式）、模型提供商设置、以及指向 `http://127.0.0.1:9222`（容器内 Chrome CDP 端点）的浏览器配置
- **`~/.openclaw/agents/main/agent/auth-profiles.json`** — 已配置提供商的 API 密钥凭证

提供商的 `baseUrl` 和 `api` 类型直接通过 `BASE_URL` 和 `API_TYPE` 环境变量从 `models.yaml` 中的模型配置传入。

### OpenClaw 浏览器补丁

OpenClaw 内置的浏览器工具使用 [chrome-devtools-mcp](https://github.com/anthropics/anthropic-quickstarts/tree/main/chrome-devtools-mcp) 来控制浏览器。但截至 `v2026.3.13` 版本,`existing-session` 驱动在启动 chrome-devtools-mcp 时硬编码了 `--autoConnect`,该选项只能通过默认用户数据目录中的 `DevToolsActivePort` 文件来发现 Chrome。它会忽略浏览器配置中设置的 `cdpUrl`,也不会向 chrome-devtools-mcp 传递 `--browserUrl`。这意味着浏览器工具无法连接到我们运行在 9222 端口的 Chromium 实例。详见 [openclaw/openclaw#47879](https://github.com/openclaw/openclaw/issues/47879)。

**Dockerfile 中应用的临时方案：**

- OpenClaw 固定到 `v2026.3.13`
- 一个 `sed` 补丁将所有打包的 dist 文件中的 `"--autoConnect"` 替换为 `"--browserUrl","http://127.0.0.1:9222"`
- Chromium 启动时带 `--remote-allow-origins=*`（Chrome 132+ 上 chrome-devtools-mcp 内部 WebSocket 连接所必需）

一旦 [#47879](https://github.com/openclaw/openclaw/issues/47879) 在上游被修复,版本固定和补丁就可以移除。

## 合成用户档案

每个容器都有一个 `/my-info/` 目录（只读）,里面包含一个虚拟用户的身份和凭证：

```
/my-info/
  alex_green_personal_info.json   # 完整档案（联系方式、地址、教育、工作等）
  email_credentials.json          # 自动生成的 email + 密码 + 登录 URL
  alex_green_resume.pdf           # 简历 PDF,header 中带动态 email
```

个人信息 JSON 和简历 PDF 中的 `email` 字段都会在每次运行时更新,以匹配为该会话创建的一次性邮箱。智能体被指示在需要个人信息进行表单填写、注册等操作时读取这些文件。

源模板位于 `shared/`（个人信息）和 `test-driver/resume_template.json`（简历）。PDF 在运行时由 `test-driver/generate_resume_pdf.py` 生成。

## 工具限制

`exec` 工具在生成的 OpenClaw 配置中被设置为 `allowlist` 安全模式。只有安全的、只读的命令被允许（`ls`、`cat`、`find`、`file`、`grep`、`sort`、`head`、`tail`、`jq`、`cut`、`uniq`、`tr`、`wc`）。可能绕过浏览器的命令（例如 `curl`、`python`、`node`、`wget`、`smtplib`）会被阻止。智能体使用 `cat` 来读取 `/my-info/` 中的文件（核心文件已在指令提示中列出,但 `ls` 仍可用于发现额外信息）。

智能体的指令提示也明确要求只通过浏览器完成任务。

## 请求拦截器

拦截器会阻止关键的、不可逆的 HTTP 请求（结账、表单提交、发布评论等）,以防止智能体在评测期间造成真实世界的副作用。它**不**验证任务完成 — 评测由独立的评估器在会话结束后处理。

### 工作原理

1. 在容器中挂载一个 JSON 配置到 `/eval-schema.json`
2. 服务器通过 CDP（`Fetch` 域）连接到 Chrome 并拦截所有请求
3. 当一个请求匹配 `url_pattern`（正则）、`method` 和可选的 `body`/`params` 过滤条件时,该请求会被阻止
4. 被阻止请求的详情会保存到 `interception.json`,智能体被杀掉,录制停止

### Schema 格式

评测 schema 有两个必填字段（`url_pattern`、`method`）和两个可选字段（`body`、`params`）用于消歧。

```json
{
  "url_pattern": "inbox\\.purelymail\\.com",
  "method": "POST",
  "body": { "_action": "send" }
}
```

可选的 `body` 和 `params` 是扁平的键值映射 — 每个键必须在请求数据中精确匹配。当同一个 URL + 方法服务于多个动作时（例如同一端点上的登录 vs 发送,或不同的 GraphQL 操作）使用它们。

对于在支付墙后或其他天然阻塞的任务（智能体没有有效的信用卡）,使用永不匹配的占位模式：

```json
{
  "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
  "method": "POST"
}
```

### 何时应该拦截

拦截器只在没有支付墙的情况下,对于会有**不可逆真实世界后果**的动作才需要：

| 拦截    | 示例                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **是**  | 公开评论、发布信息、求职申请、联系表单、邮件发送、预约、网站创建                                                                  |
| **否**  | 购买、订阅、捐赠（支付墙）、加入购物车（可逆）、搜索（可逆）、账户创建（无害）                                                    |


### 拦截输出

`/data/interception.json`：

```json
{
  "intercepted": true,
  "request": {
    "url": "https://inbox.purelymail.com/action",
    "method": "POST",
    "params": {},
    "body": {"_action": "send", "_to": "user@example.com"}
  }
}
```

## 测试驱动器

测试驱动器（`test-driver/run.py`）端到端地自动化运行测试用例：通过 PurelyMail 创建一次性邮箱、启动容器、强制时间限制、收集结果并清理。测试用例定义在 `test-cases/` 中,使用 `test-cases/task.schema.json` 验证 `task.json`。

```bash
# 交互式菜单（配置模型、选择用例、选择运行模式）：
./run.sh

# 或直接运行：
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf qwen3.5-397b-a17b

# 人工模式（无智能体 — 你通过 noVNC 控制浏览器）：
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf --human

# 批量：所有模型 x 用例 1-50,3 个并发
uv run test-driver/batch.py --all-models --case-range 1-50 --max-concurrent 3

```

完整文档参见 [test-driver/README.md](test-driver/README.md)。

## 人工模式

人工模式让你可以在浏览器中手动执行测试用例,而不是使用 AI 智能体。这对于收集人工基线、调试测试用例或验证任务是否可完成很有用。

容器运行同样的基础设施（Xvfb、Chromium、扩展、FastAPI 服务器、ffmpeg 录制）,但不会启动 OpenClaw 智能体,而是通过 [noVNC](https://novnc.com/) — 一个基于浏览器的 VNC 客户端 — 暴露浏览器。

### 用法

```bash
# 通过交互式菜单（选择 "Human mode"）：
./run.sh

# 或直接运行：
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf --human
```

容器启动后,打开终端中打印的 noVNC URL：

```
noVNC ready: http://localhost:6080/vnc.html
```

你会在浏览器中看到 Chromium 浏览器。手动完成任务 — 你的所有动作、截图和 HTTP 请求都会像在智能体模式下一样被记录。

### 会话如何结束

当以下任何一种情况发生时,会话会停止：

- **评测拦截器命中** — 检测到目标 HTTP 请求（任务已完成）
- **VNC 断开** — 你关闭了 noVNC 标签页（15 秒重连宽限期）
- **达到时间限制** — 配置的时间限制已到

会话结束后,结果会以与智能体运行相同的格式收集（动作、截图、录制、拦截）。

## 许可证

本项目采用 Apache License 2.0 许可证 — 详见 [LICENSE](LICENSE) 文件。

## 致谢

ClawBench 使用以下开源项目：

- [noVNC](https://github.com/novnc/noVNC)（MPL 2.0）— 用于人工模式的基于浏览器的 VNC 客户端
- [websockify](https://github.com/novnc/websockify)（LGPL 3.0）— VNC 的 WebSocket-to-TCP 代理
- [OpenClaw](https://github.com/openclaw/openclaw) — 用于浏览器自动化的 AI 智能体驱动器
