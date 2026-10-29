param(
    [string]$Mode = "katalon" # "katalon" or "playwright"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   ENTERPRISE AUTOMATION - E2E FLOW PROBER & XPATH CRAWLER" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$projectDir = Split-Path -Parent $PSScriptRoot

if ($Mode -eq "playwright") {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) { $pythonCmd = Get-Command py -ErrorAction SilentlyContinue }
    if ($pythonCmd) {
        Write-Host "[+] Khởi chạy crawler qua Playwright (real_e2e_runner.py)..." -ForegroundColor Green
        & $pythonCmd "$projectDir\real_e2e_runner.py" --probe
        exit 0
    } else {
        Write-Host "[!] Không tìm thấy Python trên máy host." -ForegroundColor Yellow
        Write-Host "[+] Tự động chuyển sang chế độ Katalon Native Runner..." -ForegroundColor Cyan
        $Mode = "katalon"
    }
}

if ($Mode -eq "katalon") {
    Write-Host "[+] Khởi chạy crawler qua Katalon Native Test Suite (PROBE_E2E_Flow)..." -ForegroundColor Green
    
    $katalonExec = $null
    $possiblePaths = @(
        $env:KATALON_HOME,
        "C:\Katalon_Studio_Engine\katalonc.exe",
        "C:\Katalon_Studio\katalon.exe"
    )
    foreach ($p in $possiblePaths) {
        if ($p -and (Test-Path $p)) {
            $katalonExec = $p
            break
        }
    }

    if ($katalonExec) {
        Write-Host "[+] Sử dụng Katalon Engine tại: $katalonExec" -ForegroundColor Cyan
        $prjPath = "$projectDir\project.prj"
        $suiteRelPath = "Test Suites/PROBE_E2E_Flow"
        
        $argsList = @(
            "-noSplash",
            "-runMode=console",
            "-projectPath=`"$prjPath`"",
            "-retry=0",
            "-testSuitePath=`"$suiteRelPath`"",
            "-browserType=`"Chrome`""
        )
        if ($env:KATALON_API_KEY) {
            $argsList += "-apiKey=`"$($env:KATALON_API_KEY)`""
        }
        
        & $katalonExec $argsList
    } else {
        Write-Host "`n[!] Để chạy bộ dò luồng tự động:" -ForegroundColor Yellow
        Write-Host "    1. Mở Katalon Studio -> Open Project tại thư mục dự án này" -ForegroundColor White
        Write-Host "    2. Chọn Test Suites -> 'PROBE_E2E_Flow' -> Bấm nút Run (Chrome)" -ForegroundColor White
        Write-Host "    3. Hoặc chạy lệnh trong Docker: docker-compose up" -ForegroundColor White
    }
}