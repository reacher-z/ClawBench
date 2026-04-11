# Request Interceptor

The request interceptor is ClawBench's safety layer. It blocks critical, irreversible HTTP requests — checkout, form submission, review posting, email sending — to prevent the agent from causing real-world side effects during evaluation.

**Important:** the interceptor does **not** validate task completion. It only blocks requests. PASS/FAIL is determined post-hoc by a human or an agentic reviewer. See [`evaluation.md`](evaluation.md).

## How it works

1. Each test case's `task.json` specifies an `eval_schema` (see [`test-cases/task.schema.json`](../test-cases/task.schema.json)).
2. The test driver writes this schema to `eval-schema.json` in the output directory and mounts it read-only into the container at `/eval-schema.json`.
3. At startup, the extension server connects to Chrome via CDP (`Fetch` domain) and intercepts all browser requests.
4. For each request, the server checks:
   - **URL** against `url_pattern` (Python `re.search`)
   - **HTTP method** against `method`
   - **Body** against `body` (optional, flat key-value exact match)
   - **Query params** against `params` (optional, flat key-value exact match)
5. When all specified conditions match, the request is **blocked**, its details are saved to `/data/interception.json`, the agent is killed, and the recording stops (after a 15-second grace period to capture the final screen state).

## Schema format

```json
{
  "url_pattern": "inbox\\.purelymail\\.com",
  "method": "POST",
  "body": { "_action": "send" }
}
```

| Field         | Type    | Required | Description                                                                 |
| ------------- | ------- | -------- | --------------------------------------------------------------------------- |
| `url_pattern` | string  | yes      | Regex pattern matched against the request URL via `re.search()`             |
| `method`      | string  | yes      | HTTP method to match (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`)              |
| `body`        | object  | no       | Key-value pairs that must match exactly in the request body                 |
| `params`      | object  | no       | Key-value pairs that must match exactly in the URL query parameters         |

The optional `body` and `params` are **flat key-value maps** — each key must match exactly in the request data. Use them when the same URL + method serves multiple actions (e.g., login vs send on the same endpoint, or different GraphQL operations).

Remember to **regex-escape literal dots** in `url_pattern`: `inbox\\.purelymail\\.com`, not `inbox.purelymail.com`.

## When to block

The interceptor should fire only for actions with **irreversible real-world consequences** without a natural payment wall.

| Block   | Examples                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Yes** | Public reviews, listings, job applications, contact forms, email sends, appointment bookings, website creation, content publishing |
| **No**  | Purchases, subscriptions, donations (payment wall), cart additions (reversible), searches (reversible), account creation (benign) |

## The placeholder pattern

For tasks behind a payment wall or another natural blocker (the agent has no valid credit card), use a pattern that will never match:

```json
{
  "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
  "method": "POST"
}
```

The interceptor will never fire, and the session runs until the time limit expires or the agent declares it's done. This is the right choice for checkout-style tasks where the natural payment failure protects you.

## Interception output

When the interceptor fires, `/data/interception.json` contains:

```json
{
  "intercepted": true,
  "request": {
    "url": "https://inbox.purelymail.com/action",
    "method": "POST",
    "params": {},
    "body": {"_action": "send", "_to": "user@example.com"}
  }
}
```

When the session ends for another reason (idle, time limit, agent exit), the test driver writes a fallback `interception.json`:

```json
{
  "intercepted": false,
  "stop_reason": "agent_idle",
  "stop_description": "Session stopped: agent went idle (300s no actions) before triggering the interceptor.",
  "request": null
}
```

See [`architecture.md#watchdog-stop-reasons`](architecture.md#watchdog-stop-reasons) for all stop reasons.

## Finding the right URL pattern for a new test case

When you add a new test case, the hardest part is identifying the terminal HTTP request. The easiest workflow:

1. Run the task in **human mode**: `uv run --project test-driver test-driver/run.py test-cases/<your-case> --human`.
2. Open the noVNC URL and drive the browser yourself to the point just before the irreversible action.
3. Complete the action (it's safe — the interceptor won't be configured yet for your case, or you can intentionally use a placeholder and complete it once to capture the request).
4. Inspect `/data/requests.jsonl` for the terminal POST — look at the URL, method, and body shape.
5. Regex-escape literal dots in the URL and write it as `url_pattern`.
6. If the same URL + method is hit by unrelated requests (very common for SPAs), add a `body` or `params` filter with the specific action discriminator.

See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for the full test-case authoring workflow.

## Related reading

- [`evaluation.md`](evaluation.md) — why the interceptor does NOT judge success
- [`architecture.md`](architecture.md) — how the interceptor fits into the container lifecycle
- [`../test-cases/task.schema.json`](../test-cases/task.schema.json) — the authoritative JSON schema
