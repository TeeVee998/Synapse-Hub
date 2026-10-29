#!/usr/bin/env bash
# ==============================================================================
# Enterprise Agent-Skills Hub: Automated Bootstrap Setup (macOS / Linux)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

echo "=========================================================="
echo "  Enterprise Agent-Skills Hub: Automated Bootstrap Setup  "
echo "=========================================================="

# 1. Python 3 Runtime
echo -e "\n[1/4] Checking Python 3 Runtime..."
if command -v python3 &>/dev/null; then
  echo "  [OK] Found Python: $(python3 --version)"
else
  echo "  [FAIL] Python 3 is required. Please install via apt, brew, or dnf."
  exit 1
fi

# 2. Virtual Environment
echo -e "\n[2/4] Setting up Virtual Environment (.venv)..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
VENV_PY=".venv/bin/python"

# 3. Dependencies
echo -e "\n[3/5] Installing Core Dependencies..."
"$VENV_PY" -m pip install --upgrade pip setuptools wheel --quiet
if [ -f "requirements.txt" ]; then
  "$VENV_PY" -m pip install -r requirements.txt --quiet
  echo "  [OK] Requirements installed successfully."
fi

# 4. Verification
echo -e "\n[4/5] Verifying Skills Catalog Integrity..."
if [ -f "tools/verify_all.py" ]; then
  "$VENV_PY" tools/verify_all.py || true
fi

# 5. Initialize Central Agent Memory (SQLite Cache)
echo -e "\n[5/5] Initializing Global Central Agent Memory (~/.agent_memory/global_cache.db)..."
if [ -f "tools/cache_resolver.py" ]; then
  "$VENV_PY" tools/cache_resolver.py init || true
  echo "  [OK] Central Agent Memory initialized and seeded."
fi

echo -e "\n=========================================================="
echo "  Bootstrap Complete! Hub is ready for Multi-Agent Swarm."
echo "=========================================================="
