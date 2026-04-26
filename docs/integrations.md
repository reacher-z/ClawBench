# Integrations

Supported pairings between ClawBench tasks and external browser-agent tools.

## Claude for Chrome (Anthropic, beta)

[Claude for Chrome](https://claude.com/claude-for-chrome) is Anthropic's Chrome
extension that lets Claude navigate tabs, click, and fill forms directly in
the user's browser. It is not a ClawBench harness in the automated sense —
the extension runs in the user's local Chrome rather than inside our
container — but it pairs cleanly with ClawBench task specs for a
manual-but-realistic evaluation flow.

### Try a ClawBench task with Claude for Chrome

1. Install the extension from the Chrome Web Store (link on
   [claude.com/claude-for-chrome](https://claude.com/claude-for-chrome)).
2. Pick a task. The bundled suite is listed by `clawbench cases`; each case
   directory holds a `task.json` with the starting URL and the natural-language
   `instruction` the agent is expected to complete.
3. Open the starting URL in the Chrome window where Claude for Chrome is
   active. Paste the `instruction` into the Claude side-panel and let it
   drive.
4. When Claude reaches the final submit step, copy the outbound request from
   Chrome DevTools → Network (or let it actually go through — ClawBench's
   submission-interceptor only runs inside our container, so live runs in
   your own browser will hit the real site).
5. Score yourself against the per-task rubric in
   [`eval/agentic_eval.md`](../eval/agentic_eval.md), or run the full judge
   pipeline on a recording by hand.

### What this flow is good for

- Sanity-checking task reachability from an end-user perspective.
- Generating additional human or agent reference runs without our container.
- Comparing Anthropic's first-party browser agent against the harnesses we
  already ship (`openclaw`, `opencode`, `claude-code`, `codex`,
  `browser-use`, `claw-code`, and `hermes`).

### What it is *not*

- Not an automated leaderboard submission — scoring still requires the
  full five-layer recording that our container produces (video + screenshots
  + HTTP + browser actions + agent messages).
- Not a safe way to run write-heavy tasks (checkout, job applications,
  bookings) on your personal accounts. For the interception layer, run the
  same task inside ClawBench's container with `clawbench run <case> --human`
  instead.

### Roadmap

A first-class `--harness claude-for-chrome` entry is tracked as an open
question: it requires either (a) Anthropic exposing a programmatic hook so
the extension can drive a remote Chrome over CDP, or (b) running the
extension itself inside our container image. Contributions welcome — open
an issue tagged `harness:claude-for-chrome` if you want to help scope it.
