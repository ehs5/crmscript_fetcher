#!/usr/bin/env bash
# Builds the macOS GUI app in one command: dist/CRMScript Fetcher.app
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Building Vue frontend"
(cd gui/vue && npm ci && npm run build)

echo "==> Setting up Python environment"
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --quiet -r requirements.txt

echo "==> Building macOS app"
.venv/bin/pyinstaller "CRMScript Fetcher.spec"

echo "==> Done: dist/CRMScript Fetcher.app"
