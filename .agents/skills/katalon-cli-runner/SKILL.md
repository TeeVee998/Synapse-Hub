---
name: katalon-cli-runner
description: "Execute headless Katalon and Gradle test runners with automatic driver cleanup."
---

# Katalon CLI & Enterprise Runner — Dual-Mode Execution Management

Specialized skill for managing, dispatching, and monitoring enterprise Katalon test runs across different licensing states (**Licensed Headless KRE** vs **Free Community Mode**), integrated with Allure reporting and automated driver cleanup.

---

## 1. Adaptive Dual-Mode Execution Strategy

| Licensing State | Recommended Mode | Response Time | Licensing Cost |
|---|---|:---:|:---:|
| **KRE License Available** | **Mode 1: Headless KRE CLI** (CI/CD or Terminal) | Batch-oriented | Licensed |
| **No License Available** | **Mode 2A: Katalon Studio GUI (Free Edition)** (Suite Acceptance) | 5–10 mins | **$0** |
| **No License Available** | **Mode 2B: Playwright Live Interaction** (Selector probing / logic check) | **< 200 ms** | **$0** |

---

## 2. Pre-Flight Quality Check

Before launching heavy CLI runs, execute fast pre-flight verification:
```bash
python3 -c "
import glob
for p in glob.glob('Keywords/**/*.groovy', recursive=True) + glob.glob('Scripts/**/*.groovy', recursive=True):
    with open(p, 'rb') as fp:
        assert fp.read(3) != b'\xef\xbb\xbf', f'BOM detected: {p}'
print('[PASS] Pre-flight passed: 100% UTF-8 No BOM')
"
```

---

## 3. License Recovery & Process Cleanup

1. **License Expiration Handling:** When `License quota exceeded` occurs, halt batch retries immediately and switch to Playwright live validation or local GUI.
2. **Zombie Chromedriver & Java Process Termination:**
   ```powershell
   # Windows process cleanup
   Get-Process -Name "chromedriver", "katalon" -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
   ```bash
   # Unix process cleanup
   pkill -f chromedriver || true
   pkill -f katalon || true
   ```

---

## 4. Standard Headless Execution Commands

```bash
# Execute specific Test Suite via KRE CLI in pure headless mode
katalonc -noSplash -runMode=console \
  -projectPath="$(pwd)/project.prj" \
  -retry=0 \
  -testSuitePath="Test Suites/TS_SmokeTest" \
  -browserType="Chrome (headless)" \
  -executionProfile="default" \
  -apiKey="$KATALON_API_KEY"
```

---

## 5. Definition of Done (DoD)

1. **Exit Code = 0:** Runner completes cleanly without runtime crash.
2. **Clean JUnit XML:** Results XML contains 0 `<failure>` or `<error>` tags.
3. **Compile Allure Report:** `allure generate ./allure-results -o ./Reports/allure-report --clean`.
4. If failures occur, immediately dispatch failure autopsy:
   ```bash
   python3 tools/pinpoint_failure.py
   ```
