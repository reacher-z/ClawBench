# Hacker News — Show HN

## Title options

1. `ClawBench: 153 live-web tasks where the best agent still fails 4 in 10`
2. `We ran 7 frontier agents on 153 real websites. Best one passes 61%`
3. `ClawBench: benchmark for web agents that runs on real sites without side effects`

**Recommended:** Option 2. States the number, states the delta, doesn't oversell.

## Submission time

Tuesday or Wednesday, 07:30–08:30am PT (peak HN front-page window).

## Body (~250 words)

Show HN: ClawBench, a benchmark of 153 everyday web tasks on 144 live production sites. We ran 7 frontier agents on it. The best one (Claude Opus 4.6) passes 61.4%. Everyone else is in the 17 to 56 range, and several sub-10.

Tasks are the things people actually do online: order Pad Thai on Uber Eats, book a pet sitter on Rover, apply to a job on Greenhouse, schedule a dentist, file an RMA, reserve an OpenTable slot. 15 categories. The sites are the real sites, not mirrors. To keep agents off anyone's credit card, we wrote a CDP-level interceptor that sits in front of Chromium and captures the final write request (checkout POST, form submit, email send) right before it hits the wire. The agent gets all the way to the "Place Order" tap; the tap just never lands. Everything before that is real: real search, real login, real cart, real captchas.

Some failure patterns we kept seeing:

- Agents add two Pad Thais because the "+" button lives inside the quantity stepper and they can't tell it already defaulted to 1.
- Job-application uploads succeed but the resume goes into the cover-letter field.
- Travel bookings pick the right dates in the date picker, then submit the default dates that were there before.

Install: `pip install claw-bench`.
Paper: https://huggingface.co/papers/2604.08523
Repo: https://github.com/reacher-z/ClawBench

Happy to answer questions. If you want your model on the leaderboard, open a PR with a results CSV and we'll verify.

## Pre-drafted first-hour replies

### "How is this different from WebArena?"

WebArena runs on self-hosted clones of OneStopShop, GitLab, Reddit, etc. Great for reproducibility, but the sites don't have the anti-bot stack, the A/B-tested checkout funnels, or the 2026 DOM that real sites have. ClawBench runs on the live production sites. The cost is that we had to build an interception layer so nothing actually gets charged or sent. The benefit is that when GPT-5.4 fails on DoorDash, it fails on the DoorDash you use tonight.

### "Why 153?"

No deep reason. We built the list category-by-category from "things our friends did online last week" and stopped when we had good coverage across 15 life categories and every task had a working human reference run. 153 is where that landed. There's also a curated 20-task Lite subset (`test-cases/lite.json`) if you want a cheaper signal.

### "Can I add my model?"

Yes. Models are defined in `models/models.yaml` with a small adapter. If your model speaks OpenAI-compatible chat or Anthropic Messages, it's a 20-line config. Open a PR with the adapter plus a results CSV from a full run and we'll verify on our side before merging to the leaderboard. Happy to help you wire it up in issues.

### "What about CAPTCHAs?"

They happen and they count. If the agent can't solve a Cloudflare challenge, it fails the task, same as a human who gave up. We don't pre-solve, don't whitelist, don't feed cookies. A few sites (maybe 6 or 7 out of 144) hit hCaptcha aggressively enough that no current agent gets past them; those tasks are 0% across the board and we flag them in the per-site breakdown.

### "Isn't this just OSWorld?"

OSWorld is desktop-scoped: the agent controls a whole VM, opens Photoshop, edits an xlsx, uses the file manager. ClawBench is browser-only. No desktop apps, no shell beyond read-only `ls`/`cat`/`grep` on the dummy user's profile directory. Different surface. You'd pick OSWorld if you care about a model that can operate Linux; you'd pick ClawBench if you care about a model that can actually book the flight.

### "How does the interception work?"

Chromium runs in a Docker container with remote debugging on. We attach via CDP's `Fetch` domain and register a request-paused handler. Each test case ships an `eval_schema` with a `url_pattern` regex plus HTTP method (and optional body/params). When a request matches, we snapshot it to `interception.json`, kill the agent process, and stop recording. Everything before that request goes through normally, so the agent sees real server responses the whole way. For tasks behind a payment wall where we can't know the exact final URL, the pattern is a sentinel that never matches and the run times out; those tasks are judged entirely by the post-session agentic evaluator against a human reference trajectory.
