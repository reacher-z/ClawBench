# Evaluation

ClawBench separates **safety** from **success**:

- The **request interceptor** blocks irreversible HTTP requests (see [`request_interceptor.md`](request_interceptor.md)). It does NOT judge whether the agent did the task correctly.
- **PASS/FAIL** is determined **post-hoc** by reviewing the run artifacts with an agentic evaluator prompt.

This split matters because an interceptor hit alone is not success. An agent can trigger the interceptor while filling a form wrong, or it can legitimately complete a payment-walled task that never triggers the interceptor. The artifacts — action log, HTTP log, agent messages, screenshots, and the MP4 — together describe what happened, and an evaluator decides whether that constitutes success.

## The agentic evaluator

The evaluator is a Claude Code subagent driven by the prompt in [`../prompts/agentic_eval.md`](../prompts/agentic_eval.md). Point it at a single run directory (`test-output/<model>/<case>-.../`) and it reviews the evidence to emit PASS or FAIL with a short rationale.

## Evaluation criteria (summary)

The full criteria live in [`../prompts/agentic_eval.md`](../prompts/agentic_eval.md). The essentials:

- **Completed the task → PASS**, otherwise FAIL.
- **Must use the disposable email** from `/my-info/email_credentials.json` when the task requires an email or verification code. Skipping it is FAIL.
- **Must attempt to use payment info** from the user profile for purchases. The card will decline — that's fine — but the agent must *click the button*. Failing to attempt is FAIL.
- **Must attempt to fill out checkout forms and click checkout** when asked to "proceed to checkout". Omitting that step is FAIL.
- **Interceptor hit counts as success** as long as all prior inputs were correct and the blocked request was the intended terminal action.
- **Phone-verification wall:** if the agent completes every step up to and including the phone-number prompt but can't solve the SMS challenge, PASS. The phone wall is an external blocker, not an agent failure.
- **CAPTCHAs:** the agent should attempt to solve them. If it can't, FAIL — we treat anti-bot challenges as part of the real-world difficulty.
- **No success page due to interception** is OK: the agent can still be PASS if prior actions were correct.

## Running the evaluation

The agentic evaluator is designed for use with Claude Code (or a similar interactive agent). A typical flow:

1. Pick a run directory: `test-output/qwen3.5-397b-a17b/001-daily-life-food-uber-eats-qwen3.5-397b-a17b-20260411-120000/`
2. Feed [`../prompts/agentic_eval.md`](../prompts/agentic_eval.md) to the evaluator subagent along with a pointer to that directory.
3. The evaluator reads `run-meta.json`, `data/actions.jsonl`, `data/requests.jsonl`, `data/agent-messages.jsonl`, `data/interception.json`, and spot-checks `data/screenshots/` and `data/recording.mp4`.
4. The evaluator emits PASS or FAIL with rationale.

An automated end-to-end evaluation harness (running the evaluator over an entire batch directory and emitting a summary CSV) is out of scope for this repository — build one in your own tooling if you need it.

## What each artifact tells the evaluator

| Artifact                | What the evaluator uses it for                                         |
| ----------------------- | ---------------------------------------------------------------------- |
| `run-meta.json`         | Quick context: model, duration, whether the interceptor fired          |
| `data/actions.jsonl`    | Did the agent actually interact with the page? Empty = idle failure    |
| `data/requests.jsonl`   | What HTTP requests did the browser make? The terminal action should be visible here (even if blocked) |
| `data/agent-messages.jsonl` | Agent reasoning: did it understand the task? Did it plan sensibly? |
| `data/interception.json`| Whether the interceptor blocked a request, and which one               |
| `data/screenshots/`     | Visual sanity checks on form fields, errors, confirmation pages        |
| `data/recording.mp4`    | Full ground truth — watch the session end-to-end when unsure           |

## Related reading

- [`../prompts/agentic_eval.md`](../prompts/agentic_eval.md) — the authoritative evaluator prompt (11 rules)
- [`request_interceptor.md`](request_interceptor.md) — why interceptor ≠ judge
- [`data_format.md`](data_format.md) — the shape of each artifact
