#!/bin/bash
cd "$(dirname "$0")" || exit
exec uv run --no-editable clawbench
