<#
.SYNOPSIS
    Automated validation test for all skills in Agent-Skills Hub.
.DESCRIPTION
    Checks presence of SKILL.md, valid frontmatter (name, description), and verifies skills_manifest.json.
#>

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         Agent-Skills Quality & Integrity Linter          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$skillsDir = Join-Path $PSScriptRoot "..\.agents\skills"
$manifestPath = Join-Path $PSScriptRoot "..\skills_manifest.json"

$passed = 0
$failed = 0

if (-not (Test-Path $manifestPath)) {
    Write-Host "[FAIL] Missing skills_manifest.json!" -ForegroundColor Red
    exit 1
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
Write-Host "[INFO] Manifest loaded: $($manifest.totalSkills) declared skills." -ForegroundColor Gray

$skillDirs = Get-ChildItem -Path $skillsDir -Directory

foreach ($dir in $skillDirs) {
    $skillMd = Join-Path $dir.FullName "SKILL.md"
    if (-not (Test-Path $skillMd)) {
        Write-Host "[FAIL] $($dir.Name): Missing SKILL.md" -ForegroundColor Red
        $failed++
        continue
    }

    $content = Get-Content $skillMd -Raw
    $hasName = $content -match "name:\s*[\w\-\s]+"
    $hasDesc = $content -match "description:\s*.+"

    if ($hasName -and $hasDesc) {
        Write-Host "[PASS] $($dir.Name) - Valid Frontmatter" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "[FAIL] $($dir.Name) - Invalid or missing YAML frontmatter" -ForegroundColor Red
        $failed++
    }
}

Write-Host "----------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Verification Results: $passed Passed, $failed Failed." -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "----------------------------------------------------------" -ForegroundColor Cyan

if ($failed -gt 0) {
    exit 1
} else {
    exit 0
}
