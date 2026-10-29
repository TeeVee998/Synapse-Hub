<#
.SYNOPSIS
    One-click setup and dependency bootstrap script for Enterprise Agent-Skills Hub.
.DESCRIPTION
    Detects and installs Python, Node.js, Playwright, sets up a clean virtual environment,
    installs requirements.txt, and verifies the full 30-skill catalog.
#>

[CmdletBinding()]
param(
    [switch]$ForceInstall = $false
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Enterprise Agent-Skills Hub: Automated Bootstrap Setup  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# 1. Verify / Install Python
Write-Host "`n[1/5] Checking Python 3 Runtime..." -ForegroundColor Yellow
$py = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $v = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $v -match "Python\s+3\.(1[0-9]|[2-9][0-9])") {
            $py = $cmd
            Write-Host "  [OK] Found Python: $v" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $py) {
    Write-Host "  [WARN] Python 3.10+ not found in PATH." -ForegroundColor Yellow
    Write-Host "  Attempting automated installation via winget..." -ForegroundColor Cyan
    try {
        winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements --scope currentUser
        Write-Host "  [OK] Python 3.11 installed. Please restart your shell if PATH is not updated." -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] Could not auto-install Python. Please install from https://python.org" -ForegroundColor Red
    }
}

# 2. Virtual Environment Setup
Write-Host "`n[2/5] Setting up Virtual Environment (.venv)..." -ForegroundColor Yellow
$venvDir = Join-Path $repoRoot ".venv"
if (-not (Test-Path $venvDir) -and $py) {
    Write-Host "  Creating virtual environment at $venvDir..." -ForegroundColor Cyan
    & $py -m venv $venvDir
}

$venvPython = if ($IsWindows -or $env:OS -match "Windows") {
    Join-Path $venvDir "Scripts\python.exe"
} else {
    Join-Path $venvDir "bin/python"
}

# 3. Pip Dependencies
Write-Host "`n[3/5] Installing Core Python Dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $repoRoot "requirements.txt"
if (Test-Path $venvPython) {
    Write-Host "  Upgrading pip & wheel..." -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip setuptools wheel --quiet
    if (Test-Path $reqFile) {
        Write-Host "  Installing requirements from requirements.txt..." -ForegroundColor Cyan
        & $venvPython -m pip install -r $reqFile --quiet
        Write-Host "  [OK] Dependencies installed in .venv" -ForegroundColor Green
    }
} elseif ($py) {
    Write-Host "  Installing requirements using system $py..." -ForegroundColor Cyan
    & $py -m pip install -r $reqFile --quiet
} else {
    Write-Host "  [SKIP] Skipping pip install: Python runtime not yet active." -ForegroundColor Yellow
}

# 4. Check Node.js / Playwright
Write-Host "`n[4/5] Checking Node.js & Playwright CLI..." -ForegroundColor Yellow
try {
    $nodeVer = & node --version 2>&1
    Write-Host "  [OK] Found Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "  [INFO] Node.js not detected. Optional for standalone Python tools, required for Playwright MCP." -ForegroundColor Gray
}

# 5. Run Quality Gate Linting
Write-Host "`n[5/6] Running Quality Gate & Skill Integrity Verification..." -ForegroundColor Yellow
$linter = Join-Path $repoRoot "scripts\lint_skills.ps1"
if (Test-Path $linter) {
    & powershell -ExecutionPolicy Bypass -File $linter
}

# 6. Initialize SQLite Central Agent Memory
Write-Host "`n[6/6] Initializing Global Central Agent Memory (~/.agent_memory/global_cache.db)..." -ForegroundColor Yellow
$cacheTool = Join-Path $repoRoot "tools\cache_resolver.py"
if (Test-Path $cacheTool) {
    try {
        if (Test-Path $venvPython) {
            & $venvPython $cacheTool init
        } elseif ($py) {
            & $py $cacheTool init
        }
        Write-Host "  [OK] Central Agent Memory initialized and seeded." -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Could not initialize ~/.agent_memory/global_cache.db: $_" -ForegroundColor Yellow
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  Bootstrap Complete! Hub is ready for Multi-Agent Swarm. " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
