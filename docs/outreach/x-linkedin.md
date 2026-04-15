# X (Twitter) + LinkedIn

All char counts under 280. No emojis. No engagement bait.

## Thread A — Failure-reel hook (general audience)

**1/7**
We recorded 7 frontier AI agents doing 153 everyday tasks on real websites. The results are a comedy special. A thread of the funniest failures, followed by the leaderboard.

**2/7**
Uber Eats task: order a burrito. The agent hit a claw-machine style CAPTCHA, spent 14 turns trying to "grab the plushie," declared victory, and submitted an empty cart. Billed nothing. Ordered nothing. Claimed success.

**3/7**
Calendly task: book a meeting for next Tuesday. Agent booked it for Tuesday 2019. User would need a time machine to attend. Agent reported the slot as confirmed.

**4/7**
Indeed task: apply to 3 software jobs. Perimeter X bot-check intercepted on page 1. Agent spent 40 turns re-clicking the same "I am human" button, then wrote a cover letter addressed to the CAPTCHA.

**5/7**
Gmail task: email the recruiter. Agent composed a perfect message, forgot to fill the To: field, and sent it into the void. Logged the blank send as a completed task.

**6/7**
Across 144 live production sites and 1,071 runs, the best frontier model passed 33.3%. Most models landed under 40%. WebArena scores do not survive contact with real CAPTCHAs, real cookies, real date pickers.

**7/7**
ClawBench is live. Paper: huggingface.co/papers/2604.08523. Code + harness: github.com/reacher-z/ClawBench. Leaderboard + recorded rollouts: claw-bench.com. Run your own agent in one command.

## Thread B — Researcher hook (ML Twitter)

**1/5**
New benchmark: ClawBench. 153 everyday tasks on 144 live production websites, evaluated on 7 frontier agents. Designed to measure what WebArena cannot: the long tail of real-site quirks. Headline result: best agent 33.3%, most under 40%.

**2/5**
Methodology: interception-layer design. Agents drive real sites up to the final submit (checkout, send, book), which we block and verify server-side. No mocks, no replays, no synthetic DOMs. The agent sees production HTML, production anti-bot, production latency.

**3/5**
The regression this exposes: frontier agents that post strong WebArena numbers collapse on site-specific friction. Claw-machine CAPTCHAs, Perimeter X challenges, ambiguous date pickers, cookie walls. Capability on clean tasks does not transfer.

**4/5**
We release 1,071 recorded rollouts (video + action trace per run), the full task suite, the grading harness, and a reproducible install. Failure modes are inspectable frame-by-frame, which is the part we found most useful for model debugging.

**5/5**
Paper: huggingface.co/papers/2604.08523. Repo: github.com/reacher-z/ClawBench. Leaderboard and rollouts: claw-bench.com. Submissions open.

## Reply / Quote-Tweet scripts

### 1. For @_akhaliq daily papers roundups
ClawBench is live on HF Papers — 153 everyday web tasks across 7 frontier models. Live leaderboard: claw-bench.com. HF Space demo: <URL>. Paper: hf.co/papers/2604.08523

### 2. For @GoogleAI / @OpenAI agent announcements
Congrats on the release. If you want an external signal on real-site behavior, ClawBench has 144 live production sites and video rollouts per run. Happy to add your model to the leaderboard: claw-bench.com.

### 3. For WebArena / VisualWebArena discussion threads
WebArena is the right abstraction for controlled eval. ClawBench is the complement: same task shape, run against live production sites with real anti-bot and real date pickers. The gap between the two is informative.

### 4. For "AI agents are almost there" takes
The best frontier agent we measured on 153 everyday tasks passes 33.3%. The failure reel on claw-bench.com is the clearest answer to how close "almost there" actually is.

### 5. For browser-use / Playwright agent posts
Nice work. If you want a standardized harness to score it, ClawBench ships a one-command runner against 144 live sites with server-side grading. github.com/reacher-z/ClawBench.

## LinkedIn post (~180 words)

Announcing ClawBench, a new benchmark for AI browser agents operating on live production websites.

ClawBench covers 153 everyday tasks across 144 real sites, including Uber Eats, Calendly, Indeed, and Gmail. Unlike sandboxed web benchmarks, agents drive the actual production stack, with real anti-bot systems, real cookie walls, and real latency. Grading uses an interception layer: the agent performs the task end-to-end, and we block the final submission to verify intent server-side. Nothing is mocked.

We evaluated 7 frontier models across 1,071 runs. The strongest agent (Claude Sonnet 4.6) passes roughly 33.3% of tasks, and most models land under 40%. Models that score strongly on WebArena regress sharply on site-specific friction such as CAPTCHAs, ambiguous date pickers, and form-validation quirks, suggesting current agent capability does not transfer cleanly from clean environments to production ones.

The release includes the full task suite, grading harness, and recorded video rollouts for every run, which we have found particularly useful for debugging failure modes.

Paper: huggingface.co/papers/2604.08523
Repository: github.com/reacher-z/ClawBench
Leaderboard and rollouts: claw-bench.com

Submissions are open. Feedback welcome.
