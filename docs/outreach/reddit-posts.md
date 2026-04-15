# Reddit — per-subreddit customized posts

**Important:** do NOT crosspost. Submit natively to each sub. Reddit anti-self-promo heuristic kicks in if >10% of recent posts link to the same domain — space submissions 7–10 days apart, comment organically in each sub first.

## 1. r/MachineLearning — highest bar, set citation anchor here

**Title:** `[R] ClawBench: 153 everyday web tasks across 144 live production sites — frontier agents cap at 33.3%`

**Body:**

We release ClawBench, a benchmark for browser-using agents evaluated on live production websites rather than sandboxed replicas or static DOM snapshots.

**Setup.** 153 tasks (booking, form-filling, search-and-extract, multi-step checkout flows) across 144 distinct live sites, evaluated on 7 frontier models. Tasks are graded by a deterministic interception layer that sits between the agent and the site: it records structured side-effects (API calls, form submissions, state deltas) rather than scraping the final DOM. This sidesteps the usual LLM-judge-on-screenshots failure mode and yields reproducible pass/fail signals even when a site re-skins its UI.

**Results (pass@1, n=153):** the top frontier model passes 33.3% of tasks, and most of the 7 evaluated models land under 40%. Full per-model table is on the leaderboard (link in first comment).

**Failure breakdown (aggregated, top-model):**

| Category                     | Share of failures |
|------------------------------|-------------------|
| Multi-step state tracking    | 31%               |
| Authentication / CAPTCHA     | 22%               |
| Dynamic content / late DOM   | 18%               |
| Tool-call schema drift       | 14%               |
| Premature termination        | 9%                |
| Other                        | 6%                |

The interception-layer grader is, to our knowledge, the first grading approach that is invariant to site cosmetic changes while remaining fully deterministic. We discuss the tradeoff against end-state DOM grading in Section 4.

Paper and repo in comment (sub rules).

**First pinned self-comment:**
> Paper: https://huggingface.co/papers/2604.08523
> Repo: https://github.com/reacher-z/ClawBench
> Happy to discuss the grader design — the choice to grade on intercepted side-effects vs terminal DOM is the main methodological contribution and I expect it to be the most contested part.

**Time:** Tue/Wed 08:00–10:00 PT. **Flair:** [R]. **Risk:** account needs 50+ karma or post held for manual review.

---

## 2. r/LocalLLaMA

**Title:** `I ran 7 frontier models on 153 real web tasks (live sites, not sandboxes). Nobody cracks 33.3%.`

Spent the last couple of months building a harness that runs browser agents against 144 live production sites (Amazon, DoorDash, airline sites, government portals, the usual mess). 153 tasks total, 7 frontier models, graded deterministically by intercepting the network layer instead of screenshotting.

Pass@1 headline: the top frontier model caps at 33.3%, and most models land under 40%. Full per-model numbers are on the leaderboard.

The one open-weights model in this cut lands squarely in the mid-pack — roughly on par with the smaller closed models, still meaningfully behind the frontier. A year ago the gap on comparable web tasks was much wider, so it's narrowing, but "run your web agent on a 3090" is not yet a sensible sentence.

What actually kills open models on these tasks isn't reasoning — it's tool-call schema drift and premature termination. Qwen/DeepSeek finetunes trained specifically on browser-tool traces would probably close most of the remaining gap.

Repo has the harness and per-task traces if anyone wants to run their own local model through it:
https://github.com/reacher-z/ClawBench
https://huggingface.co/papers/2604.08523

**Time:** Tue–Thu 09:00–11:00 PT. **Risk:** low; expect pushback demanding Qwen3/DeepSeek/Llama — pre-empt in comments.

---

## 3. r/LangChain

**Title:** `ClawBench — 153 live-site browser tasks, LangChain-compatible harness`

Built a benchmark for browser agents that runs against 144 real production sites rather than replicas. The harness exposes agents through a standard tool interface, so dropping in a LangChain `AgentExecutor` or LangGraph node takes about 20 lines — there's an example in `examples/langchain_agent.py`.

Grading happens at a network interception layer (not DOM scraping, not LLM-judge), so your agent gets the same pass/fail signal regardless of whether the site redesigns mid-run.

Frontier results: the best of the 7 models we ran tops out at 33.3%, and most land under 40%. Most failures are multi-step state tracking and tool-call schema drift — both things LangGraph's checkpointer and structured-output coercion help with, so there's room for harness-side wins without changing the model.

Repo: https://github.com/reacher-z/ClawBench
Paper: https://huggingface.co/papers/2604.08523

PRs welcome for additional harness adapters.

**Time:** Wed 10:00 PT. **Risk:** low; verify `examples/langchain_agent.py` exists before posting.

---

## 4. r/AIAgents

**Title:** `ClawBench: benchmark your agent on 153 live websites, add your model with a YAML file`

If you're building a browser agent and want a non-toy benchmark, ClawBench runs 153 everyday tasks across 144 live production sites — shopping, booking, forms, multi-step flows. Real sites, real CAPTCHAs, real state.

How to use it:

1. Clone the repo, `uv sync`.
2. Drop a model config in `configs/models/` (YAML — endpoint, auth, tool schema).
3. `clawbench run --model yourmodel` runs the full suite in roughly 4–6 hours depending on parallelism.
4. Results drop into a shared leaderboard if you opt in, or stay local if you don't.

Grading is deterministic (network-level interception), so you get the same score today and next month even if the site changes its UI.

Current leaderboard covers 7 frontier models. Top score is 33.3%, and most land under 40% — a useful reality check if you've been reading WebArena numbers and assuming the problem is solved.

Repo: https://github.com/reacher-z/ClawBench
Paper: https://huggingface.co/papers/2604.08523

**Time:** Tue 09:00 PT. **Risk:** low.

---

## 5. r/ClaudeAI

**Title:** `Claude Sonnet 4.6 tops ClawBench at 33.3% (153 live web tasks, 7 frontier models)`

Ran all three current Claude models plus GPT-5 and a few others on ClawBench, a benchmark of 153 tasks on 144 real production websites. 7 frontier models total.

Headline: Sonnet 4.6 is the top model at 33.3%. Most of the 7 models we ran land under 40% — nobody cracks the threshold. Full per-model table is on the leaderboard.

Sonnet being above the rest of the Claude family (and above the other frontier models we ran) is consistent with the pattern where Sonnet holds long tool-call chains better before drifting. Most failures across the board come down to multi-step state tracking and tool-call schema drift rather than raw reasoning — premature termination in particular hits smaller models harder.

https://github.com/reacher-z/ClawBench
https://huggingface.co/papers/2604.08523

**Time:** Wed 09:00 PT. **Risk:** moderate — lead with number, not announcement. Do not title "I built X".

---

## 6. r/OpenAI

**Title:** `ClawBench — 153 real-world web tasks on live sites, 7 frontier models, nobody clears 33.3%`

New benchmark results: ClawBench runs agents against 153 everyday tasks on 144 live production websites (not sandboxed copies), evaluated on 7 frontier models.

Headline pass@1: the top model tops out at 33.3%, and most of the 7 land under 40%. GPT-5 and GPT-5-mini both sit in the middle of the pack — GPT-5 is competitive with the leaders on authentication-flow tasks and late-DOM dynamic content (likely from stronger vision grounding on post-load rendered pages), while GPT-5-mini is the real story for people building cost-constrained agents: within striking distance of GPT-5 at roughly a tenth of the price per task.

Full per-model leaderboard is on the repo. Grading is deterministic via network interception, so these numbers are reproducible.

https://github.com/reacher-z/ClawBench
https://huggingface.co/papers/2604.08523

**Time:** Tue 08:00 PT. **Risk:** moderate — account needs >100 karma.

---

## 7. r/singularity

**Title:** `Even frontier models fail 2 in 3 real web tasks. New benchmark on 144 live production sites.`

ClawBench: 153 everyday tasks (booking flights, filling forms, checking out on real storefronts) across 144 live production websites, evaluated on 7 frontier models. Deterministic grading via network interception, not screenshots.

The best model on the planet right now scores 33.3%. Most of the 7 we ran land under 40%. Full per-model numbers are on the leaderboard.

So: the models that supposedly do PhD-level reasoning cannot reliably book a dentist appointment. Most failures are boring — multi-step state tracking, tool-call schema drift, premature termination. The interesting implication is that scaling raw capability is not the bottleneck; harness and memory are.

Useful reality check next time someone tells you agents will replace knowledge work by next quarter.

Repo: https://github.com/reacher-z/ClawBench
Paper: https://huggingface.co/papers/2604.08523

**Time:** Sun 18:00 or Mon 08:00 PT. **Risk:** low; sub rewards provocative framing.

---

## Other subs with simpler handling

- **r/programming**: weekly Show-off thread only; link to blog-post form of the HN body. Tue–Thu 06:00–08:00 PT.
- **r/webdev**: post in Showoff Saturday thread, 07:00–10:00 PT Saturday.
- **r/huggingface**: small (~15k) but focused — paste HN body, Tue–Thu 07:00 PT.
- **r/compsci**: academic framing only, keep r/ML version's abstract-first structure.
- **r/AI_Agents**: same as r/AIAgents above.
- **r/ArtificialInteligence** (misspelled, 1.3M): DM mods first before posting.

## Submission order

1. r/MachineLearning (sets citation anchor)
2. r/LocalLLaMA (volume)
3. r/singularity (volume + discussion)
4. r/ClaudeAI / r/OpenAI / r/AIAgents / r/LangChain (targeted)

Space out 7–10 days between submissions.
