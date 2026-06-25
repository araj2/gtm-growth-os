#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run marimo edit notebooks/gtm_growth_os_marimo.py
