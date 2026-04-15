# Awesome-list PR targets

Ranked by (scope fit × maintainer activity × audience). Each is a single-entry PR adding ClawBench to the appropriate Benchmarks/Evaluation section. Disclosure of maintainer affiliation (reacher-z) in every PR.

## Tier 1 — execute first

| Repo | Stars | Last commit | Section | Notes |
|---|---|---|---|---|
| `steel-dev/awesome-web-agents` | ~1,383 | 2026-04-08 | Benchmarks & Research | Best fit — lists WebArena, Mind2Web, WebVoyager. Strict CONTRIBUTING: factual, disclose affiliation, one item per PR, title `Add: item-name`. |
| `ZJU-REAL/Awesome-GUI-Agents` | ~399 | 2026-04-15 | Datasets/Benchmarks (table) | Very active. Paper-list style with date prefix. |
| `ranpox/awesome-computer-use` | ~532 | 2025-11-07 | Papers → Evaluation | OSWorld/AndroidWorld peers. |
| `cdxeve/awesome-computer-use-agents` | ~10 | 2026-04-14 | Benchmarks | Small but fresh and benchmark-native. |
| `dataanswer/awesome-agent-benchmarks` | ~6 | 2026-03-26 | Datasets > GUI Agent (8-col table) | Schema-perfect. |
| `Jenqyang/Awesome-AI-Agents` | ~1,068 | 2026-04 | Benchmark/Evaluator | Star-badge format. |
| `kyrolabs/awesome-agents` | ~2,172 | 2026-04 | Testing and Evaluation | Bold-name bullet format. |
| `angrykoala/awesome-browser-automation` | ~600 | 2026-03-23 | Tools > AI | Adjacent to Browser-Use. |

## Tier 2 — execute second batch

| Repo | Stars | Last commit | Section | Notes |
|---|---|---|---|---|
| `onejune2018/Awesome-LLM-Eval` | ~631 | 2025-11 | Agent-Capabilities (table) | Lists WebArena-adjacent entries. |
| `BradyFU/Awesome-Multimodal-Large-Language-Models` | ~17,647 | 2026-04-09 | Benchmarks for Evaluation | 17K-star amplification. |
| `kaushikb11/awesome-llm-agents` | ~1,431 | 2026-04 | Would require a new Benchmarks subsection | Medium-effort. |
| `luo-junyu/Awesome-Agent-Papers` | ~2,619 | 2025-11 | Datasets & Benchmarks | Paper-year-venue format. |
| `Hannibal046/Awesome-LLM` | ~26,646 | 2025-07 | LLM Evaluation | Loose fit; highest reach if accepted. |
| `caramaschiHG/awesome-ai-agents-2026` | ~306 | 2026-04 | — | Low-gating, easy win. |
| `supernalintelligence/Awesome-Gui-Agents` | ~62 | 2025-08 | Resources | Borderline freshness. |

## Skip with reason

- `e2b-dev/awesome-ai-agents` (27k stars) — maintainer inactive >14 months
- `OSU-NLP-Group/GUI-Agents-Paper-List` — **already lists ClawBench** (line 131); no PR needed
- `Shubhamsaboo/awesome-llm-apps` (105k stars) — scope is apps/demos, not benchmarks
- `steven2358/awesome-generative-ai` — no benchmarks home
- `sindresorhus/awesome` — meta-index only
- `slavakurilyak/awesome-ai-agents`, `wgwang/awesome-LLM-benchmarks`, `junhua/awesome-llm-agents` — stale (>6 months)
- `showlab/Awesome-GUI-Agent` — moderately stale (8 months), include only if time permits

## Entry drafts (ready to paste per repo)

### steel-dev/awesome-web-agents
```md
- [ClawBench](https://github.com/reacher-z/ClawBench) - A benchmark of 153 everyday tasks across 144 live production websites in 15 categories, with a submission-interception layer that blocks only the final write request so agents are evaluated end-to-end on real sites without real-world side effects.
```

### ZJU-REAL/Awesome-GUI-Agents
Table row:
```md
| ClawBench: Can AI Agents Complete Everyday Online Tasks? (Apr. 2026) | figures/clawbench.jpg | [Github](https://github.com/reacher-z/ClawBench) <br> [Paper](https://huggingface.co/papers/2604.08523) |
```

### ranpox/awesome-computer-use (Evaluation subsection)
```md
- [ClawBench: Can AI Agents Complete Everyday Online Tasks?](https://huggingface.co/papers/2604.08523) - 153 everyday tasks on 144 live production sites (15 categories), with a submission-interception layer for safe real-website evaluation.
```

### cdxeve/awesome-computer-use-agents (benchmarks table)
```md
| **ClawBench** | Live production web browsing | 2026 | [Paper](https://huggingface.co/papers/2604.08523) · [GitHub](https://github.com/reacher-z/ClawBench) |
```

### dataanswer/awesome-agent-benchmarks (8-column table)
```md
| ClawBench | https://github.com/reacher-z/ClawBench | 2026 | Evaluates browser agents on everyday tasks across live production websites rather than sandboxes. | 153 tasks | Task Success Rate | Live-site evaluation | Web |
```

### Jenqyang/Awesome-AI-Agents
```md
- **ClawBench** [[GitHub](https://github.com/reacher-z/ClawBench)] - Benchmark of 153 everyday tasks on 144 live production websites across 15 categories, targeting real-world browser-agent evaluation rather than sandboxed replicas.
```

### kyrolabs/awesome-agents
```md
- **[ClawBench](https://github.com/reacher-z/ClawBench)**: Live-web benchmark of 153 everyday tasks across 144 production sites in 15 categories, measuring browser agents against unsimulated real-world conditions.
```

### angrykoala/awesome-browser-automation (Tools > AI)
```md
- [ClawBench](https://github.com/reacher-z/ClawBench) - Benchmark of 153 everyday tasks on live production websites for evaluating AI browser agents beyond sandboxed environments.
```

### onejune2018/Awesome-LLM-Eval (Agent-Capabilities table)
```md
| ClawBench | reacher-z | [ClawBench](https://github.com/reacher-z/ClawBench) | 153 everyday tasks on 144 live production websites across 15 categories; submission-interception layer enables safe evaluation; best model ~62% (2026-04) |
```

### BradyFU/Awesome-Multimodal-Large-Language-Models
```md
| ClawBench: Can AI Agents Complete Everyday Online Tasks? | arXiv 2026 | 2026-04 | [GitHub](https://github.com/reacher-z/ClawBench) | [Paper](https://huggingface.co/papers/2604.08523) |
```

### luo-junyu/Awesome-Agent-Papers
```md
**[ClawBench: Can AI Agents Complete Everyday Online Tasks?](https://huggingface.co/papers/2604.08523)** (*2026*) > 153 everyday tasks across 144 production websites in 15 categories; submission-interception layer for safe live-site evaluation.
```

### Hannibal046/Awesome-LLM (LLM Evaluation)
```md
- [ClawBench](https://github.com/reacher-z/ClawBench) - Browser-agent benchmark of 153 everyday web tasks on 144 live production sites; submission-interception layer for safe real-site evaluation.
```
