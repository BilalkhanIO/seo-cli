#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.10 or newer, then run this file again."
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
PYTHON="$ROOT/.venv/bin/python"

if ! "$PYTHON" -c 'import flask, googleapiclient, google_auth_oauthlib' >/dev/null 2>&1; then
  echo "Installing the app's Python packages…"
  "$PYTHON" -m pip install --upgrade pip
  "$PYTHON" -m pip install -r requirements.txt
fi

echo "Starting SEO app at http://127.0.0.1:5000"
echo "Keep this window open. Press Ctrl+C to stop the app."
("$PYTHON" -c 'import time, webbrowser; time.sleep(1); webbrowser.open("http://127.0.0.1:5000")' >/dev/null 2>&1 &) || true
exec "$PYTHON" dashboard/app.py
