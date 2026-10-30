# Enterprise Synapse-Hub Global Antigravity Plugin Installer (Windows)
# ======================================================================
# Mounts Synapse-Hub directly into Google Antigravity's Global Plugin Directory.
# Once installed, all 27 skills and 6 subagents are active across all projects automatically.

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path "$ScriptDir\.."

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "   SYNAPSE-HUB: ANTIGRAVITY GLOBAL PLUGIN 1-CLICK INSTALLER           " -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$PluginsDir = "$HOME\.gemini\config\plugins"
$TargetPluginDir = "$PluginsDir\synapse-hub"

if (-not (Test-Path $PluginsDir)) {
    Write-Host "[1/5] Creating Antigravity plugins directory: $PluginsDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $PluginsDir -Force | Out-Null
} else {
    Write-Host "[1/5] Antigravity plugins directory verified: $PluginsDir" -ForegroundColor Green
}

# Ensure clean target directory
if (-not (Test-Path $TargetPluginDir)) {
    Write-Host "[2/5] Creating plugin bundle directory: $TargetPluginDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TargetPluginDir -Force | Out-Null
} else {
    Write-Host "[2/5] Plugin bundle directory exists: $TargetPluginDir" -ForegroundColor Green
}

# 1. Copy plugin.json & README.md
Write-Host "[3/5] Copying plugin manifest (plugin.json)..." -ForegroundColor Yellow
Copy-Item "$RepoRoot\plugin.json" "$TargetPluginDir\plugin.json" -Force
if (Test-Path "$RepoRoot\README.md") {
    Copy-Item "$RepoRoot\README.md" "$TargetPluginDir\README.md" -Force
}

# 2. Setup skills and agents via NTFS Junctions (Instant, zero duplication)
Write-Host "[4/5] Linking skills, agents, and rules into Global Plugin..." -ForegroundColor Yellow

$SkillsLink = "$TargetPluginDir\skills"
$AgentsLink = "$TargetPluginDir\agents"
$ToolsLink = "$TargetPluginDir\tools"
$RulesDir = "$TargetPluginDir\rules"

# Skills Junction
if (Test-Path $SkillsLink) {
    (Get-Item $SkillsLink).Delete()
}
New-Item -ItemType Junction -Path $SkillsLink -Target "$RepoRoot\.agents\skills" | Out-Null
Write-Host "  • Linked skills  : $SkillsLink -> $RepoRoot\.agents\skills" -ForegroundColor Green

# Agents Junction
if (Test-Path $AgentsLink) {
    (Get-Item $AgentsLink).Delete()
}
New-Item -ItemType Junction -Path $AgentsLink -Target "$RepoRoot\.agents\agents" | Out-Null
Write-Host "  • Linked agents  : $AgentsLink -> $RepoRoot\.agents\agents" -ForegroundColor Green

# Tools Junction
if (Test-Path $ToolsLink) {
    (Get-Item $ToolsLink).Delete()
}
New-Item -ItemType Junction -Path $ToolsLink -Target "$RepoRoot\tools" | Out-Null
Write-Host "  • Linked tools   : $ToolsLink -> $RepoRoot\tools" -ForegroundColor Green

# Rules directory & AGENTS.md
if (-not (Test-Path $RulesDir)) {
    New-Item -ItemType Directory -Path $RulesDir -Force | Out-Null
}
Copy-Item "$RepoRoot\AGENTS.md" "$RulesDir\AGENTS.md" -Force
Write-Host "  • Deployed rules : $RulesDir\AGENTS.md" -ForegroundColor Green

# 3. Initialize SQLite Cache
Write-Host "`n[5/5] Initializing Central Agent Memory (SQLite Cache)..." -ForegroundColor Yellow
try {
    python "$RepoRoot\tools\cache_resolver.py" init
} catch {
    Write-Host "  (Notice: cache_resolver init will run when Python is invoked)" -ForegroundColor DarkGray
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  🎉 SUCCESS: Synapse-Hub is now installed as a GLOBAL PLUGIN!        " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "• Location : $TargetPluginDir" -ForegroundColor White
Write-Host "• Skills   : 27 Standardized QA Skills" -ForegroundColor White
Write-Host "• Agents   : 6 Swarm Subagent Profiles" -ForegroundColor White
Write-Host "`n👉 Antigravity will now automatically load Synapse-Hub across ALL projects" -ForegroundColor Yellow
Write-Host "   without needing to add Synapse-Hub as a workspace folder!" -ForegroundColor Yellow
Write-Host "======================================================================`n" -ForegroundColor Cyan
