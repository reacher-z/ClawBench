#!/usr/bin/env bash
#
# Record the README hero GIF reproducibly.
#
# The ClawBench hero is the single biggest star-driver we're missing
# (20 peer-repo study: 14/20 used a hero GIF/video above the fold).
# This script produces static/hero.gif from a real agent run so we can
# re-generate it each release without scrambling.
#
# Usage:
#   ./scripts/record-hero-gif.sh <case-dir> <model>
#   e.g. ./scripts/record-hero-gif.sh test-cases/daily-life-food-uber-eats claude-opus-4-6
#
# Requirements: ffmpeg, gifski (brew install ffmpeg gifski).
# Produces:  static/hero.gif (~15s, <1200px wide, <6 MB).

set -euo pipefail

CASE="${1:?usage: $0 <case-dir> <model>}"
MODEL="${2:?usage: $0 <case-dir> <model>}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
OUT_DIR="${REPO_ROOT}/static"
MP4="${OUT_DIR}/hero-source.mp4"
GIF="${OUT_DIR}/hero.gif"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found (brew install ffmpeg)"; exit 1; }
command -v gifski >/dev/null || { echo "gifski not found (brew install gifski)"; exit 1; }

mkdir -p "$OUT_DIR"

# ClawBench records the agent's browser to <output-dir>/recording.mp4
# automatically (see extension-server/server.py). We just point
# `claw-bench run` at a known output dir and grab that file.
RUN_OUT="${REPO_ROOT}/claw-output/hero-gif-$(date +%s)"
echo ">> Running agent on $CASE with $MODEL (recording to $RUN_OUT)"
"${REPO_ROOT}/run.sh" run "$CASE" "$MODEL" --output-dir "$RUN_OUT" --no-upload

SOURCE_MP4="$(find "$RUN_OUT" -name 'recording.mp4' -print -quit)"
[ -z "$SOURCE_MP4" ] && { echo "recording.mp4 not found under $RUN_OUT"; exit 1; }

echo ">> Trimming to the 15s that best tells the story"
# Default trim: the last 15s before interception — usually the payoff.
# Operators can re-run with FROM=<seconds> TO=<seconds> env vars if the
# interesting moment is elsewhere.
FROM="${FROM:-$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$SOURCE_MP4" | awk '{printf "%d", $1 - 15}')}"
TO="${TO:-$((FROM + 15))}"
ffmpeg -y -ss "$FROM" -to "$TO" -i "$SOURCE_MP4" \
  -vf "scale=1200:-2,fps=12" -an "$MP4"

echo ">> Encoding GIF via gifski (smaller + higher quality than ffmpeg)"
ffmpeg -y -i "$MP4" -vf "fps=12" "${OUT_DIR}/hero-%04d.png"
gifski --fps 12 --width 1200 --quality 85 \
  -o "$GIF" "${OUT_DIR}"/hero-*.png
rm -f "${OUT_DIR}"/hero-*.png

echo ">> Done: $GIF ($(du -h "$GIF" | cut -f1))"
echo "   Embed in README.md above the 'Can AI Agents...' subtitle:"
echo "     <img src=\"static/hero.gif\" alt=\"ClawBench agent demo\" width=\"720\">"
