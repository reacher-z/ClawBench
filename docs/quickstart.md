# Quickstart

**Goal:** go from a freshly cloned repo to a recorded agent run in under 5 minutes.

This walkthrough assumes you have already completed [`installation.md`](installation.md) through step 8 (container built, `.env` filled, one model configured in `models/models.yaml`).

## 1. Pick a low-risk test case

`001-daily-life-food-uber-eats` is a good first run:

- It's the lowest-numbered case.
- It sits behind a natural payment wall, so the eval interceptor uses the `__PLACEHOLDER_WILL_NOT_MATCH__` pattern — nothing will be blocked, the session simply runs until the agent stops or the time limit expires.
- No irreversible consequences.

## 2. Launch the run

```bash
./run.sh
```

In the TUI:

1. Pick **Single run**.
2. Pick your model (e.g. `qwen3.5-397b-a17b`).
3. Pick test case `001` (you can type the numeric prefix).
4. Confirm.

Or equivalently, from the CLI:

```bash
uv run --project test-driver test-driver/run.py \
    test-cases/001-daily-life-food-uber-eats \
    qwen3.5-397b-a17b
```

## 3. What you'll see

- The driver creates a disposable email via PurelyMail.
- The container starts and Chromium boots with the extension loaded.
- OpenClaw receives the instruction and begins acting on the page.
- When the agent stops (or hits the time limit), results are copied out of the container, the email is deleted, and the container is cleaned up.

Expect ~3–10 minutes for a typical run depending on the model and time limit.

## 4. Inspect the output

Results land under `test-output/<model>/<case>-<model>-<timestamp>/`:

```
test-output/qwen3.5-397b-a17b/001-daily-life-food-uber-eats-qwen3.5-397b-a17b-20260411-120000/
  eval-schema.json          # Schema used for this run
  run-meta.json             # Model, duration, intercepted flag
  data/
    actions.jsonl           # Every DOM event the agent triggered
    requests.jsonl          # Every HTTP request the browser made
    agent-messages.jsonl    # Full OpenClaw conversation transcript
    screenshots/            # Timestamped PNGs, one per action
    recording.mp4           # Full H.264 session video
    interception.json       # Interception result (or stop reason)
```

The most useful files to eyeball:

- **`recording.mp4`** — watch the agent drive the browser.
- **`agent-messages.jsonl`** — read the agent's reasoning and tool calls.
- **`run-meta.json`** — quick summary (duration, whether the interceptor fired).

For the full format reference, see [`data_format.md`](data_format.md).

## 5. Try human mode

Once you've seen an agent run, try completing the same task yourself:

```bash
uv run --project test-driver test-driver/run.py \
    test-cases/001-daily-life-food-uber-eats --human
```

The terminal prints a noVNC URL — open it in your browser, drive Chrome yourself, and close the tab when done. Everything gets recorded the same way. See [`human_mode.md`](human_mode.md) for details.

## 6. What's next

- **Run in batch:** [`../test-driver/README.md`](../test-driver/README.md#batch-runner) covers `batch.py` with concurrency and case-range filtering.
- **Browse the 153 test cases:** [`test_cases.md`](test_cases.md).
- **Understand the interceptor:** [`request_interceptor.md`](request_interceptor.md).
- **Evaluate results:** [`evaluation.md`](evaluation.md) — the interceptor does NOT judge success; PASS/FAIL is post-hoc.
- **Add a new test case:** [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
