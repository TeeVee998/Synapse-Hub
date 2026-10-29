Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   ENTERPRISE AUTOMATION - ALLURE REPORT GENERATOR" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$projectDir = Split-Path -Parent $PSScriptRoot
$resultsDir = Join-Path $projectDir "allure-results"
$reportDir  = Join-Path $projectDir "allure-report"

if (-not (Test-Path $resultsDir)) {
    Write-Host "[!] Không tìm thấy thư mục: $resultsDir" -ForegroundColor Yellow
    Write-Host "[!] Hãy thực thi Test Suite trước để sinh dữ liệu kết quả." -ForegroundColor Yellow
    exit 0
}

# Kiểm tra Allure CLI
$allureCmd = Get-Command allure -ErrorAction SilentlyContinue

if ($allureCmd) {
    Write-Host "[+] Đang xuất báo cáo Allure HTML..." -ForegroundColor Green
    allure generate $resultsDir -o $reportDir --clean
    Write-Host "[+] Xuất báo cáo hoàn tất tại: $reportDir" -ForegroundColor Green
    Write-Host "[+] Đang mở báo cáo trên trình duyệt..." -ForegroundColor Cyan
    allure open $reportDir
} else {
    Write-Host "[!] Không tìm thấy công cụ Allure CLI trong hệ thống." -ForegroundColor Yellow
    Write-Host "[*] Hướng dẫn cài đặt nhanh:" -ForegroundColor White
    Write-Host "    Cách 1: npm install -g allure-commandline" -ForegroundColor Gray
    Write-Host "    Cách 2: scoop install allure" -ForegroundColor Gray
    Write-Host "    Cách 3: choco install allure-commandline" -ForegroundColor Gray
}