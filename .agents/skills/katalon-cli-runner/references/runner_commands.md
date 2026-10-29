# CLI Runner Commands & Enterprise Test Suites Registry

Reference documentation for the `katalon-cli-runner` skill.

---

## 1. Environment Variable Configuration (.env)
```bash
KATALON_API_KEY="your_actual_api_key_here"
KATALON_PROJECT_PATH="/path/to/project"
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_CHAT_ID="your_chat_id"
```

---

## 2. Platform-Specific Execution Commands (KRE CLI)

### 2.1. Windows Environment (PowerShell Runner)
```powershell
# Run Test Suite with API Key
powershell -ExecutionPolicy Bypass -File .\run_tests_windows.ps1 -Suite "Test Suites/07_QuanTriDuLieu" -ApiKey $env:KATALON_API_KEY

# Run single Test Suite for debugging:
powershell -ExecutionPolicy Bypass -File .\run_tests_windows.ps1 -Suite "Test Suites/Group_07_01_CumCongNghiep"
```

### 2.2. macOS / Linux CLI (Headless Full HD)
```bash
# Run Test Suite
katalonc \
  -noSplash \
  -runMode=console \
  -projectPath="$(pwd)/project.prj" \
  -retry=0 \
  -testSuitePath="Test Suites/07_QuanTriDuLieu" \
  -browserType="Chrome (headless)" \
  -executionProfile="default" \
  -apiKey="$KATALON_API_KEY" \
  --args="-headless --window-size=1920,1080 --disable-gpu --no-sandbox --disable-dev-shm-usage"

# Run single Test Case (Debug Mode):
katalonc \
  -noSplash \
  -runMode=console \
  -projectPath="$(pwd)/project.prj" \
  -testCasePath="Test Cases/TC-1 Kiểm tra tạo mới thành công" \
  -browserType="Chrome (headless)" \
  -apiKey="$KATALON_API_KEY"
```

---

## 3. Standard Enterprise Test Suite Registry

| Test Suite Name | Scale | Target Functional Module |
| :--- | :---: | :--- |
| `Test Suites/All_Tests` | Full Suite | All functional modules |
| `Test Suites/01_QuanLyChiTieu` | 7 TCs | Target Planning |
| `Test Suites/02_XacThucNguoiDung` | 5 TCs | User Authentication & Profiles |
| `Test Suites/03_QuanTriHeThong` | 4 TCs | System Administration & Users |
| `Test Suites/04_DanhMucDungChung` | 12 TCs | Common Categories (Departments, Roles) |
| `Test Suites/05_DanhMucNganhCongThuong` | 64 TCs | 16 Industry Sub-Categories |
| `Test Suites/06_QuyHoachCongThuong` | 30 TCs | Sector Planning |
| `Test Suites/07_QuanTriDuLieu` | 125 TCs | Data Mining & GIS Maps |
| `Test Suites/08_BaoCaoThongKe` | 2 TCs | Statistical Reports (Data & Permits) |
| `Test Suites/09_ChiaSeDuLieu` | 10 TCs | Data Sharing & API Token Lifecycle |
