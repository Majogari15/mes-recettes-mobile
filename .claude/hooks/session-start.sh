#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

python3 -m pip install --quiet --disable-pip-version-check --root-user-action=ignore -r tests/requirements.txt

# Chromium est préinstallé dans /opt/pw-browsers sur les sessions web ;
# ne le télécharger que s'il manque pour la version de Playwright épinglée.
if ! python3 - << 'PY'
import sys
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        p.chromium.launch().close()
except Exception:
    sys.exit(1)
PY
then
  python3 -m playwright install chromium
fi
