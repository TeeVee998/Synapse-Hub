# Enterprise Synapse-Hub 1-Click Update Script (Windows PowerShell)
# ======================================================================
# Pulls latest updates, refreshes Global Plugin, and syncs episodic memory.

[CmdletBinding()]
param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path "$ScriptDir\.."

if ($Check) {
    python "$RepoRoot\tools\update_sentinel.py" --check
    exit $LASTEXITCODE
}

python "$RepoRoot\tools\update_sentinel.py" --update
