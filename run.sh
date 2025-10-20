#!/usr/bin/env bash
set -euo pipefail

# Create venv if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt

export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/main.py


