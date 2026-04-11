# Contributing to ClawBench

Thanks for your interest in contributing! The most impactful way to contribute is by adding new test cases that expand ClawBench's coverage of real-world web tasks.

## Adding a New Test Case

1. **Pick a task ID** — find the next available number by checking existing directories in `test-cases/`.

2. **Create the directory** following the naming convention:
   ```
   test-cases/<id>-<metaclass>-<class>-<platform>/
   ```
   Example: `test-cases/887-daily-life-food-grubhub/`

3. **Create `task.json`** in the directory. It must conform to `test-cases/task.schema.json`:
   ```json
   {
     "$schema": "../task.schema.json",
     "metadata": {
       "task_id": 887,
       "metaclass": "daily-life",
       "class": "food",
       "description": "Order a burger on Grubhub",
       "sites_involved": ["grubhub.com"],
       "platform": "grubhub",
       "common_info": {
         "email_credentials": "credentials to use the assigned disposable email account",
         "user_info": "alex_green_personal_info.json; the dummy user's personal information",
         "user_resume": "PDF resume with disposable email account injected"
       }
     },
     "instruction": "On Grubhub, order delivery: one cheeseburger to home address",
     "eval_schema": {
       "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
       "method": "POST"
     },
     "time_limit": 30
   }
   ```

4. **Set the eval_schema** — this tells the interceptor which HTTP request to block:
   - If the task has an irreversible action (form submit, email send, application submit): set `url_pattern` to a regex matching the submission endpoint, and `method` to the HTTP method.
   - If the task is behind a payment wall (agent has no valid credit card): use `"url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__"` — the interceptor will never fire and the session runs until timeout.
   - See [test-driver/README.md](test-driver/README.md#eval_schema) for details on `body` and `params` filters.

5. **Test with human mode** to verify the task is completable:
   ```bash
   uv run --project test-driver test-driver/run.py test-cases/887-daily-life-food-grubhub --human
   ```

6. **Submit a PR** with your new test case directory.

## Extra Info Files

If the task requires additional context (e.g., a pre-filled profile, a specific document), add files under `extra_info/` in the test case directory and reference them in `task.json`:

```json
"extra_info": [
  {
    "path": "extra_info/cover_letter.txt",
    "description": "Cover letter to attach with the application"
  }
]
```

## Code Changes

For changes to the framework itself (test driver, extension server, Chrome extension, container):

1. Read the relevant sub-README for component-specific documentation:
   - [test-driver/README.md](test-driver/README.md)
   - [extension-server/README.md](extension-server/README.md)
   - [chrome-extension/README.md](chrome-extension/README.md)
2. Open a PR with a clear description of the change and how you tested it.

## Reporting Issues

Please use the [issue templates](https://github.com/reacher-z/ClawBench/issues/new/choose) to report bugs or propose new test cases.
