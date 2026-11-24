#!/usr/bin/env bash
# Copy finished files from the subagents' working folder into the library, then validate, index and render them.
# Usage: bash tools/sync_from_kit.sh KIT_DIR
set -u
KIT="$1"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cp -u "$KIT"/organisations/*.json "$ROOT/organisations/" 2>/dev/null
cp -u "$KIT"/workflows/*.json "$ROOT/workflows/" 2>/dev/null
cd "$ROOT"
python tools/validate.py organisations/*.json > validation_organisations.txt 2>&1
python tools/validate.py workflows/*.json --index workflows_index.csv > validation_workflows.txt 2>&1
python tools/render.py pages/organisations organisations/*.json > /dev/null
python tools/render.py pages/workflows workflows/*.json > /dev/null
tail -1 validation_organisations.txt; tail -1 validation_workflows.txt
echo "workflow errors: $(grep -c ERROR validation_workflows.txt)"
