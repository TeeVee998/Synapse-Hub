# PowerShell Script to ensure TestReports and summaryTemp.txt for CI/CD Dashboard
param(
    [string]$ProjectName = "Enterprise-Automation"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "=== [Centralize CI/CD] Generating TestReports & summaryTemp.txt for $ProjectName ===" -ForegroundColor Cyan

$testReportsDir = Join-Path $PSScriptRoot "..\TestReports"
$reportsDir = Join-Path $PSScriptRoot "..\Reports"

if (-not (Test-Path $testReportsDir)) {
    New-Item -ItemType Directory -Path $testReportsDir -Force | Out-Null
}

$passed = 0
$failures = 0
$errors = 0
$incomplete = 0
$skipped = 0
$foundExistingSummary = $false

# 0. Check if Cleanup_Browser already exported summaryTemp.txt with business test case counts
$existingSummaryFile = Join-Path $reportsDir "summaryTemp.txt"
if (-not (Test-Path $existingSummaryFile)) {
    $existingSummaryFile = Join-Path $testReportsDir "summaryTemp.txt"
}
if (Test-Path $existingSummaryFile) {
    try {
        $rawSummary = [System.IO.File]::ReadAllText($existingSummaryFile, [System.Text.Encoding]::UTF8)
        if ($rawSummary -match "(\d+)\s+Passed\s+-\s+.*?(\d+)\s+Failures\s+-\s+.*?(\d+)\s+Errors") {
            $passed = [int]$matches[1]
            $failures = [int]$matches[2]
            $errors = [int]$matches[3]
            if ($passed -gt 0) {
                $foundExistingSummary = $true
                Write-Host "[+] Found valid summaryTemp.txt from Cleanup_Browser: $rawSummary" -ForegroundColor Green
            }
        }
    } catch {}
}

# 1. Find the latest report directory (check Reports, then TestReports)
$latestReport = Get-ChildItem -Path @($reportsDir, $testReportsDir) -Recurse -Filter "*junit*.xml" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $foundExistingSummary -and $latestReport) {
    Write-Host "[+] Found latest JUnit report: $($latestReport.FullName)" -ForegroundColor Green
    try {
        [xml]$xml = Get-Content $latestReport.FullName
        if ($xml.testsuites) {
            $passed = [int]($xml.testsuites.passed)
            $failures = [int]($xml.testsuites.failures)
            $errors = [int]($xml.testsuites.errors)
            $incomplete = [int]($xml.testsuites.incompleted)
            $skipped = [int]($xml.testsuites.skipped)
        } elseif ($xml.testsuite) {
            $tests = [int]($xml.testsuite.tests)
            $failures = [int]($xml.testsuite.failures)
            $errors = [int]($xml.testsuite.errors)
            $skipped = [int]($xml.testsuite.skipped)
            $passed = [Math]::Max(0, $tests - $failures - $errors - $skipped)
        }
        $foundExistingSummary = $true
    } catch {
        Write-Warning "[!] Failed to parse XML: $_"
    }
}

if (-not $foundExistingSummary) {
    # Fallback to console0.log
    $latestLog = Get-ChildItem -Path @($reportsDir, $testReportsDir) -Recurse -Filter "console0.log" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($latestLog) {
        Write-Host "[+] Fallback: Parsing console log: $($latestLog.FullName)" -ForegroundColor Yellow
        $logContent = Get-Content $latestLog.FullName -Raw
        if ($logContent -match "Passed:\s*(\d+)\s*\|\s*Failed:\s*(\d+)\s*\|\s*Errors:\s*(\d+)") {
            $passed = [int]$matches[1]
            $failures = [int]$matches[2]
            $errors = [int]$matches[3]
        } elseif ($logContent -match "Tổng số:\s*(\d+)\s*\|\s*Đạt:\s*(\d+)\s*\|\s*Thất bại:\s*(\d+)\s*\|\s*Lỗi:\s*(\d+)") {
            $passed = [int]$matches[2]
            $failures = [int]$matches[3]
            $errors = [int]$matches[4]
        } else {
            $passed = ([regex]::Matches($logContent, "\[TEST_CASE\]\[PASSED\]")).Count
            $failures = ([regex]::Matches($logContent, "\[TEST_CASE\]\[FAILED\]")).Count
            $errors = ([regex]::Matches($logContent, "\[TEST_CASE\]\[ERROR\]")).Count
        }
    }
}

Write-Host "[+] Metrics: Passed=$passed, Failures=$failures, Errors=$errors, Incomplete=$incomplete, Skipped=$skipped" -ForegroundColor Cyan

# 2. Write summaryTemp.txt: \u2705 {P} Passed - \u274C {F} Failures - \u274C {E} Errors - \u2757 {I} Incomplete - \u26AA {S} Skipped
$summaryContent = "\u2705 $passed Passed - \u274C $failures Failures - \u274C $errors Errors - \u2757 $incomplete Incomplete - \u26AA $skipped Skipped"

$summaryFile = Join-Path $testReportsDir "summaryTemp.txt"
[System.IO.File]::WriteAllText($summaryFile, $summaryContent, [System.Text.Encoding]::ASCII)
Write-Host "[+] Created: $summaryFile" -ForegroundColor Green
Write-Host "    $summaryContent"

# Also write to Reports/summaryTemp.txt for fallback
if (Test-Path $reportsDir) {
    [System.IO.File]::WriteAllText((Join-Path $reportsDir "summaryTemp.txt"), $summaryContent, [System.Text.Encoding]::ASCII)
}

# 3. Synchronize report files into TestReports/<Project>_<timestamp>/ if Katalon saved to Reports/
if ($latestReport) {
    $reportParentDir = $latestReport.Directory.FullName
    $nowStr = Get-Date -Format "yyyyMMddHHmmss"
    if ($ProjectName -match "_\d{10,14}$") {
        $targetProjDir = Join-Path $testReportsDir $ProjectName
    } else {
        $targetProjDir = Join-Path $testReportsDir "${ProjectName}_$nowStr"
    }
    $targetSubDir = Join-Path $targetProjDir (Split-Path $reportParentDir -Leaf)

    if (-not (Test-Path $targetSubDir)) {
        New-Item -ItemType Directory -Path $targetSubDir -Force | Out-Null
    }

    Copy-Item -Path "$reportParentDir\*" -Destination $targetSubDir -Recurse -Force
    Write-Host "[+] Synced artifacts to: $targetSubDir" -ForegroundColor Green

    # Ensure results.html exists in targetProjDir
    $htmlFiles = Get-ChildItem -Path $targetSubDir -Filter "*.html"
    if ($htmlFiles.Count -gt 0) {
        Copy-Item -Path $htmlFiles[0].FullName -Destination (Join-Path $targetProjDir "results.html") -Force
        Write-Host "[+] Created results.html in: $targetProjDir" -ForegroundColor Green
    }
}

Write-Host "=== [Centralize CI/CD] Report Generation Complete ===" -ForegroundColor Cyan
