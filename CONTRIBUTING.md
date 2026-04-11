# Contributing to ClawBench

Thanks for contributing! The single highest-leverage contribution is **adding new test cases** — they expand the benchmark's coverage. This doc also covers bug reports, new model wiring, documentation changes, and the PR checklist.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#reporting-bugs)
- [Adding a New Test Case](#adding-a-new-test-case)
- [Adding a New Model](#adding-a-new-model)
- [Documentation Changes](#documentation-changes)
- [Pull Request Checklist](#pull-request-checklist)

## Code of Conduct

Be kind. Treat reviewers and other contributors with respect.

**Never commit real PII.** All test cases use the Alex Green synthetic profile — never add your own email, name, phone, or address to a test case (they'll be replaced at runtime anyway). Never commit real API keys, passwords, or credentials to `models/models.yaml`, `.env`, or anywhere else. If you accidentally do, rotate the key immediately.

## Reporting Bugs

Before opening an issue, check [`docs/troubleshooting.md`](docs/troubleshooting.md) — many common failures are documented there with fixes.

When opening a new issue, please include:

- **Reproduction steps** — the exact command you ran and the test case + model involved.
- **Expected vs actual behavior.**
- **Environment** — OS, container engine + version (`docker --version` or `podman --version`), `uv --version`, Python version.
- **Logs** — the contents of `test-output/.../data/interception.json` (stop reason), `data/gateway.log` if OpenClaw was involved, and the last 100 lines of the container log if available.

## Adding a New Test Case

This is the main path for new contributors. Expect to spend ~30 minutes on your first case; subsequent ones go faster.

### 1. Pick an unused task ID

Task IDs are globally unique but gaps are allowed — you don't need to pick the next integer, just pick one that isn't used.

```bash
ls test-cases/ | awk -F- '{print $1}' | sort -n | tail
```

Pick an ID higher than the largest, or fill in a gap.

### 2. Name the directory

Convention: `{task_id:03d}-{metaclass}-{class}-{platform}` — lowercase, hyphen-separated, no spaces.

Examples from the repo:

- `001-daily-life-food-uber-eats`
- `086-job-search-hr-cv-autofill-greenhouse-meta`
- `482-creation-init-general-confluence`
- `551-finance-investment-crypto-wallet-trezor`

See [`docs/test_cases.md`](docs/test_cases.md) for the full category breakdown and pick a metaclass that fits your task.

### 3. Write `task.json`

Your test case directory must contain a `task.json` that validates against [`test-cases/task.schema.json`](test-cases/task.schema.json). Here's a complete example:

```json
{
  "$schema": "../task.schema.json",
  "metadata": {
    "task_id": 887,
    "metaclass": "daily-life",
    "class": "food",
    "description": "Order food from DoorDash for delivery to the user's address, using the user's default payment method.",
    "sites_involved": ["doordash.com"],
    "platform": "doordash",
    "common_info": {
      "email_credentials": "credentials to use the assigned disposable email account",
      "user_info": "alex_green_personal_info.json; the dummy user's personal information",
      "user_resume": "PDF resume with disposable email account injected"
    }
  },
  "instruction": "Order a large pepperoni pizza from the nearest Pizza Hut on DoorDash. Use my saved address and default payment method. Complete the order.",
  "eval_schema": {
    "url_pattern": "doordash\\.com/graphql/checkoutCart",
    "method": "POST",
    "body": { "operationName": "placeOrder" }
  },
  "time_limit": 10
}
```

Notes:

- `common_info` keys are `const` strings in the schema — copy them verbatim from any existing test case.
- `instruction` is sent to the agent verbatim as part of its prompt. Keep it natural and specific.
- `time_limit` is in **minutes** (not seconds). Rule of thumb: 2–3× the typical human completion time.
- `extra_info` is optional (see below).

### 4. Choose the `eval_schema`

This is the trickiest part. The `eval_schema` tells the request interceptor which HTTP request represents the "point of no return" for the task.

**Block irreversible actions only:**

| Block   | Examples                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Yes** | Public reviews, listings, job applications, contact forms, email sends, appointment bookings, website publishing                  |
| **No**  | Purchases, subscriptions, donations (payment wall), cart additions (reversible), searches (reversible), account creation (benign) |

For tasks behind a payment wall or another natural blocker — the agent has no valid credit card, so the payment page is a dead end anyway — use the placeholder pattern:

```json
{
  "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
  "method": "POST"
}
```

The interceptor will never fire and the session runs until the time limit. That's correct for checkout-style tasks.

#### Finding the right URL pattern

The best way to discover the terminal HTTP request:

1. Run the task in **human mode** on the case you're authoring (with any `url_pattern` — even the placeholder, since you'll replace it):

   ```bash
   uv run --project test-driver test-driver/run.py test-cases/887-daily-life-food-doordash --human
   ```

2. Open the noVNC URL and complete the task by hand until just before the irreversible action.
3. Click the final button (Submit, Place Order, Send, etc.).
4. Inspect `test-output/.../data/requests.jsonl` for the terminal POST.
5. Extract the URL and regex-escape literal dots (`doordash.com` → `doordash\\.com`).
6. If the same URL + method is hit by unrelated requests (very common for SPAs and GraphQL), add a `body` or `params` filter with the specific discriminator — often an `operationName`, `_action`, or `event_type` field.

See [`docs/request_interceptor.md`](docs/request_interceptor.md) for the full schema reference.

### 5. Set `time_limit`

Expressed in **minutes**. Pick 2–3× the time it takes you to complete the task manually in human mode.

Most existing cases use values between 5 and 30. Shorter is better — you want the agent to fail fast on obvious dead ends.

### 6. (Optional) Add `extra_info` files

If your test case needs a specific file in `/my-info/` (a project brief, a spreadsheet the agent must upload, a screenshot, etc.), place it in your test case directory and reference it from `task.json`:

```
test-cases/887-daily-life-food-doordash/
  task.json
  extra_info/
    preferences.json
```

```json
{
  "extra_info": [
    {
      "path": "extra_info/preferences.json",
      "description": "Food preferences and dietary restrictions — reference these before placing the order."
    }
  ]
}
```

The driver copies the file into `/my-info/` inside the container and injects `preferences.json: <description>` into the agent prompt.

### 7. Validate locally

Dry-run in human mode:

```bash
uv run --project test-driver test-driver/run.py test-cases/887-daily-life-food-doordash --human
```

Check:

- Container builds and Chromium launches.
- You can complete the task manually via noVNC.
- The interceptor fires on the correct request (check `data/interception.json` shows `"intercepted": true` with the expected URL).
- `run-meta.json` looks right.

### 8. (Optional but encouraged) Agent validation

Run the case end-to-end with one cheap or free model:

```bash
uv run --project test-driver test-driver/run.py test-cases/887-daily-life-food-doordash qwen3.5-397b-a17b
```

Watch `data/recording.mp4` and skim `data/agent-messages.jsonl`. If you want a formal PASS/FAIL, run the agentic evaluator prompt at [`prompts/agentic_eval.md`](prompts/agentic_eval.md) against the output — see [`docs/evaluation.md`](docs/evaluation.md).

### 9. Open the PR

- **One test case per PR** is strongly preferred (easier to review, easier to revert).
- Include in the PR description:
  - A 1-sentence summary of what the task is.
  - The human-mode result (`duration_seconds`, `intercepted: true/false`).
  - (Optional) the agent result with at least one model.
- Do not include your personal `.env` or `models/models.yaml` in the PR (they're gitignored — verify with `git status`).

## Adding a New Model

Models are configured per-user in `models/models.yaml`, which is gitignored. You do **not** need to open a PR to add a model for your own use — just edit your local `models/models.yaml`.

If you want to add a brand-new `api_type` (a provider that OpenClaw doesn't already support), that's an upstream change in OpenClaw itself — open an issue on this repo so we can track it, then work with the OpenClaw maintainers.

See [`docs/installation.md#5-get-a-model-api-key`](docs/installation.md#5-get-a-model-api-key) for supported providers and their `api_type` values.

## Documentation Changes

All user-facing docs live in `docs/`. Each file is scoped to one concept — keep it that way. If you add a new concept, add a new file under `docs/` and link it from [`docs/README.md`](docs/README.md) and the root README's Documentation table.

The root `README.md` should stay concise (~180 lines). Push deep content into `docs/`.

Sub-component READMEs (`test-driver/`, `chrome-extension/`, `extension-server/`) own their own detail and should not be duplicated in `docs/`.

## Pull Request Checklist

- [ ] No secrets committed (`.env`, `models/models.yaml`, API keys in examples)
- [ ] No real PII (real emails, names, phone numbers) in test cases
- [ ] New test case: `task.json` validates against `test-cases/task.schema.json`
- [ ] New test case: human-mode dry run succeeds and the interceptor fires on the expected request (or the placeholder pattern is deliberately used)
- [ ] Docs changes: new files are linked from `docs/README.md`
- [ ] Commit messages are descriptive (the commit style is lowercase imperative, e.g. `docs: overhaul readme`)
- [ ] `README.md` still renders correctly and all links resolve
