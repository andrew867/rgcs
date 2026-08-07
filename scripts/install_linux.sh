#!/usr/bin/env bash
# RGCS Linux installer: venv + desktop extra + smoke check + receipt.
# Intended for a clean checkout; reuses an existing .venv if present.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ required")
print(f"Python OK: {sys.version}")
PY

if [ ! -f .venv/bin/activate ] && [ ! -f .venv/Scripts/activate ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate          # POSIX venv layout
else
    source .venv/Scripts/activate      # Windows venv layout (Git Bash)
fi
python -m pip install --upgrade pip
python -m pip install -e ".[desktop]"

QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}" \
    python -m rgcs_desktop --smoke-check \
    || QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}" \
       rgcs-workbench --smoke-check

mkdir -p .rgcs-install
cat > .rgcs-install/install_receipt.txt <<EOF
RGCS install receipt
python=$(python --version)
date=$(date -Iseconds)
path=$ROOT
smoke=passed
EOF

chmod +x scripts/run_rgcs_workbench.sh
echo "Install complete. Run: ./scripts/run_rgcs_workbench.sh"
