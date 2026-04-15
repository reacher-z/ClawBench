# ClawBench Press Kit

One-stop paste-and-send pack for getting ClawBench picked up across AI-news
aggregators, research-paper summary sites, and developer newsletters. Copy a
pitch variant, open the submission channel, send. Track status in the
distribution table at the bottom.

## The Golden Three (always cite these three numbers)

- **153** everyday web tasks across **144** live production websites in **15** life categories
- **7** frontier AI models evaluated; the best passes **33.3%** of tasks
- A **submission-interception layer** lets agents run end-to-end on real sites without real-world side effects

## Canonical assets

| What | Where |
|---|---|
| Paper | https://arxiv.org/abs/2604.08523 |
| HF paper page | https://huggingface.co/papers/2604.08523 |
| Dataset | https://huggingface.co/datasets/NAIL-Group/ClawBench |
| Code | https://github.com/reacher-z/ClawBench |
| Project site | https://claw-bench.com |
| Install (one line) | `uv tool install clawbench-eval && clawbench` |

## Contact block (use in every outbound)

```
Yuxuan Zhang, first author
Paper: arxiv.org/abs/2604.08523
Code: github.com/reacher-z/ClawBench
Project site: claw-bench.com
Media contact: <REPLACE with your email>
```

---

## Pitch variants

### V1 — Tweet / short post (280 chars)

```
New benchmark: ClawBench. 153 everyday web tasks on 144 live production
websites — checkout, booking, job apps, not sandboxed mirrors. Ran 7 frontier
agents; best passes 33.3%. Interception layer prevents real-world side effects.
arxiv.org/abs/2604.08523
```

### V2 — Short editorial blurb (150 words)

```
ClawBench is a new benchmark for AI browser agents, released this week on arXiv.
Unlike WebArena or VisualWebArena, it runs agents directly on live production
websites — the same Grubhub, Indeed, Amazon, United Airlines flows a human
would use — across 153 everyday tasks spanning 15 categories (shopping, travel,
jobs, forms, finance). A lightweight submission-interception layer captures
the final write request so agents don't actually place real orders or submit
real applications.

The result is a large gap between lab and reality: 7 frontier models evaluated,
and the strongest passes only 33.3%. Most score under 40%. Models that do well
on sandboxed benchmarks (65-75% on WebArena/OSWorld) regress sharply on
site-specific friction — cookie banners, date pickers, captchas, form validators.

Paper: https://arxiv.org/abs/2604.08523
Code + live leaderboard: https://github.com/reacher-z/ClawBench
```

### V3 — Full email pitch (400 words)

Use for editor-targeted cold emails. Replace the `<...>` placeholders.

```
Subject: New benchmark — AI browser agents top out at 33.3% on everyday web tasks

Hi <editor first name>,

We just released ClawBench, a benchmark for AI browser agents that runs them
on live production websites rather than sandboxed mirrors. The paper is on
arXiv (arxiv.org/abs/2604.08523) and the HF paper page is at
huggingface.co/papers/2604.08523.

Why it matters for <publication>:
Existing browser-agent benchmarks (WebArena, VisualWebArena, OSWorld) use
static HTML and simulated DOMs. They miss what actually breaks agents in
production: cookie consent modals, dynamic JavaScript rendering, multi-step
OAuth, and site-specific form validators. ClawBench evaluates 153 everyday
tasks on 144 real websites (Grubhub, Indeed, Amazon, United, H&R Block, etc.)
across 15 categories covering shopping, travel, jobs, government forms,
finance, and developer workflows.

A lightweight submission-interception layer, implemented via a Chrome extension
and CDP, captures and blocks only the final write request. That preserves
ecological validity without triggering real purchases, emails, or applications.

The result is a large gap between sandboxed and real-world performance:
- 7 frontier models evaluated
- Best model passes 33.3% of tasks
- Most models score under 40%
- Models scoring 65-75% on WebArena drop to sub-40% here

The repo ships a Chrome extension, a test driver, and a one-line install
(`uv tool install clawbench-eval`), so you can reproduce any run on your own
machine. The live leaderboard is at claw-bench.com.

Happy to run any specific task live for the piece or send a screen recording
of an agent failing on a real site — the failure modes are often more
informative than the pass rate.

Best,
<Your name>
<Affiliation>
<Email>

Paper: https://arxiv.org/abs/2604.08523
Code: https://github.com/reacher-z/ClawBench
Project site: https://claw-bench.com
```

### V4 — Chinese pitch (中文媒体投稿)

投稿邮箱：见下方分发表；主送+抄送一起发。

```
主题：新基准测评：AI 浏览器 agent 在真实网页上的真实表现

编辑您好,

我们刚发布了 ClawBench —— 首个聚焦真实生产网页的 AI 浏览器 agent 评测基准,
论文已上线 arXiv (arxiv.org/abs/2604.08523)。

与 WebArena、VisualWebArena 等采用静态沙盒的测评不同,ClawBench 直接在 144 个
真实网站上跑 153 个日常任务——下单、订票、投简历、填表——覆盖 15 个生活类别
(电商、出行、招聘、政务、金融、开发者工具)。

我们设计了一个轻量级"提交拦截层",通过 Chrome 扩展 + CDP 在最后一步写请求前
拦截,既保留了真实环境的完整性,又不会产生真实购买/邮件/申请。

核心发现:
- 评测 7 个前沿大模型
- 最强模型仅通过 33.3% 的任务
- 大部分模型在 40% 以下
- 在 WebArena 上 65-75% 的模型,到这里普遍掉到 40% 以下

仓库提供一键安装 (`uv tool install clawbench-eval`) 和完整 Chrome 插件,
任何读者都可以复现。Leaderboard 实时更新于 claw-bench.com。

欢迎直接使用、也欢迎报道 —— 如果需要补充素材(真实站点 agent 失败录屏、按类别
细分结果、具体失败 case),随时联系。

一作:张宇宣
机构:<待补充 UBC / Vector Institute>
Paper: arxiv.org/abs/2604.08523 | Repo: github.com/reacher-z/ClawBench
```

---

## Distribution table (22 venues, ranked)

| # | Venue | URL | Channel | Pitch | Status |
|---|---|---|---|---|---|
| 1 | **MarkTechPost** | marktechpost.com/article-submission/ | Form | V2 + paper link | TODO — covered BrowseComp, direct precedent |
| 2 | **The Decoder** | the-decoder.com/publish-with-us/ | Form + `hello@the-decoder.com` | V2 | TODO — 24-48h response SLA |
| 3 | **Unite.AI Insight Reports** | unite.ai/reports/ | Form | V3 | TODO — best structured channel |
| 4 | **VentureBeat AI desk** | venturebeat.com | `tips@venturebeat.com` | V3 | TODO — cc Carl Franzen, Michael Nuñez, Emilia David |
| 5 | **Synced / 机器之心 (EN)** | syncedreview.com | editorial form / Toronto office | V2 | TODO — no confirmed form URL |
| 6 | **量子位** | qbitai.com | `ai@qbitai.com` | V4 | TODO |
| 7 | **机器之心** | jiqizhixin.com | `editor@jiqizhixin.com`, `content@jiqizhixin.com` | V4 | TODO |
| 8 | **新智元** | aiera.com.cn | `aiera@aiera.com.cn` | V4 | TODO |
| 9 | **Analytics India Magazine** | analyticsindiamag.com/write-for-us/ | Form | V2 | TODO |
| 10 | **Towards AI** | contribute.towardsai.net | Form | V2 | TODO |
| 11 | **KDnuggets** | kdnuggets.com | `submissions@kdnuggets.com` | V2 | TODO — acceptance uncertain |
| 12 | **Latent Space (swyx)** | latent.space | Google Form in footer + warm intro | V2 | TODO — best fit, agent-eng beat |
| 13 | **Last Week in AI** | lastweekin.ai | `contact@lastweekinai.com` | V2 | TODO — podcast digest |
| 14 | **DeepAI** | deepai.org | `publish@deepai.org` | V2 | TODO |
| 15 | **Gradient Flow (Ben Lorica)** | gradientflow.com | LinkedIn / Substack DM | V2 | TODO |
| 16 | **Turing Post** | turingpost.com | LinkedIn DM Ksenia Se | V2 | TODO |
| 17 | **TechCrunch** | techcrunch.com/got-a-tip/ | `tips@techcrunch.com` | V3 | TODO — long shot |
| 18 | **Hacker News Show HN** | news.ycombinator.com | Self-post | (see hn-show-hn.md) | TODO — fire on launch day |
| 19 | **r/MachineLearning** | reddit.com/r/MachineLearning | Self-post tag `[R]` | (see reddit-posts.md) | TODO |
| 20 | **r/LocalLLaMA** | reddit.com/r/LocalLLaMA | Self-post | (see reddit-posts.md) | TODO |
| 21 | **PaperWeekly (微信)** | paperweekly.site | 官网投稿入口 | V4 | TODO |
| 22 | **@_akhaliq (X)** | x.com/_akhaliq | Reply to any paper-page tweet with our arXiv ID | V1 | TODO — curated by AK for HF Daily Papers |

### Passive (already indexed, no action needed)

- arxiv.org/abs/2604.08523 — live
- huggingface.co/papers/2604.08523 — live
- alphaXiv, Scholar Inbox, Elicit, ResearchRabbit — auto-pull from arXiv
- Emergent Mind — ingests arXiv + ranks by social signal
- Smol AI News — auto-aggregates X/Reddit/Discord
- StartupHub.ai — already picked us up

---

## Launch-day schedule (one coordinated window gives the biggest lift)

Best pattern: fire everything within a 2-hour window during US morning + CN evening overlap. That's typically 09:00-11:00 Pacific = 00:00-02:00 Beijing next day.

| T-slot | Action |
|---|---|
| T-0 | HN Show HN post (the single highest-variance lever) |
| T-0 | r/MachineLearning + r/LocalLLaMA posts |
| T-0 | X thread from first author, quote-retweeted from group accounts |
| T+15min | Email VentureBeat + TechCrunch tips lines |
| T+30min | Submit MarkTechPost, Unite.AI, Analytics India, Towards AI forms |
| T+1h | Email 机器之心 + 量子位 + 新智元 + PaperWeekly (Chinese prime time) |
| T+2h | LinkedIn post from author + co-authors |
| T+24h | Follow-up nudge to unresponsive editors (one round, polite) |

## Amplifier list (cold-reply in order)

X accounts that have amplified similar papers:

- @arankomatsuzaki — already tweeted ClawBench; thank + quote
- @_akhaliq — HF Daily Papers curator; reply to his paper-of-the-day tweet
- @_philschmid — HF, frequently boosts benchmarks
- @omarsar0 (Elvis Saravia) — agent / eval coverage
- @AravSrinivas (Perplexity CEO) — boosts browser-agent work
- @jerryjliu0 (LlamaIndex) — tool-use / agent boosts
- @swyx / @simonw — agent-eng
- @hardmaru — paper amplifier
- @sama — long shot, but "Sonnet beats GPT-5 on our benchmark" lands

---

## What to do *after* someone publishes

When a venue picks us up, within 24h:

1. Retweet / quote-tweet from the main author account
2. Link the published article back from a GitHub Discussion post (SEO backlink)
3. Add the venue to the "As seen in" badge row in the README (create one if not present)
4. Log it in `docs/outreach/executed.md` with the URL and date

## What NOT to do

- Don't post the exact same copy to every venue — Chinese platforms especially detect cross-posting as spam
- Don't cite "the best model is Claude Opus / 62%" — those numbers are stale, use 33.3% only
- Don't drop the PyPI install command as `pip install claw-bench` — that name is taken by a different project; always use `uv tool install clawbench-eval`
- Don't paste the .env file contents into any public post even accidentally
