<div align="center">

# ClawBench

[![Paper](https://img.shields.io/badge/Paper-COLM_2026-red.svg)](https://claw-bench.com)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

**Can AI Agents Complete Everyday Online Tasks?**

153 everyday tasks &middot; 144 live websites &middot; 15 life categories

**English** | [中文](README.zh-CN.md)

</div>

<br/>

<table>
<tr>
<td align="center" width="25%">
<img src="static/icons/globe.svg" width="36" height="36"><br/>
<b>Live Websites</b><br/>
<sub>144 real production sites, not sandboxed clones</sub>
</td>
<td align="center" width="25%">
<img src="static/icons/cube.svg" width="36" height="36"><br/>
<b>Isolated Containers</b><br/>
<sub>Each run in its own Docker container with Chromium</sub>
</td>
<td align="center" width="25%">
<img src="static/icons/shield-halved.svg" width="36" height="36"><br/>
<b>Request Interceptor</b><br/>
<sub>Blocks the final irreversible action to prevent side effects</sub>
</td>
<td align="center" width="25%">
<img src="static/icons/layer-group.svg" width="36" height="36"><br/>
<b>Five-Layer Recording</b><br/>
<sub>MP4 replay, screenshots, HTTP traffic, actions, agent messages</sub>
</td>
</tr>
</table>

<br/>

# <img src="static/icons/robot.svg" width="28" height="28"> LLM Quick Start

1. Point your coding agent (Claude Code, Cursor, Copilot, etc.) at [`AGENTS.md`](AGENTS.md)
2. Prompt away!

<br/>

# <img src="static/icons/person.svg" width="28" height="28"> Human Quick Start

**Prerequisites:** [Python 3.11+](https://python.org), [uv](https://docs.astral.sh/uv/), [Docker](https://www.docker.com/) or [Podman](https://podman.io/)

**1. Clone and configure:**
```bash
git clone https://github.com/reacher-z/ClawBench.git && cd ClawBench
cp .env.example .env          # Edit: add PURELY_MAIL_API_KEY + PURELY_MAIL_DOMAIN
cp models/models.example.yaml models/models.yaml   # Edit: add your model API keys
```

**2. Launch the interactive TUI:**
```bash
./run.sh
```

The TUI guides you through model selection, test case picking, and run mode (single / batch / human baseline).

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

# <img src="static/icons/chart-bar.svg" width="28" height="28"> Results

Success rate (%) of 6 frontier AI agents on ClawBench. Even the strongest model completes only 33.3% of tasks.

| Rank | Model | Overall | Daily | Finance | Work | Dev | Academic | Travel | Social | Pets |
|------|-------|---------|-------|---------|------|-----|----------|--------|--------|------|
| 1 | Claude Sonnet 4.6 | **33.3** | 44.2 | **50.0** | 19.0 | 11.1 | **50.0** | 23.1 | **38.9** | **18.2** |
| 2 | GLM-5 | 24.2 | **30.8** | 16.7 | **38.1** | 16.7 | 28.6 | 0.0 | 16.7 | **18.2** |
| 3 | Gemini 3 Flash | 19.0 | 15.4 | 33.3 | 23.8 | **22.2** | 28.6 | **30.8** | 11.1 | 0.0 |
| 4 | Claude Haiku 4.5 | 18.3 | 15.4 | 22.2 | 19.0 | **27.8** | 21.4 | 7.7 | 16.7 | **18.2** |
| 5 | GPT-5.4 | 6.5 | 9.6 | 0.0 | 0.0 | 11.1 | 7.1 | 7.7 | 0.0 | 9.1 |
| 6 | Gemini 3.1 Flash Lite | 3.3 | 1.9 | 0.0 | 0.0 | 5.6 | 14.3 | 0.0 | 0.0 | 9.1 |

<details>
<summary><b>Task Categories (15 categories, 153 tasks)</b></summary>

| Category | Tasks | Example Platforms |
|----------|-------|-------------------|
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
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf qwen3.5-397b-a17b

# Human mode (you control the browser via noVNC):
uv run --project test-driver test-driver/run.py test-cases/886-entertainment-hobbies-experience-topgolf --human

# Batch (all models x cases 1-50, 3 concurrent):
uv run --project test-driver test-driver/batch.py --all-models --case-range 1-50 --max-concurrent 3
```

See [test-driver/README.md](test-driver/README.md) for full CLI documentation, batch runner flags, test case format, and output structure.

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
@inproceedings{zhang2026clawbench,
  title     = {ClawBench: Can AI Agents Complete Everyday Online Tasks?},
  author    = {Yuxuan Zhang and Yubo Wang and Yipeng Zhu and Penghui Du and Junwen Miao and Xuan Lu and Wendong Xu and Yunzhuo Hao and Songcheng Cai and Xiaochen Wang and Huaisong Zhang and Xian Wu and Yi Lu and Minyi Lei and Kai Zou and Huifeng Yin and Ping Nie and Liang Chen and Dongfu Jiang and Wenhu Chen and Kelsey R. Allen},
  booktitle = {Conference on Language Modeling (COLM)},
  year      = {2026},
  url       = {https://claw-bench.com}
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
<a href="https://github.com/Perry2004">
<img src="https://github.com/Perry2004.png" width="80" height="80" style="border-radius:50%"><br/>
<sub><b>Perry Zhu</b></sub>
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

## License & Acknowledgments

Apache 2.0 -- see [LICENSE](LICENSE).

Built with [OpenClaw](https://github.com/openclaw/openclaw), [noVNC](https://github.com/novnc/noVNC) (MPL 2.0), and [websockify](https://github.com/novnc/websockify) (LGPL 3.0).
