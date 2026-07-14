#!/usr/bin/env bash
# Build the Linux one-dir distribution of the RGCS v2 desktop workbench.
#
# Run from anywhere; builds into <repo>/release/linux/.
# Requirements: python3.11+, pip install .[desktop] pyinstaller
#
# Result: release/linux/rgcs-workbench/rgcs-workbench (plus _internal/).
# Smoke check performed at the end with QT_QPA_PLATFORM=offscreen.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${HERE}/../.." && pwd)"
DIST="${REPO}/release/linux"
WORK="${REPO}/build/pyinstaller-linux"

cd "${REPO}"
python3 -m PyInstaller tools/packaging/rgcs_desktop.spec \
    --noconfirm \
    --distpath "${DIST}" \
    --workpath "${WORK}"

echo "--- smoke check (offscreen, must print the version banner) ---"
QT_QPA_PLATFORM=offscreen RGCS_SMOKE_CHECK=1 \
    "${DIST}/rgcs-workbench/rgcs-workbench" --smoke-check
echo "Build OK: ${DIST}/rgcs-workbench/"
