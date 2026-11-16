#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.10 or newer, then run this file again."
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || true
fi

APP_PACKAGES="$ROOT/.app-packages"
if [[ -x .venv/bin/python ]] && .venv/bin/python -m pip --version >/dev/null 2>&1; then
  PYTHON="$ROOT/.venv/bin/python"
  if ! "$PYTHON" -c 'import flask, googleapiclient, google_auth_oauthlib' >/dev/null 2>&1; then
    echo "Installing the app's Python packages into .venv…"
    "$PYTHON" -m pip install -r requirements.txt
  fi
else
  PYTHON="$(command -v python3)"
  if ! PYTHONPATH="$APP_PACKAGES${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" -c 'import flask, googleapiclient, google_auth_oauthlib' >/dev/null 2>&1; then
    if ! command -v pip3 >/dev/null 2>&1; then
      echo "Python's venv/pip support is missing. On Ubuntu install it with: sudo apt install python3-venv python3-pip"
      exit 1
    fi
    echo "This Linux Python has no ensurepip; installing packages in the project-local .app-packages folder…"
    pip3 install --disable-pip-version-check --break-system-packages --upgrade --target "$APP_PACKAGES" -r requirements.txt
  fi
  export PYTHONPATH="$APP_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"
fi

echo "Starting SEO app at http://127.0.0.1:5000"
echo "Keep this window open. Press Ctrl+C to stop the app."
export SEO_OPEN_BROWSER=1
exec "$PYTHON" dashboard/app.py
