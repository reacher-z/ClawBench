"""
ClawBench public leaderboard - Hugging Face Space entry point.

The source of truth is the `eval-results/` directory in the main repo: every
model that has been evaluated has a `<model>-eval-results.csv` with one row
per task. This app reads those CSVs at startup and renders:

  - overall pass rate per model
  - per-category breakdown
  - per-task pass/fail matrix so readers can see exactly where each agent
    broke

To refresh the board after a new eval run: copy the updated CSVs into this
Space's `eval-results/` dir and redeploy. No database, no background jobs.
That's the point - the board is auditable and reproducible from git.
"""
from __future__ import annotations

import csv
from pathlib import Path

import gradio as gr
import pandas as pd

RESULTS_DIR = Path(__file__).parent / "eval-results"
REPO_URL = "https://github.com/reacher-z/ClawBench"


def load_results() -> pd.DataFrame:
    rows: list[dict] = []
    for csv_path in sorted(RESULTS_DIR.glob("*-eval-results.csv")):
        with csv_path.open() as f:
            for row in csv.DictReader(f):
                row["pass_bool"] = row["pass"].strip().lower() == "true"
                row["category"] = row["task_name"].split("-")[0] if row.get("task_name") else "unknown"
                rows.append(row)
    if not rows:
        return pd.DataFrame(columns=["task_id", "task_name", "model", "pass", "brief_justification", "pass_bool", "category"])
    return pd.DataFrame(rows)


def overall_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Model", "Pass rate", "Passed", "Total"])
    agg = df.groupby("model")["pass_bool"].agg(["sum", "count"]).reset_index()
    agg["Pass rate"] = (agg["sum"] / agg["count"] * 100).round(1).astype(str) + "%"
    agg = agg.rename(columns={"model": "Model", "sum": "Passed", "count": "Total"})
    agg = agg[["Model", "Pass rate", "Passed", "Total"]]
    agg = agg.sort_values("Passed", ascending=False).reset_index(drop=True)
    return agg


def category_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    pivot = df.pivot_table(index="category", columns="model", values="pass_bool", aggfunc="mean") * 100
    return pivot.round(1).reset_index()


def task_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    pivot = df.pivot_table(index=["task_id", "task_name"], columns="model", values="pass", aggfunc="first")
    return pivot.reset_index()


def build_ui() -> gr.Blocks:
    df = load_results()
    with gr.Blocks(title="ClawBench Leaderboard", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            f"""
            # ClawBench Leaderboard

            Live pass-rate board for browser agents on 153 everyday web tasks.
            Source of truth: [`eval-results/` in the main repo]({REPO_URL}/tree/main/eval-results).

            Want your model on here? Run `clawbench batch` and open a PR adding your CSV.
            """
        )
        with gr.Tab("Overall"):
            gr.Dataframe(overall_table(df), interactive=False)
        with gr.Tab("By category"):
            gr.Markdown("Pass rate (%) per category. Higher is better.")
            gr.Dataframe(category_table(df), interactive=False)
        with gr.Tab("Per-task matrix"):
            gr.Markdown("Every task x every model. True = agent passed, False = failed.")
            gr.Dataframe(task_matrix(df), interactive=False, wrap=True)
    return demo


if __name__ == "__main__":
    build_ui().launch()
