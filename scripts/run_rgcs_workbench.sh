#!/usr/bin/env bash
# Launcher for the RGCS workbench installed via scripts/install_linux.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
if [ -f "$ROOT/.venv/bin/activate" ]; then
    source "$ROOT/.venv/bin/activate"
else
    source "$ROOT/.venv/Scripts/activate"
fi
exec rgcs-workbench "$@"
