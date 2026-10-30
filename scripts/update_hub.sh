#!/bin/bash
# Enterprise Synapse-Hub 1-Click Update Script (macOS / Linux)
# ======================================================================
# Pulls latest updates, refreshes Global Plugin, and syncs episodic memory.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ "$1" = "--check" ]; then
    python3 "$REPO_ROOT/tools/update_sentinel.py" --check 2>/dev/null || python "$REPO_ROOT/tools/update_sentinel.py" --check
    exit $?
fi

python3 "$REPO_ROOT/tools/update_sentinel.py" --update 2>/dev/null || python "$REPO_ROOT/tools/update_sentinel.py" --update
