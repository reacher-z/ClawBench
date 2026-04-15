# Newsletter pitches

Send 3–5 days before launch. Verified channels first; unverified flagged so you can confirm before sending.

Shared fact pack:
- 153 everyday web tasks on 144 live production sites, 15 categories
- Best frontier model ~62% pass; several under 40%
- Key design: submission-interception layer blocks only the final write request
- Paper: https://huggingface.co/papers/2604.08523
- Repo: https://github.com/reacher-z/ClawBench
- Project: https://claw-bench.com

## Verification status

| Newsletter | Channel | Status |
|---|---|---|
| Import AI | `jack@jack-clark.net` | VERIFIED |
| Last Week in AI | `contact@lastweekin.ai`, `andreyvkurenkov@gmail.com` | VERIFIED |
| The Rundown AI | `support@therundown.ai` | Partially verified |
| AlphaSignal | `lior@alphasignal.ai` | VERIFIED |
| TLDR AI | reply-to of current issue / `dan@tldrnewsletter.com` | UNVERIFIED — verify via reply-to header |
| Ben's Bites | @bensbites DM on X | UNVERIFIED — no public submit page |
| The Neuron | @theneurondaily DM | UNVERIFIED |
| AI Breakfast | @AiBreakfast DM | UNVERIFIED |
| Etude AI | internal editorial channel | UNVERIFIED which entity |

## 1. TLDR AI

**Subject:** New benchmark: frontier agents top out at 62% on everyday web tasks

Hi Dan,

Quick one for TLDR AI. We released ClawBench, a benchmark of 153 real web tasks (checkouts, bookings, form submissions) run on live sites. The best frontier model passes 62%; several major ones score under 40%.

The interesting engineering bit: a submission-interception layer blocks only the final write request, so agents execute the full flow end-to-end without ever creating real orders, tickets, or accounts. No sandboxed mirror sites.

- Paper: https://huggingface.co/papers/2604.08523
- Repo: https://github.com/reacher-z/ClawBench
- Site: https://claw-bench.com

Happy to send a per-model breakdown table, or an embargoed figure if useful.

Thanks,
[Name]

## 2. Ben's Bites

**Subject:** Benchmark for agents that actually use the real internet

Hey Ben,

If you're covering browser agents this week — we just dropped ClawBench. 153 everyday tasks (buy this, book that, submit this form) on 144 live sites. Top frontier model: 62%. Plenty of big names under 40%.

The useful-today angle: we built a submission-interception layer that lets agents run the whole flow on the real site but blocks the final write. So you can actually test agents on Amazon, DoorDash, StubHub without a graveyard of accidental orders.

- Demo and leaderboard: https://claw-bench.com
- Repo: https://github.com/reacher-z/ClawBench

Worth a bite? Happy to send you a short GIF of an agent failing hilariously on a Shopify checkout.

## 3. The Rundown AI

**Subject:** Frontier agents hit 62% on real-world web tasks — builders can ship this today

For founders shipping agent products: ClawBench just benchmarked the frontier on 153 real consumer web tasks and the ceiling is 62%. Below 40% for several well-known models. That's the live gap every agent startup is selling into.

What makes it builder-useful: a submission-interception layer blocks only the final write call, so your agent runs the full real-world flow (Amazon, Uber, Airbnb, DMV forms) without side effects. You can wire this into your own eval loop tomorrow.

- Leaderboard + videos: https://claw-bench.com
- Paper: https://huggingface.co/papers/2604.08523
- Repo (MIT): https://github.com/reacher-z/ClawBench

Happy to share the per-category failure modes.

## 4. Import AI — Jack Clark (VERIFIED)

**Subject:** ClawBench — measuring AI agent capability on the live consumer web

Hi Jack,

Thought this fit Import AI's recurring thread on agent capability evaluation. ClawBench is a 153-task benchmark that runs agents on the actual live consumer web — 144 real sites across 15 categories — rather than sandboxed mirrors. Best frontier model: 62% pass. Several major models below 40%.

The methodological contribution worth flagging: a submission-interception layer intercepts only the terminal write request. The agent traverses real login, state, and UI surfaces, but no real order, booking, or account is created. This sidesteps the usual tradeoff between realism and ethics in web-agent eval.

Policy-adjacent implication: the gap between demo videos and live-site competence is now quantifiable and reproducible.

- Paper: https://huggingface.co/papers/2604.08523
- Code + data: https://github.com/reacher-z/ClawBench

Happy to brief, or share task category breakdowns.

Best,
[Name]

## 5. The Neuron

**Subject:** We made AI agents shop, book, and fail on real websites. They failed a lot.

Fun one for you: we built ClawBench — a benchmark that sends AI agents to do 153 very normal things on real websites (buy socks, book a haircut, apply for a job). The best frontier model got a 62%. Some big names couldn't crack 40%. A D minus in internet.

To avoid accidentally ordering 400 pairs of socks during testing, we built a layer that lets the agent do everything right up to the final "Submit" click, then quietly intercepts it. The agent thinks it won. The internet is unharmed.

- Leaderboard, GIFs, failure reels: https://claw-bench.com
- Repo: https://github.com/reacher-z/ClawBench

Happy to send you the funniest failure clips for the newsletter.

## 6. Last Week in AI (VERIFIED)

**Subject:** New benchmark paper: live-web agent evaluation, 62% ceiling

Hi Andrey and team,

Submitting for potential coverage. ClawBench (arXiv 2604.08523) evaluates browser agents on 153 everyday tasks across 144 live consumer websites. Headline numbers: 62% for the strongest frontier model; several models below 40%.

Two points likely relevant to your academic-leaning readership:

1. The evaluation runs on live production websites rather than static mirrors, via a submission-interception layer that blocks only the final write request — preserving realism without side effects.
2. Task distribution covers 15 categories (commerce, government, healthcare, transit) designed to stress-test generalization beyond the typical WebArena / Mind2Web setups.

- Paper: https://huggingface.co/papers/2604.08523
- Repo and data: https://github.com/reacher-z/ClawBench
- Project: https://claw-bench.com

Happy to answer questions on methodology or share the full results CSV.

## 7. AI Breakfast

**Subject:** ClawBench: 153 web tasks, 62% frontier ceiling

Quick tip for AI Breakfast.

ClawBench — new benchmark for browser agents on the live consumer web. 153 tasks, 144 real sites, 15 categories. Best frontier model passes 62%; several under 40%. A submission-interception layer blocks only the final write request, so agents run end-to-end on real sites without side effects.

- Paper: https://huggingface.co/papers/2604.08523
- Repo: https://github.com/reacher-z/ClawBench
- Project: https://claw-bench.com

Happy to send a one-line-per-model results snippet formatted for the newsletter.

## 8. Etude AI (internal blog post — author affiliation)

Framing for an internal post (longer form than a cold pitch):

Open with the motivation — demo videos make agent progress look finished; live-site evaluation tells a different story. Introduce ClawBench — 153 tasks, 144 real sites, 15 categories — and state the top line: 62% for the best frontier model, several majors under 40%.

Middle: the submission-interception layer. Why we wanted real websites over mirrors; the engineering of intercepting only the final write request; how it preserves full-fidelity agent traces (auth, state, UI drift) without creating real orders, accounts, or bookings. Show one or two failure traces.

Close: paper, code, leaderboard, invitation for the Etude AI community to submit models, roadmap for task expansion.

## 9. Generic tip email (≤120 words, re-usable)

**Subject:** Tip: ClawBench — frontier agents cap at 62% on live-web tasks

Hi,

Quick tip in case it fits your coverage. We released ClawBench, a benchmark of 153 everyday tasks run on 144 live consumer websites (checkouts, bookings, forms). Best frontier model: 62% pass. Several major models under 40%.

The technical twist: a submission-interception layer blocks only the final write request, so agents run end-to-end on real sites without side effects.

Paper: https://huggingface.co/papers/2604.08523 · Repo: https://github.com/reacher-z/ClawBench

Happy to offer you one of the following as an exclusive: (1) full per-model results CSV before public release, (2) a 20-minute author interview, or (3) a 48-hour embargo on any follow-up result.

Thanks,
[Name]
