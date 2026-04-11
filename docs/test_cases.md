# Test Case Gallery

ClawBench ships with **153 test cases** across **27 metaclass groups**, covering everything from ordering food and booking flights to filing expense reports, opening GitHub issues, and applying for jobs.

Every test case lives under [`../test-cases/`](../test-cases/) and is validated against [`../test-cases/task.schema.json`](../test-cases/task.schema.json).

## Naming convention

```
{task_id:03d}-{metaclass}-{class}-{platform}
```

Example: `001-daily-life-food-uber-eats`

- **task_id** — three-digit zero-padded numeric identifier, globally unique. Gaps are allowed (not every integer has a case).
- **metaclass** — high-level category (e.g. `daily-life`, `job-search`, `office-secretary`).
- **class** — granular sub-category (e.g. `food`, `hr-cv-autofill`, `tasks-email-mgmt`).
- **platform** — the primary site/platform the task exercises (e.g. `uber-eats`, `greenhouse-meta`, `purelymail`).

All three metadata fields are also duplicated inside `task.json`'s `metadata` block (see [`../test-cases/task.schema.json`](../test-cases/task.schema.json)).

## Category breakdown

| Metaclass group        | Count | Example                                                       |
| ---------------------- | ----- | ------------------------------------------------------------- |
| daily-life             | 21    | `001-daily-life-food-uber-eats`                               |
| entertainment-hobbies  | 14    | `363-entertainment-hobbies-general-ticketmaster`              |
| creation-init          | 13    | `482-creation-init-general-confluence`                        |
| rating-voting          | 10    | `468-rating-voting-general-glassdoor`                         |
| office-secretary       | 9     | `120-office-secretary-tasks-email-mgmt-purelymail`            |
| education-learning     | 9     | `265-education-learning-general-coursera`                     |
| beauty-personal        | 9     | `780-beauty-personal-care-skincare-purchase-soko-glam`        |
| pet-animal             | 8     | `795-pet-animal-care-pet-adoption-aspca`                      |
| job-search             | 8     | `086-job-search-hr-cv-autofill-greenhouse-meta`               |
| shopping-commerce      | 6     | `632-shopping-commerce-beauty-care-olaplex`                   |
| personal-management    | 6     | `403-personal-management-account-security-1password-web`      |
| nonprofit-charity      | 6     | `766-nonprofit-charity-donation-doctors-without-borders-msf`  |
| academia-research      | 5     | `215-academia-research-paper-tables-overleaf`                 |
| home-services          | 4     | `735-home-services-maintenance-house-cleaning-bark`           |
| finance-investment     | 4     | `551-finance-investment-crypto-wallet-trezor`                 |
| automotive-vehicle     | 4     | `750-automotive-vehicle-services-car-insurance-compare-kanetix` |
| automation-workflows   | 3     | `695-automation-workflows-recurring-order-stumptown-coffee`   |
| travel-outdoor         | 2     | `865-travel-outdoor-hipcamp`                                  |
| travel-general         | 2     | `279-travel-general-airbnb`                                   |
| travel-flights         | 2     | `615-travel-flights-spirit-airlines`                          |
| dev-tech               | 2     | `179-dev-tech-github-ops-github`                              |
| travel-train           | 1     | `618-travel-train-bus-12go-asia`                              |
| travel-camping         | 1     | `625-travel-camping-outdoor-parks-canada-reservations`        |
| travel-bus             | 1     | `626-travel-bus-flixbus`                                      |
| government-civic       | 1     | `676-government-civic-legal-docs-legalnature`                 |
| entertainment-gaming   | 1     | `671-entertainment-gaming-humble-bundle`                      |
| deletion-revocation    | 1     | `700-deletion-revocation-data-deletion-deleteme`              |
| **Total**              | **153** |                                                             |

## Browsing

### By category

```bash
ls test-cases/ | grep -E '^[0-9]+-daily-life-'
ls test-cases/ | grep -E '^[0-9]+-job-search-'
ls test-cases/ | grep -E '^[0-9]+-travel-'
```

### By ID range

The batch runner supports `--case-range START-END` based on the numeric prefix:

```bash
# All cases with IDs 1 through 50
uv run --project test-driver test-driver/batch.py \
    --all-models --case-range 1-50 --max-concurrent 3
```

See [`../test-driver/README.md#batch-runner`](../test-driver/README.md#batch-runner) for full batch options.

### By platform

```bash
ls test-cases/ | grep airbnb
ls test-cases/ | grep github
ls test-cases/ | grep doordash
```

## Anatomy of a test case

Each case is a directory containing at minimum a `task.json`:

```
test-cases/001-daily-life-food-uber-eats/
  task.json
  extra_info/               # optional, files mounted into /my-info/
```

`task.json` structure:

```json
{
  "$schema": "../task.schema.json",
  "metadata": {
    "task_id": 1,
    "metaclass": "daily-life",
    "class": "food",
    "description": "Order food from Uber Eats for delivery.",
    "sites_involved": ["ubereats.com"],
    "platform": "uber-eats",
    "common_info": {
      "email_credentials": "credentials to use the assigned disposable email account",
      "user_info": "alex_green_personal_info.json; the dummy user's personal information",
      "user_resume": "PDF resume with disposable email account injected"
    }
  },
  "instruction": "Task prompt sent to the agent",
  "eval_schema": {
    "url_pattern": "__PLACEHOLDER_WILL_NOT_MATCH__",
    "method": "POST"
  },
  "time_limit": 5
}
```

See [`../test-cases/task.schema.json`](../test-cases/task.schema.json) for the authoritative field reference, and [`request_interceptor.md`](request_interceptor.md) for how `eval_schema` is used.

## Adding a new test case

The full workflow lives in [`../CONTRIBUTING.md`](../CONTRIBUTING.md). Short version:

1. Pick the next unused `task_id`.
2. Create `test-cases/{id:03d}-{metaclass}-{class}-{platform}/`.
3. Write `task.json` (schema-validated at runtime).
4. Find the right `eval_schema.url_pattern` by running the task in human mode and inspecting `requests.jsonl` (see [`request_interceptor.md#finding-the-right-url-pattern-for-a-new-test-case`](request_interceptor.md#finding-the-right-url-pattern-for-a-new-test-case)).
5. Validate with `--human` mode.
6. Open a PR — one test case per PR is preferred.
