---
title: ClawBench Leaderboard
emoji: ""
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: true
license: mit
---

# ClawBench Leaderboard (HF Space)

Gradio frontend for the public ClawBench leaderboard. Reads the CSVs under
`eval-results/` and renders overall, per-category, and per-task breakdowns.

## Local dev

```bash
cd leaderboard
pip install -r requirements.txt
python app.py
```

## Deploy to Hugging Face

One-time setup:

```bash
huggingface-cli login
huggingface-cli repo create clawbench-leaderboard --type space --space_sdk gradio
```

To update the Space, copy the latest CSVs into `leaderboard/eval-results/`
and push:

```bash
cp -r ../eval-results .
git add eval-results/ app.py requirements.txt README.md
git commit -m "Update leaderboard"
git push https://huggingface.co/spaces/<user>/clawbench-leaderboard main
```

The Space rebuilds automatically on push.

## Adding a model

Every CSV under `eval-results/` is picked up automatically - no app changes
needed. The filename convention is `<model-id>-eval-results.csv` and the
required columns are `task_id, task_name, model, pass, brief_justification`.

To contribute a new run: open a PR on the main repo adding your CSV. The
Space will pick it up on the next deploy.
