#!/bin/bash
cd "$(dirname "$0")" || exit
exec uv run clawbench
