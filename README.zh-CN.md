<div align="center">

# ClawBench

[![arXiv](https://img.shields.io/badge/arXiv-2604.08523-b31b1b.svg?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2604.08523)
[![Project Page](https://img.shields.io/badge/Project-Page-8A2BE2.svg?logo=githubpages&logoColor=white)](https://claw-bench.com)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-D22128.svg?logo=apache&logoColor=white)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-supported-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![GitHub stars](https://img.shields.io/github/stars/reacher-z/ClawBench?style=social)](https://github.com/reacher-z/ClawBench)

### AI 智能体能完成日常在线任务吗?

我们让 6 个前沿 AI 智能体去做人们每天都在做的事 --<br/>
点外卖、订酒店、投简历、写评价、管理项目。<br/>
**最强的模型也只完成了 33.3% 的任务。**

[论文](https://arxiv.org/abs/2604.08523) &nbsp;&bull;&nbsp; [项目主页](https://claw-bench.com) &nbsp;&bull;&nbsp; [排行榜](#-实验结果)

---

**153** 个日常任务 &nbsp;&middot;&nbsp; **144** 个真实网站 &nbsp;&middot;&nbsp; **15** 个生活类别

<a href="README.md"><img src="static/icons/language.svg" width="16" height="16"> English</a>

</div>

<br/>

<table>
<tr>
<td align="center" width="25%">
<img src="static/icons/globe.svg" width="36" height="36"><br/>
<b>真实网站</b>
</td>
<td align="center" width="25%">
<img src="static/icons/cube.svg" width="36" height="36"><br/>
<b>隔离容器</b>
</td>
<td align="center" width="25%">
<img src="static/icons/shield-halved.svg" width="36" height="36"><br/>
<b>请求拦截器</b>
</td>
<td align="center" width="25%">
<img src="static/icons/layer-group.svg" width="36" height="36"><br/>
<b>五层录制</b>
</td>
</tr>
</table>

<br/>

## 工作流程

```
   你选择一个任务             ClawBench 启动一个          智能体驱动浏览器:          拦截器捕获最终操作
   来自 153 个真实             隔离的 Docker 容器          导航、填表、点击            并记录所有数据
   日常场景                    + Chromium                                           
                                                                                    
   ┌──────────────┐           ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
   │ "在 Rover 上 │    ──►    │    容器      │    ──►    │   AI 智能体  │    ──►    │   已拦截     │
   │  预订宠物     │           │  + Chromium  │           │  浏览真实    │           │   五层数据   │
   │  寄养"       │           │  + 智能体    │           │   网站       │           │   已录制     │
   └──────────────┘           └──────────────┘           └──────────────┘           └──────────────┘
```

<br/>

# <img src="static/icons/robot.svg" width="28" height="28"> LLM 快速开始

1. 将你的编程智能体 (Claude Code, Cursor, Copilot 等) 指向 [`AGENTS.md`](AGENTS.md)
2. 直接提问!

<br/>

# <img src="static/icons/person.svg" width="28" height="28"> 手动快速开始

**前置条件:** [Python 3.11+](https://python.org), [uv](https://docs.astral.sh/uv/), [Docker](https://www.docker.com/) 或 [Podman](https://podman.io/)

**1. 克隆并配置:**
```bash
git clone https://github.com/reacher-z/ClawBench.git && cd ClawBench
cp .env.example .env          # 编辑: 填入 PURELY_MAIL_API_KEY + PURELY_MAIL_DOMAIN
cp models/models.example.yaml models/models.yaml   # 编辑: 填入你的模型 API 密钥
```

**2. 跑你的第一个任务** (三选一):

**(a) 交互式 TUI** —— 最简单,帮你挑模型 + 测试用例:
```bash
./run.sh
```

**(b) 指定模型跑单个任务:**
```bash
uv run --project test-driver test-driver/run.py \
  test-cases/001-daily-life-food-uber-eats claude-sonnet-4-6
```
结果落在 `test-output/<model>/<timestamp>-001-.../`,包含完整的五层录制。

**(c) 通过 noVNC 手动控制浏览器** —— 产出人工参考轨迹:
```bash
uv run --project test-driver test-driver/run.py \
  test-cases/001-daily-life-food-uber-eats --human
```
打开脚本打印的 noVNC URL,在浏览器里亲手完成任务,完事后关掉标签页。

<br/>

# <img src="static/icons/chart-bar.svg" width="28" height="28"> ClawBench-Lite

**第一次跑？先跑这个。** [`test-cases/lite.json`](test-cases/lite.json) 是完整 153 任务的 **20 个精选子集**，按站点知名度、真实日常相关度、难度和类别多样性挑选。它对齐了 [browser-use/benchmark](https://github.com/browser-use/benchmark) 的 20-tasks-per-source 规范，用完整 benchmark 一小部分的成本就能拿到可信的信号。

分层: **flagship 9 / core 8 / wildcard 3** —— 覆盖日常生活 (OpenTable, DoorDash, Instacart, TaskRabbit)、娱乐爱好 (Eventbrite, Goodreads, Fandango)、创建初始化 (Asana, Mailchimp, Squarespace)、旅行 (Airbnb)、教育 (LeetCode)、开发技术 (GitHub)、学术研究 (Overleaf)、个人管理 (1Password) 等类别。所有 Lite 任务均由 [`eval/agentic_eval.md`](eval/agentic_eval.md) 判定，不依赖 `url_pattern` 形态。

完整 manifest 格式见 [`test-cases/lite.schema.json`](test-cases/lite.schema.json)；4 轴选择 rubric 与完整 swap history 见 `lite.json` 的 `notes` 字段。

<br/>

# <img src="static/icons/video.svg" width="28" height="28"> 教程

<div align="center">

<!-- TODO: 替换为实际视频链接 -->

[![在 YouTube 观看](https://img.shields.io/badge/观看教程-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com)
&nbsp;&nbsp;
[![在 Bilibili 观看](https://img.shields.io/badge/观看教程-Bilibili-00A1D6?style=for-the-badge&logo=bilibili&logoColor=white)](https://bilibili.com)

</div>

<br/>

# <img src="static/icons/play.svg" width="28" height="28"> 演示

<!-- TODO: 替换为实际的演示 GIF/录屏 -->

<table>
<tr>
<td width="50%" align="center">

**在 Uber Eats 上点餐**

https://github.com/user-attachments/assets/placeholder-uber-eats

</td>
<td width="50%" align="center">

**提交求职申请**

https://github.com/user-attachments/assets/placeholder-greenhouse

</td>
</tr>
</table>

> 每次 ClawBench 运行都会产生完整的 MP4 录屏。访问[项目主页](https://claw-bench.com)查看全部 153 个任务的录屏。

<br/>

# <img src="static/icons/circle-question.svg" width="28" height="28"> 任务走读示例

好奇一个任务从头到尾到底长什么样? 下面是 **001 号任务** 的完整走读。

**任务定义** —— 来自 [`test-cases/001-daily-life-food-uber-eats/task.json`](test-cases/001-daily-life-food-uber-eats/task.json):

```json
{
  "instruction": "On Uber Eats, order delivery: one Pad Thai, deliver to home address, note \"no peanuts\"",
  "time_limit": 30,
  "eval_schema": {
    "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
    "method": "POST"
  }
}
```

智能体拿到的就是这段原文 `instruction`,另外有只读权限访问 `/my-info/alex_green_personal_info.json` (dummy user 的姓名、住址、电话、生日) 和一个一次性邮箱账号 (万一遇到强制登录)。它有 **30 分钟** 去触发一个 `POST` 请求,超时容器会被 kill。

**智能体要做什么** (顺利路径下):

1. 打开 `ubereats.com`
2. 从 `/my-info/alex_green_personal_info.json` 读出 dummy user 的家庭住址,填入配送地址输入框
3. 在菜品搜索框里搜 **"Pad Thai"**
4. 挑一家能配送到这个地址且有 Pad Thai 的餐厅
5. 进入菜品详情页,在定制或特殊说明字段里填 **"no peanuts"**
6. 加一份到购物车,打开购物车,必要时用一次性邮箱凭据处理登录弹窗
7. 进入 checkout,点 **Place Order**

**拦截器抓到了什么** —— 最后的 *Place Order* 那一点会发起一个 `POST` 请求。ClawBench 的 request interceptor 架在浏览器和目标站之间,**会在请求到达 Uber Eats 服务器之前抓下来**,所以 dummy user 永远不会被真的扣款。拦截发生的那一瞬间,五层录制 (MP4 视频、PNG 截图、HTTP 流量、浏览器动作、智能体消息) 会被一起冻结到 `/data/`。

**裁判怎么判 PASS / FAIL** —— 001 号任务的 `url_pattern` 是特意留的 sentinel `__PLACEHOLDER_WILL_NOT_MATCH__`,这意味着**没有任何请求路径能机械匹配**。判决完全由 [`eval/agentic_eval.md`](eval/agentic_eval.md) 里的 agentic judge 给出 —— 它把智能体的五层录制和人工参考轨迹对照,检查四件事:

- 智能体有没有真正走到最后的 checkout?
- 购物车里是不是**正好一份** Pad Thai (不是两份、也不是套餐)?
- 配送地址是不是 `alex_green_personal_info.json` 里的家庭住址?
- 订单的特殊说明字段里有没有 **"no peanuts"**?

四条全满足才算 **PASS**,任何一条没达到就是 **FAIL**,而且失败证据会被绑定到对应的判据上。正是这种 per-task rubric 让 ClawBench 对裁判敏感而不是对 URL 正则敏感 —— 完整 rubric 格式见 [`eval/README.md`](eval/README.md),judge prompt 见 [`eval/agentic_eval.md`](eval/agentic_eval.md)。

<br/>

# <img src="static/icons/chart-bar.svg" width="28" height="28"> 实验结果

<div align="center">

**6 个前沿 AI 智能体在 ClawBench 上的成功率 (%)**

</div>

| 排名 | 模型 | 总体 | 日常 | 金融 | 工作 | 开发 | 学术 | 旅行 | 社交 | 宠物 |
|:----:|-------|:------:|:-----:|:-----:|:----:|:---:|:----:|:----:|:----:|:----:|
| 1 | **Claude Sonnet 4.6** | **33.3** | 44.2 | **50.0** | 19.0 | 11.1 | **50.0** | 23.1 | **38.9** | **18.2** |
| 2 | GLM-5 | 24.2 | **30.8** | 16.7 | **38.1** | 16.7 | 28.6 | 0.0 | 16.7 | **18.2** |
| 3 | Gemini 3 Flash | 19.0 | 15.4 | 33.3 | 23.8 | **22.2** | 28.6 | **30.8** | 11.1 | 0.0 |
| 4 | Claude Haiku 4.5 | 18.3 | 15.4 | 22.2 | 19.0 | **27.8** | 21.4 | 7.7 | 16.7 | **18.2** |
| 5 | GPT-5.4 | 6.5 | 9.6 | 0.0 | 0.0 | 11.1 | 7.1 | 7.7 | 0.0 | 9.1 |
| 6 | Gemini 3.1 Flash Lite | 3.3 | 1.9 | 0.0 | 0.0 | 5.6 | 14.3 | 0.0 | 0.0 | 9.1 |

<details>
<summary><b>任务类别 (15 个类别, 153 个任务)</b></summary>

| 类别 | 数量 | 示例平台 |
|----------|:-----:|-------------------|
| 日常生活 | 21 | Uber Eats, DoorDash, Instacart, Zillow, Craigslist |
| 娱乐与爱好 | 15 | Ticketmaster, AMC Theatres, Topgolf, Crunchyroll |
| 创建与初始化 | 13 | Squarespace, Wix, Webflow, Ghost, Substack |
| 评分与投票 | 10 | Trustpilot, G2, Goodreads, RateMyProfessors |
| 旅行 | 9 | Booking.com, Expedia, Airbnb, TripAdvisor |
| 教育与学习 | 9 | Coursera, Udemy, Khan Academy, Duolingo |
| 办公与秘书 | 9 | Google Calendar, Slack, Notion, Trello |
| 美容与个护 | 9 | Sephora, Ulta, Glossier |
| 求职与 HR | 8 | LinkedIn, Greenhouse, Lever, Workday |
| 宠物与动物护理 | 8 | Chewy, Petco, Rover |
| 个人管理 | 6 | Mint, YNAB, Todoist |
| 购物与电商 | 6 | Amazon, eBay, Etsy, Target |
| 非营利与慈善 | 6 | GoFundMe, DonorsChoose |
| 学术与研究 | 5 | Google Scholar, Semantic Scholar, OpenReview |
| 金融与投资 | 4 | Robinhood, Fidelity, Coinbase |
| 其他 | 15 | 自动化、开发与技术、政府、家居服务、汽车 |

</details>

<br/>

## 架构

<details>
<summary>容器内部结构</summary>

```
┌─────────────────────────────────────────────────┐
│  容器 (Docker / Podman)                          │
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

</details>

<br/>

# <img src="static/icons/terminal.svg" width="28" height="28"> 命令行

```bash
# 交互式 TUI (推荐):
./run.sh

# 单次运行:
uv run --project test-driver test-driver/run.py test-cases/001-daily-life-food-uber-eats claude-sonnet-4-6

# 人工模式 (通过 noVNC 控制浏览器):
uv run --project test-driver test-driver/run.py test-cases/001-daily-life-food-uber-eats --human

# 批量运行 (所有模型 x 用例 1-50, 3 个并发):
uv run --project test-driver test-driver/batch.py --all-models --case-range 1-50 --max-concurrent 3
```

完整 CLI 文档、批量运行参数、测试用例格式和输出结构详见 [test-driver/README.md](test-driver/README.md)。

<br/>

# <img src="static/icons/chart-bar.svg" width="28" height="28"> 测评

测评是**运行之后**的步骤 -- 先运行智能体收集轨迹,再将轨迹与人类参考运行进行对比评估。

```
 1. 运行智能体 (test-driver)        2. 测评 (eval/)
 ────────────────────────           ────────────────────────────────
 ./run.sh 或 batch.py        ──►    Claude Code 子代理对比
 生成 test-output/                  智能体 vs 人类轨迹
   含五层录制数据                    按 eval/agentic_eval.md rubric 判定
```

测评器将智能体轨迹与人类参考轨迹在五层录制数据（视频、截图、HTTP 流量、浏览器动作、智能体消息）上进行逐步对比,输出 PASS/FAIL 及带证据的判定理由。

完整测评指南和 Claude Code prompt 模板详见 [eval/README.md](eval/README.md)。

<br/>

# <img src="static/icons/circle-question.svg" width="28" height="28"> 常见问题

<details>
<summary><b>每次运行会产生什么数据?</b></summary>

每次会话会在 `/data/` 下记录五层同步数据:

| 层 | 文件 | 描述 |
|-------|------|-------------|
| 会话回放 | `recording.mp4` | 完整的会话视频 (H.264, 15fps) |
| 动作截图 | `screenshots/*.png` | 每个浏览器动作的带时间戳 PNG |
| 浏览器动作 | `actions.jsonl` | 每个 DOM 事件 (click, keydown, input, pageLoad, scroll 等) |
| HTTP 流量 | `requests.jsonl` | 每个 HTTP 请求,包含 headers、body 和查询参数 |
| 智能体消息 | `agent-messages.jsonl` | 完整的智能体对话记录 (思考、文本、工具调用) |

拦截结果保存在 `interception.json` 中。

</details>

<details>
<summary><b>请求拦截器如何工作?</b></summary>

拦截器会阻止关键的、不可逆的 HTTP 请求 (结账、表单提交、邮件发送) 以防止真实副作用。它通过 CDP 的 `Fetch` 域连接到 Chrome,并将请求与评测 schema (`url_pattern` 正则 + `method` + 可选的 `body`/`params`) 进行匹配。命中时,它会将被阻止的请求保存到 `interception.json`,杀掉智能体并停止录制。

拦截器**不**验证任务完成 -- 评测由独立的评估器在会话结束后处理。

对于在支付墙后的任务 (智能体没有有效的信用卡),评测 schema 使用一个永不匹配的占位模式,因此会话会一直运行到超时。

</details>

<details>
<summary><b>合成用户档案是什么?</b></summary>

每个容器都有一个 `/my-info/` 目录,包含一个虚拟用户身份 (Alex Green): 个人信息 JSON、邮箱凭证和简历 PDF。邮箱是每次运行时新创建的一次性 PurelyMail 地址。智能体在需要填写表单、注册账号等时会读取这些文件。

源模板: `shared/alex_green_personal_info.json` (档案) 和 `test-driver/resume_template.json` (简历)。

</details>

<details>
<summary><b>可以用 Podman 代替 Docker 吗?</b></summary>

可以。设置 `export CONTAINER_ENGINE=podman`。框架会自动检测可用的引擎。Podman 无需 root 权限。

</details>

<details>
<summary><b>智能体可以使用哪些工具?</b></summary>

OpenClaw 智能体只能使用浏览器工具和一组受限的只读 shell 命令 (`ls`、`cat`、`find`、`grep`、`head`、`tail`、`jq`、`wc` 等)。可能绕过浏览器的命令 (`curl`、`python`、`node`、`wget`) 会被阻止。智能体指令也明确要求只通过浏览器完成任务。

</details>

<details>
<summary><b>如何添加新的测试用例?</b></summary>

参见 [CONTRIBUTING.md](CONTRIBUTING.md)。简言之: 在 `test-cases/` 下创建目录,编写符合 `test-cases/task.schema.json` 的 `task.json`,定义评测 schema,用人工模式测试,然后提交 PR。

</details>

<br/>

## 贡献

我们欢迎贡献 -- 尤其是新的测试用例。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 引用

如果你在研究中使用了 ClawBench,请引用:

```bibtex
@misc{zhang2026clawbench,
  title         = {ClawBench: Can AI Agents Complete Everyday Online Tasks?},
  author        = {Yuxuan Zhang and Yubo Wang and Yipeng Zhu and Penghui Du and Junwen Miao and Xuan Lu and Wendong Xu and Yunzhuo Hao and Songcheng Cai and Xiaochen Wang and Huaisong Zhang and Xian Wu and Yi Lu and Minyi Lei and Kai Zou and Huifeng Yin and Ping Nie and Liang Chen and Dongfu Jiang and Wenhu Chen and Kelsey R. Allen},
  year          = {2026},
  eprint        = {2604.08523},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2604.08523}
}
```

## 核心贡献者

<table>
<tr>
<td align="center">
<a href="https://github.com/reacher-z">
<img src="https://github.com/reacher-z.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Yuxuan Zhang</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/Wyyyb">
<img src="https://github.com/Wyyyb.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Yubo Wang</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/Perry2004">
<img src="https://github.com/Perry2004.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Perry Zhu</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/eternaldolphin">
<img src="https://github.com/eternaldolphin.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Penghui Du</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/MEKSAAA">
<img src="https://github.com/MEKSAAA.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Junwen Miao</b></sub>
</a>
</td>
</tr>
</table>

## 指导老师

<table>
<tr>
<td align="center">
<a href="https://github.com/k-r-allen">
<img src="https://github.com/k-r-allen.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Kelsey R. Allen</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/wenhuchen">
<img src="https://github.com/wenhuchen.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Wenhu Chen</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/jdf-prog">
<img src="https://github.com/jdf-prog.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Dongfu Jiang</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/chenllliang">
<img src="https://github.com/chenllliang.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Liang Chen</b></sub>
</a>
</td>
</tr>
</table>

## 许可证与致谢

Apache 2.0 -- 详见 [LICENSE](LICENSE)。

基于以下开源项目构建: [OpenClaw](https://github.com/openclaw/openclaw), [noVNC](https://github.com/novnc/noVNC) (MPL 2.0), [websockify](https://github.com/novnc/websockify) (LGPL 3.0)。
