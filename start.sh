#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo " Resume AI Assistant - starting..."
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.11+ and try again."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
  echo "Add GEMINI_API_KEY to .env for Gemini answers (optional for local demo)."
fi

if [ ! -f "knowledge/index/chunks.json" ]; then
  echo "Building knowledge index..."
  python -m src.ingest
fi

echo ""
echo " Open http://127.0.0.1:8000"
echo " Keep this terminal open. Press Ctrl+C to stop."
echo ""

if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:8000" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:8000" || true
fi

python -m src.webapp
