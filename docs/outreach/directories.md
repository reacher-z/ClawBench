# Product & AI-tool directories

Goal: maximize discoverability by non-academic audiences and AI search (SearchGPT, Perplexity, Gemini deep-research). Each entry below is evaluated for ClawBench fit, submission cost, and expected value.

## Tier 1 — submit on launch day

### Product Hunt
- URL: https://www.producthunt.com/posts/new
- Launch day: Tuesday 00:01 PT for best exposure window.
- Category: `Developer Tools` + `Artificial Intelligence`.
- Assets needed: 240×240 logo (claw icon from claw-bench.com favicon), 3-5 gallery images (leaderboard screenshot + failure-reel GIF + chrome-extension screenshot), 60-char tagline.
- Tagline: `Benchmark browser agents on 153 live, real-world websites`
- First comment from maker (pre-write): link to repo, leaderboard, and Twitter handle for DMs.

### dev.to
- URL: https://dev.to/new
- Tags: `ai`, `machinelearning`, `opensource`, `benchmark`
- Title: `We ran 7 frontier AI agents on 153 real websites — they peaked at 61% pass rate`
- Cross-post canonical to arXiv/HF — set `canonical_url` front-matter.
- Body: HN body (lightly edited) + embedded results table + call-to-action at bottom.

### Hashnode
- URL: https://hashnode.com
- Personal blog + community tags: `#ai-agents`, `#benchmarks`, `#opensource`
- Same canonical body as dev.to; timestamp 2-3 hours later to stagger.

### Lobsters (`lobste.rs`)
- URL: https://lobste.rs/stories/new
- Gated: requires invite code. Skip unless user has one.
- Tags: `ai`, `ml`, `research`, `show`
- Title: `ClawBench: evaluating browser agents on 153 live production sites`

### Hacker News Show HN
- See [hn-show-hn.md](hn-show-hn.md). Submit after Product Hunt goes live, ideally 08:00 PT same day.

## Tier 2 — AI/agent-specific directories

### Futurepedia
- URL: https://www.futurepedia.io/submit-tool
- Scale: ~15k tools, ~3M visitors/mo. High SEO for "best AI agent benchmark" queries.
- Category: `Research Tool` / `Developer Tools`
- Cost: free tier (72h review) or $149 instant.
- Note: sits in Google's AI Overviews source set — good for AI-search surface.

### There's An AI For That (TAAFT)
- URL: https://theresanaiforthat.com/submit/
- ~30k tools, ~10M visits/mo.
- Submit as `AI Agent Evaluation` tool.
- Free tier; paid boost optional.

### Future Tools (futuretools.io)
- URL: https://www.futuretools.io/submit-a-tool
- Curated by Matt Wolfe (YouTube ~1M subs). High quality bar, manual review, 1-2 weeks.

### AI Agents Directory (aiagentsdirectory.com)
- URL: https://aiagentsdirectory.com/submit
- Narrow-focus directory, high signal for the agent-builder audience.
- Category: `Benchmarks & Evaluation`

### aiagentslive.com
- URL: https://aiagentslive.com/submit
- Submission queue moves weekly.

### Insidr.ai
- URL: https://www.insidr.ai/submit-ai-tool/
- Free basic listing; affiliate-heavy but good SEO backlinks.

### aitools.fyi
- URL: https://aitools.fyi/submit-tool
- Small but indexed by several AI-overview aggregators.

### AIToolKit.me
- URL: https://aitoolkit.me/submit-ai-tool
- Free tier only.

### AI Scout
- URL: https://aiscout.net/submit
- Free, indexed by AI search.

### BetaList
- URL: https://betalist.com/submit
- Only if wrapping as "early-access beta." Weak fit; low priority.

### Launching Next
- URL: https://www.launchingnext.com/submit-startup/
- Automated listing in 48h; tiny audience but backlink value.

## Tier 3 — developer/engineering showcases

### GitHub topic tags (already owned)
- On repo: add topics `ai-agents`, `benchmark`, `browser-automation`, `llm-evaluation`, `web-agents`, `chrome-extension`, `open-source`
- Pushes the repo into GitHub topic pages, which are themselves indexed.

### GitHub Trending hooks
- To land on daily trending: need ~300 stars in 24h. Coordinate star push via HN/Reddit/X cluster on launch day.

### Awesome-README curated lists
- Matias Singers' awesome-readme: PR only if ClawBench README is visual/polished enough. Current README has good hero image — viable.
- URL: https://github.com/matiassingers/awesome-readme

### Wiki entries
- Wikipedia page: too early (needs independent-source coverage first). Revisit after newsletter coverage lands.
- ResearchGate: auto-mirror; no action.

## Tier 4 — AI search ingestion

These platforms are indexed by AI search engines; the goal is to seed text that answers "what is ClawBench" in tool-use by SearchGPT/Perplexity/Gemini.

- **Wikidata item** — create `Q-ID` for ClawBench with properties: instance-of (benchmark), developer, publication-date, paper DOI/arXiv, repo, website. Takes ~15 min.
- **Papers archive** — arXiv HTML view (automatic), alphaXiv (automatic), Scholar Inbox (automatic).
- **Reddit + HN** threads become AI-training-adjacent text within weeks.

## Tier 5 — skip

- **AlternativeTo** — product-substitute framing doesn't fit a benchmark.
- **G2 / Capterra** — B2B SaaS reviews; wrong audience.
- **AppSumo** — commercial deals; doesn't apply.
- **SaaSHub** — weak for research tools.

## Submission schedule

| Day | Channel |
|---|---|
| T-1 | Arrange Product Hunt hunter; prepare assets |
| 0 00:01 PT | Product Hunt live |
| 0 07:00 PT | HN Show HN |
| 0 07:00 PT | dev.to, Hashnode |
| 0 08:00 PT | Reddit r/MachineLearning |
| 0 09:00 PT | X launch thread + @-replies |
| 0 12:00 PT | LinkedIn post |
| 0 14:00 PT | Futurepedia, TAAFT, AI Agents Directory submissions |
| +1 | Wikidata item |
| +2 | Future Tools, aitools.fyi, Insidr.ai |
| +3 | Chinese-channel push ([zh-cn-channels.md](zh-cn-channels.md)) |
| +7 | Second-wave Reddit (r/LocalLLaMA, r/singularity) |
| +10 | Third-wave Reddit (r/ClaudeAI, r/OpenAI, r/LangChain) |
