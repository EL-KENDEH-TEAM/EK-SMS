#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002