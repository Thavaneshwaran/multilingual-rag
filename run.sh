#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama pull llama3.1:8b || true

python ingest.py
uvicorn server:app --reload --port 8000
