<div align="center">

# ClawBench

[![arXiv](https://img.shields.io/badge/arXiv-2604.08523-b31b1b.svg)](https://arxiv.org/abs/2604.08523)
[![Project Page](https://img.shields.io/badge/Project-Page-blue.svg)](https://claw-bench.com)
[![GitHub stars](https://img.shields.io/github/stars/reacher-z/ClawBench?style=social)](https://github.com/reacher-z/ClawBench)

**⚡ Run in one line of code**

### Can AI Agents Complete Everyday Online Tasks?

We asked 6 frontier AI agents to do what people do every day --<br/>
order food, book travel, apply for jobs, write reviews, manage projects.<br/>
**The best model completed only 33.3% of tasks.**

[Paper](https://arxiv.org/abs/2604.08523) &nbsp;&bull;&nbsp; [Project Page](https://claw-bench.com) &nbsp;&bull;&nbsp; [Leaderboard](#-results)

---

**153** everyday tasks &nbsp;&middot;&nbsp; **144** live websites &nbsp;&middot;&nbsp; **15** life categories

<a href="README.zh-CN.md"><img src="static/icons/language.svg" width="16" height="16"> 中文</a>

</div>

<br/>

<p align="center">
<img src="static/icons/globe.svg" width="24" height="24">&nbsp;<b>Live Websites</b>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="static/icons/cube.svg" width="24" height="24">&nbsp;<b>Isolated Containers</b>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="static/icons/shield-halved.svg" width="24" height="24">&nbsp;<b>Request Interceptor</b>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="static/icons/layer-group.svg" width="24" height="24">&nbsp;<b>Five-Layer Recording</b>
</p>

<br/>

## How It Works

```
   You pick a task            ClawBench spins up           Agent drives the         Interceptor catches
   from 153 real-world        an isolated Docker           browser: navigates,      the final action &
   everyday scenarios         container + Chromium         fills forms, clicks      records everything
                                                                                    
   ┌──────────────┐           ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
   │  "Book a pet │    ──►    │   Container  │    ──►    │   AI Agent   │    ──►    │  Intercepted │
   │   sitter on  │           │  + Chromium  │           │  browses the │           │   5 layers   │
   │   Rover"     │           │  + Agent     │           │   live site  │           │   recorded   │
   └──────────────┘           └──────────────┘           └──────────────┘           └──────────────┘
```

<br/>

# <img src="static/icons/robot.svg" width="28" height="28"> LLM Quick Start

Point your coding agent (Claude Code, Cursor, Copilot, etc.) at [`AGENTS.md`](AGENTS.md) and prompt away.

<br/>

# <img src="static/icons/person.svg" width="28" height="28"> Human Quick Start

```bash
git clone https://github.com/reacher-z/ClawBench.git && cd ClawBench && ./run.sh
```

**Prerequisites:** [Python 3.11+](https://python.org), [uv](https://docs.astral.sh/uv/), and a container engine — [Docker](https://www.docker.com/) **or** [Podman](https://podman.io/). ClawBench auto-detects whichever is installed; force one with `export CONTAINER_ENGINE=docker` or `export CONTAINER_ENGINE=podman`.

<details>
<summary><b>Install Docker or Podman</b> (macOS / Linux / Windows)</summary>

#### macOS

```bash
# Option A — Docker Desktop (easiest, includes GUI)
brew install --cask docker
open -a Docker                 # launch and wait for the whale icon to settle

# Option B — Podman (rootless, no daemon, CLI only)
brew install podman
podman machine init            # one-time: downloads the Linux VM image
podman machine start           # must be running before any podman command
```

> **macOS Podman needs a VM.** `brew install podman` alone is not enough — Podman on macOS runs containers inside a small Linux VM, so you must `podman machine init && podman machine start` once after install or `podman info` will fail with `Cannot connect to Podman`.

#### Linux (Ubuntu / Debian)

```bash
# Option A — Podman (rootless by default, recommended)
sudo apt update && sudo apt install -y podman

# Option B — Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER  # log out / back in so your shell picks up the group
```

> **Rootful Docker ownership note:** with classic `sudo`-docker, files extracted from containers land owned by `root` on the host. ClawBench's driver detects this after each run and chowns `test-output/` back to your user automatically — but if you run other container tooling alongside, rootless Podman (or rootless Docker) avoids the issue entirely.

#### Windows

```powershell
# Option A — Docker Desktop (WSL2 backend)
winget install Docker.DockerDesktop
# then launch Docker Desktop from the Start menu and wait for it to be ready

# Option B — Podman
winget install RedHat.Podman
podman machine init
podman machine start
```

> Run the `uv run …` commands below from **PowerShell**, **WSL2**, or **Git Bash**. Like macOS, Windows Podman requires `podman machine init && podman machine start` before its first use.

</details>

**1. Clone and configure:**
```bash
git clone https://github.com/reacher-z/ClawBench.git && cd ClawBench
cp models/models.example.yaml models/models.yaml   # edit: add your model API keys
# `.env` (PurelyMail creds for disposable-email signups) is already committed
# and works out of the box. Edit it only to override defaults or add HF_TOKEN.
```

> [!NOTE]
> **First run builds a container image** (chromium + ffmpeg + noVNC + Node + openclaw, roughly **2 GB** download, **5–10 min** on a decent connection). You'll see a live progress spinner with the current build step. Subsequent runs reuse the cached layers and finish in seconds.

**2. Run your first task** (pick one):

> [!TIP]
> **Recommended &rarr; Interactive TUI** &nbsp; guided model + test case selection
> ```bash
> ./run.sh
> ```
> Needs an interactive terminal. For pipes / CI / non-TTY, call `test-driver/run.py` or `test-driver/batch.py` directly.

**(b) Run one specific task against a specific model:**
```bash
uv run --project test-driver test-driver/run.py \
  test-cases/001-daily-life-food-uber-eats claude-sonnet-4-6
```
Once the container starts, the script prints a **noVNC URL** (e.g. `http://localhost:6080/vnc.html`) — open it in your browser to watch the agent operate in real-time. If port 6080 is already in use, an alternative port is chosen automatically.

Results land in `test-output/<model>/<timestamp>-001-.../` with the full five-layer recording.

**(c) Drive the browser yourself via noVNC** — produces a human reference run:
```bash
uv run --project test-driver test-driver/run.py \
  test-cases/001-daily-life-food-uber-eats --human
```
Open the noVNC URL the script prints, complete the task by hand, then close the tab. Port is auto-assigned if 6080 is busy.

<br/>

# <img src="static/icons/chart-bar.svg" width="28" height="28"> ClawBench-Lite

**New here? Run this first.** [`test-cases/lite.json`](test-cases/lite.json) is a **20-task curated subset** of the full 153, selected for household-name sites, real-world relevance, difficulty, and category diversity. It matches the 20-tasks-per-source convention of [browser-use/benchmark](https://github.com/browser-use/benchmark) and gives you a credible signal at a fraction of the full-benchmark cost.

Tier distribution: **flagship 9 / core 8 / wildcard 3** — spanning daily life (OpenTable, DoorDash, Instacart, TaskRabbit), entertainment (Eventbrite, Goodreads, Fandango), creation (Asana, Mailchimp, Squarespace), travel (Airbnb), education (LeetCode), dev-tech (GitHub), academia (Overleaf), personal management (1Password), and more. All Lite tasks are judged by [`eval/agentic_eval.md`](eval/agentic_eval.md) regardless of `url_pattern` shape.

See [`test-cases/lite.schema.json`](test-cases/lite.schema.json) for the manifest shape and the `notes` field in `lite.json` for the 4-axis selection rubric + full swap history.

<br/>

# <img src="static/icons/video.svg" width="28" height="28"> Tutorial

<div align="center">

<!-- TODO: Replace with actual video links -->

[![Watch on YouTube](https://img.shields.io/badge/Watch_Tutorial-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com)
&nbsp;&nbsp;
[![Watch on Bilibili](https://img.shields.io/badge/Watch_Tutorial-Bilibili-00A1D6?style=for-the-badge&logo=bilibili&logoColor=white)](https://bilibili.com)

</div>

<br/>

# <img src="static/icons/play.svg" width="28" height="28"> Demos

<!-- TODO: Replace with actual demo GIFs/recordings -->

<table>
<tr>
<td width="50%" align="center">

**Ordering food on Uber Eats**

https://github.com/user-attachments/assets/placeholder-uber-eats

</td>
<td width="50%" align="center">

**Submitting a job application**

https://github.com/user-attachments/assets/placeholder-greenhouse

</td>
</tr>
</table>

> Each ClawBench run produces a full MP4 session recording. See the [project page](https://claw-bench.com) for all 153 task recordings.

<br/>

# <img src="static/icons/circle-question.svg" width="28" height="28"> Example Walkthrough

Curious what one task actually looks like, start to finish? Here's task **001** end to end.

**The task** — from [`test-cases/001-daily-life-food-uber-eats/task.json`](test-cases/001-daily-life-food-uber-eats/task.json):

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

The agent gets this `instruction` verbatim, plus read-only access to `/my-info/alex_green_personal_info.json` (the dummy user's name, home address, phone, date of birth) and a disposable email account for any sign-in prompt. It has **30 minutes** to reach a `POST` request — any longer and the container is killed.

**What the agent does** (the happy path):

1. Navigates to `ubereats.com`
2. Reads the dummy user's home address from `/my-info/alex_green_personal_info.json` and enters it in the delivery-address box
3. Searches for **"Pad Thai"** in the food search
4. Picks a restaurant that has Pad Thai available for delivery to that address
5. Opens the item detail page, finds the customization or special-instructions field, enters **"no peanuts"**
6. Adds one to cart, opens the cart, and handles any sign-in prompt using the disposable email credentials
7. Reaches checkout, taps **Place Order**

**What the interceptor catches** — that final *Place Order* tap fires a `POST` request. ClawBench's request interceptor sits in front of the browser and **captures the outbound request before it reaches Uber Eats's servers**, so the dummy user is never actually charged. At the exact moment of interception, all five recording layers (MP4 video, PNG screenshots, HTTP traffic, browser actions, agent messages) are frozen into `/data/`.

**How the judge decides PASS / FAIL** — task 001's `url_pattern` is the intentional sentinel `__PLACEHOLDER_WILL_NOT_MATCH__`, which means **no request path can mechanically match**. The verdict comes from the agentic judge in [`eval/agentic_eval.md`](eval/agentic_eval.md), which replays the five-layer recording against a human reference run and checks four things:

- Did the agent actually reach the final checkout step?
- Is the cart exactly **one** Pad Thai (not two, not a combo)?
- Is the delivery address the user's home address from `alex_green_personal_info.json`?
- Does the order carry the **"no peanuts"** note in the instructions field?

All four must hold for a **PASS**. Miss any one and it's a **FAIL** with evidence from the recording pinned to the failing criterion. This per-task rubric is what makes ClawBench judge-sensitive rather than URL-regex-sensitive — see [`eval/README.md`](eval/README.md) for the full rubric format and [`eval/agentic_eval.md`](eval/agentic_eval.md) for the judge prompt.

<br/>

# <img src="static/icons/chart-bar.svg" width="28" height="28"> Results

<div align="center">

**Success rate (%) of 6 frontier AI agents on ClawBench**

</div>

| Rank | Model | Overall | Daily | Finance | Work | Dev | Academic | Travel | Social | Pets |
|:----:|-------|:-------:|:-----:|:-------:|:----:|:---:|:--------:|:------:|:------:|:----:|
| 1 | **Claude Sonnet 4.6** | **33.3** | 44.2 | **50.0** | 19.0 | 11.1 | **50.0** | 23.1 | **38.9** | **18.2** |
| 2 | GLM-5 | 24.2 | **30.8** | 16.7 | **38.1** | 16.7 | 28.6 | 0.0 | 16.7 | **18.2** |
| 3 | Gemini 3 Flash | 19.0 | 15.4 | 33.3 | 23.8 | **22.2** | 28.6 | **30.8** | 11.1 | 0.0 |
| 4 | Claude Haiku 4.5 | 18.3 | 15.4 | 22.2 | 19.0 | **27.8** | 21.4 | 7.7 | 16.7 | **18.2** |
| 5 | GPT-5.4 | 6.5 | 9.6 | 0.0 | 0.0 | 11.1 | 7.1 | 7.7 | 0.0 | 9.1 |
| 6 | Gemini 3.1 Flash Lite | 3.3 | 1.9 | 0.0 | 0.0 | 5.6 | 14.3 | 0.0 | 0.0 | 9.1 |

<details>
<summary><b>Task Categories (15 categories, 153 tasks)</b></summary>

| Category | Tasks | Example Platforms |
|----------|:-----:|-------------------|
| Daily Life | 21 | Uber Eats, DoorDash, Instacart, Zillow, Craigslist |
| Entertainment & Hobbies | 15 | Ticketmaster, AMC Theatres, Topgolf, Crunchyroll |
| Creation & Initialization | 13 | Squarespace, Wix, Webflow, Ghost, Substack |
| Rating & Voting | 10 | Trustpilot, G2, Goodreads, RateMyProfessors |
| Travel | 9 | Booking.com, Expedia, Airbnb, TripAdvisor |
| Education & Learning | 9 | Coursera, Udemy, Khan Academy, Duolingo |
| Office & Secretary | 9 | Google Calendar, Slack, Notion, Trello |
| Beauty & Personal Care | 9 | Sephora, Ulta, Glossier |
| Job Search & HR | 8 | LinkedIn, Greenhouse, Lever, Workday |
| Pet & Animal Care | 8 | Chewy, Petco, Rover |
| Personal Management | 6 | Mint, YNAB, Todoist |
| Shopping & Commerce | 6 | Amazon, eBay, Etsy, Target |
| Nonprofit & Charity | 6 | GoFundMe, DonorsChoose |
| Academia & Research | 5 | Google Scholar, Semantic Scholar, OpenReview |
| Finance & Investment | 4 | Robinhood, Fidelity, Coinbase |
| Others | 15 | Automation, Dev & Tech, Government, Home Services, Automotive |

</details>

<br/>

## Architecture

<details>
<summary>Container internals</summary>

```
┌─────────────────────────────────────────────────┐
│  Container (Docker / Podman)                    │
│                                                 │
│  ┌───────────┐   DOM events  ┌──────────────┐   │
│  │ content.js├──────────────►│ background.js│   │
│  │ (per tab) │               │  (service    │   │
│  └───────────┘               │   worker)    │   │
│                              └──┬──────┬────┘   │
│                                 │      │        │
│                         actions │      │ screenshots
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

# <img src="static/icons/terminal.svg" width="28" height="28"> CLI

```bash
# Interactive TUI (recommended):
./run.sh

# Single run:
uv run --project test-driver test-driver/run.py test-cases/001-daily-life-food-uber-eats claude-sonnet-4-6

# Human mode (you control the browser via noVNC):
uv run --project test-driver test-driver/run.py test-cases/001-daily-life-food-uber-eats --human

# Batch (all models x cases 1-50, 3 concurrent):
uv run --project test-driver test-driver/batch.py --all-models --case-range 1-50 --max-concurrent 3
```

See [test-driver/README.md](test-driver/README.md) for full CLI documentation, batch runner flags, test case format, and output structure.

<br/>

# <img src="static/icons/chart-bar.svg" width="28" height="28"> Evaluation

Evaluation is a **post-session** step -- first run agents to collect trajectories, then evaluate them against human reference runs.

```
 1. Run agents (test-driver)       2. Evaluate (eval/)
 ─────────────────────────         ────────────────────────────────
 ./run.sh  or  batch.py     ──►    Claude Code subagents compare
 produces test-output/             agent vs human trajectories
   with 5-layer recordings         under eval/agentic_eval.md rubric
```

The evaluator compares each agent trajectory against a human reference trajectory across all five recording layers (video, screenshots, HTTP traffic, browser actions, agent messages), then outputs PASS/FAIL with evidence-backed justification.

See [eval/README.md](eval/README.md) for the full evaluation guide and Claude Code prompt template.

<br/>

# <img src="static/icons/circle-question.svg" width="28" height="28"> FAQ

<details>
<summary><b>What data does each run produce?</b></summary>

Each session records five layers of synchronized data under `/data/`:

| Layer | File | Description |
|-------|------|-------------|
| Session replay | `recording.mp4` | Full session video (H.264, 15fps) |
| Action screenshots | `screenshots/*.png` | Timestamped PNG per browser action |
| Browser actions | `actions.jsonl` | Every DOM event (click, keydown, input, pageLoad, scroll, etc.) |
| HTTP traffic | `requests.jsonl` | Every HTTP request with headers, body, and query params |
| Agent messages | `agent-messages.jsonl` | Full agent conversation transcript (thinking, text, tool calls) |

The interceptor result is saved to `interception.json`.

</details>

<details>
<summary><b>How does the request interceptor work?</b></summary>

The interceptor blocks critical, irreversible HTTP requests (checkout, form submit, email send) to prevent real-world side effects. It connects to Chrome via CDP's `Fetch` domain and matches requests against the eval schema (`url_pattern` regex + `method` + optional `body`/`params`). When triggered, it saves the blocked request to `interception.json`, kills the agent, and stops recording.

The interceptor does **not** validate task completion -- evaluation is handled separately by evaluators post-session.

For tasks behind payment walls (agent has no valid credit card), the eval schema uses a placeholder pattern that never matches, so the session runs until timeout.

</details>

<details>
<summary><b>What is the synthetic user profile?</b></summary>

Each container gets a `/my-info/` directory with a dummy user identity (Alex Green): personal info JSON, email credentials, and a resume PDF. The email is a fresh disposable PurelyMail address generated per run. The agent reads these files when it needs to fill forms, register accounts, etc.

Source templates: `shared/alex_green_personal_info.json` (profile) and `test-driver/resume_template.json` (resume).

</details>

<details>
<summary><b>Can I use Podman instead of Docker?</b></summary>

Yes. Set `export CONTAINER_ENGINE=podman`. The framework auto-detects whichever is available. Podman works without root privileges.

</details>

<details>
<summary><b>What tools can the agent use?</b></summary>

The OpenClaw agent can only use the browser tool and a restricted set of read-only shell commands (`ls`, `cat`, `find`, `grep`, `head`, `tail`, `jq`, `wc`, etc.). Commands that could bypass the browser (`curl`, `python`, `node`, `wget`) are blocked. The agent instruction also explicitly requires browser-only task completion.

</details>

<details>
<summary><b>How do I add a new test case?</b></summary>

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: create a directory under `test-cases/` with a `task.json` conforming to `test-cases/task.schema.json`, define the eval schema, test with human mode, and submit a PR.

</details>

<br/>

## Contributing

We welcome contributions -- especially new test cases. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Citation

If you use ClawBench in your research, please cite:

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

## Core Contributors

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

## Advisors

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

## License & Acknowledgments

Apache 2.0 -- see [LICENSE](LICENSE).

Built with [OpenClaw](https://github.com/openclaw/openclaw), [noVNC](https://github.com/novnc/noVNC) (MPL 2.0), and [websockify](https://github.com/novnc/websockify) (LGPL 3.0).
