# ClawBench Evaluation

ClawBench evaluation is a **post-session** step: first you run agents to collect trajectories, then you evaluate those trajectories against human reference runs.

```
Step 1: Run agents          Step 2: Evaluate
(runner package)            (this directory)

./run.sh                    Claude Code subagents compare
  or                        agent traces vs human references
src/runner/batch.py         under eval/agentic_eval.md rubric
       │                              │
       ▼                              ▼
  test-output/                {model}-eval-results.csv
    {model}/{run}/            {model}-eval-results.json
      data/
        actions.jsonl
        requests.jsonl
        screenshots/
        recording.mp4
        interception.json
        agent-messages.jsonl
```

## How It Works

The evaluator is a Claude Code subagent that compares two trajectories side by side:

- **Agent trajectory** -- the five-layer recording from the AI agent's run
- **Human reference trajectory** -- the same five layers recorded by a human annotator completing the task correctly

The evaluator follows a fixed rubric ([`agentic_eval.md`](agentic_eval.md)) to determine PASS or FAIL for each task. This comparative approach means the evaluator has a concrete ground truth -- it knows exactly which form fields to fill, which buttons to click, and which endpoint the final submission hits.

## Prerequisites

- Agent run outputs in `test-output/{model}/` (produced by `clawbench-run` or `clawbench-batch`)
- Human reference runs in a separate directory (same five-layer format)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed

## Running Evaluation

Open Claude Code at the project root and send the following prompt. Replace the three placeholders with your actual values:

- `{agent_dir}` -- path to the model's output directory (e.g., `test-output/claude-sonnet-4-6/`)
- `{human_dir}` -- path to the human reference directory (e.g., `test-output/human/`)
- `{model}` -- model name for output file naming (e.g., `claude-sonnet-4-6`)

```
Read the evaluation rubric at eval/agentic_eval.md and follow it strictly.

Evaluate all 153 agent runs against their corresponding human reference runs.

Agent runs directory: {agent_dir}
Human reference directory: {human_dir}

Each directory contains multiple run subdirectories (one per task). Each run subdirectory contains:
- run-meta.json
- data/actions.jsonl
- data/requests.jsonl
- data/screenshots/
- data/recording.mp4
- data/interception.json
Agent runs also contain data/agent-messages.jsonl.

Dispatch 16 subagents to evaluate in parallel, each subagent handling ~10 tasks. Each subagent should:
1. Match agent run to human run by task_id in run-meta.json
2. Read both run-meta.json to get task instruction and context
3. Compare the agent trajectory against the human reference trajectory
4. Determine PASS or FAIL with justification, noting which evidence files and lines support the decision

Dispatch 3 supervisor agents to monitor the work of the 16 evaluation subagents, checking for consistency and correctness.

After all subagents complete, merge their results and output two files:
1. {model}-eval-results.csv — columns: task_id, task_name, model, pass, brief_justification
2. {model}-eval-results.json — detailed results per task, each entry including: task_id, task_name, model, pass, justification, and evidence references (file path and line numbers that support the verdict)
```

## Output

The evaluation produces two files at the project root:

| File | Format | Description |
|------|--------|-------------|
| `{model}-eval-results.csv` | CSV | Quick summary -- one row per task with PASS/FAIL and a brief justification |
| `{model}-eval-results.json` | JSON | Detailed results with full justification and evidence references (file paths + line numbers) |

## Evaluation Rubric

The full rubric is in [`agentic_eval.md`](agentic_eval.md). Key rules:

- **Interceptor block = PASS** if all prior steps are correct (the interceptor is designed to cut the session short)
- **Payment must be attempted** -- the agent has a dummy credit card and must try to use it
- **Phone verification wall = PASS** if all prior steps are complete (the agent has no phone number)
- **CAPTCHA must be attempted** -- skipping a CAPTCHA is FAIL
- **Email must be used** when the task requires registration or verification
