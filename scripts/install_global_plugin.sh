#!/bin/bash
# Enterprise Synapse-Hub Global Antigravity Plugin Installer (macOS / Linux)
# ======================================================================
# Mounts Synapse-Hub directly into Google Antigravity's Global Plugin Directory.
# Once installed, all 27 skills and 6 subagents are active across all projects automatically.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
echo "======================================================================"
echo "   SYNAPSE-HUB: ANTIGRAVITY GLOBAL PLUGIN 1-CLICK INSTALLER           "
echo "======================================================================"
echo ""

PLUGINS_DIR="$HOME/.gemini/config/plugins"
TARGET_PLUGIN_DIR="$PLUGINS_DIR/synapse-hub"

mkdir -p "$PLUGINS_DIR"
mkdir -p "$TARGET_PLUGIN_DIR"

echo "[1/4] Copying plugin manifest..."
cp "$REPO_ROOT/plugin.json" "$TARGET_PLUGIN_DIR/plugin.json"
[ -f "$REPO_ROOT/README.md" ] && cp "$REPO_ROOT/README.md" "$TARGET_PLUGIN_DIR/README.md"

echo "[2/4] Symlinking skills, agents, and tools..."
ln -sfn "$REPO_ROOT/.agents/skills" "$TARGET_PLUGIN_DIR/skills"
ln -sfn "$REPO_ROOT/.agents/agents" "$TARGET_PLUGIN_DIR/agents"
ln -sfn "$REPO_ROOT/tools" "$TARGET_PLUGIN_DIR/tools"

mkdir -p "$TARGET_PLUGIN_DIR/rules"
cp "$REPO_ROOT/AGENTS.md" "$TARGET_PLUGIN_DIR/rules/AGENTS.md"

echo "[3/4] Initializing Central Agent Memory (SQLite Cache)..."
python3 "$REPO_ROOT/tools/cache_resolver.py" init 2>/dev/null || python "$REPO_ROOT/tools/cache_resolver.py" init 2>/dev/null || true

echo ""
echo "======================================================================"
echo "  🎉 SUCCESS: Synapse-Hub is now installed as a GLOBAL PLUGIN!        "
echo "======================================================================"
echo "• Location : $TARGET_PLUGIN_DIR"
echo "• Skills   : 27 Standardized QA Skills"
echo "• Agents   : 6 Swarm Subagent Profiles"
echo ""
echo "👉 Antigravity will now automatically load Synapse-Hub across ALL projects"
echo "   without needing to add Synapse-Hub as a workspace folder!"
echo "======================================================================"
echo ""
