# Enterprise Automation Failure Diagnostic & Healing Matrix

Reference documentation for the `failure-autopsy-and-healing` skill.

---

## 1. Diagnostic & Healing Matrix

| Visual / Exception Symptom | Root Cause | Groovy POM Healing Patch |
| :--- | :--- | :--- |
| **Save button `[ ✓ ]` disabled / dimmed** | Angular Reactive Form missed change detection or missing required field (`*`). | `WebElement el = findElement(By.cssSelector("input[formcontrolname='code']"))`<br>`jsSetInput(el, uniqueCode)` |
| **Alert: *"Phạm vi giữa các khu/cụm không hợp lệ"*** | OpenLayers polygon overlaps previously saved boundary data. | `Actions actions = new Actions(driver)`<br>`actions.moveToElement(viewport, -180, -80).click().perform()` |
| **`ElementClickInterceptedException`** | Modal overlay `.p-component-overlay` fading out but still blocking clicks. | `((JavascriptExecutor) driver).executeScript("arguments[0].click();", element)` |
| **Red Toast: *"Mã đã tồn tại"*** | Non-unique test data colliding with existing records. | `String code = BasePage.uniqueCode("CCN_")` |
| **`StaleElementReferenceException`** | Angular DOM re-rendered after API response, detaching element. | `for (int i = 0; i < 3; i++) { try { findElement(by).click(); break; } catch (StaleElementReferenceException e) { sleep(500) } }` |
| **`TimeoutException` (Waiting for table/button)** | Loading overlay `.p-blockui` or spinner `.p-progress-spinner` blocking UI. | `waitForElementNotVisible(By.cssSelector(".p-blockui, .p-progress-spinner"), 10)` |
| **PrimeNG Dropdown value not applied** | Clicked `p-dropdown` but overlay panel `.p-dropdown-panel` has not rendered. | `waitForElementVisible(By.cssSelector(".p-dropdown-panel"), 5)`<br>`findElement(By.xpath("//li[contains(., '" + text + "')]")).click()` |
| **Blank Screenshot** | Browser crashed before capturing UI (OOM or lost WebDriver session). | Inspect `console0.log`, kill zombie drivers (`pkill -f chromedriver`), restart session. |

---

## 2. Four Flaky Test Root Causes & Cures

| Flaky Root Cause | Symptom | Curing Strategy (Root Fix) |
|---|---|---|
| **1. Unstable Locator** | Random failures due to CSS refactoring or dynamic hashes | Enforce Master Priority Map: switch to `[formcontrolname]`, `[data-testid]`; forbid positional XPaths. |
| **2. Timing & Race Condition** | Fails under network latency; clicks before Angular finishes render | Replace all hard sleeps with Smart Wait: `waitForElementVisible`, wait for `.p-blockui` / `.p-progress-spinner` to hide. |
| **3. Test Data Conflict** | Fails on parallel or repeated runs due to duplicate codes | Enforce `BasePage.uniqueCode(prefix)` with epoch timestamps. |
| **4. Environment Dependency** | Fails due to expired session or stale browser cache | Use `LoginPage.ensureLoggedIn()` before every script. |

---

## 3. Fast-Fix Triad (Zero-Token Diagnostic & Targeted Healing Workflow)

To maximize fix speed and minimize token consumption without degrading test fidelity, follow this 3-step loop:

### Step 1: Zero-Token Pinpoint (CLI Log Extraction)
Never read entire JUnit XML reports (>50KB). Extract failed test cases, exception reasons, and file line numbers in <50 tokens:
```bash
python3 tools/pinpoint_failure.py Reports/<timestamp>/<suite>/JUnit_Report.xml
```

### Step 2: Instant Form & DOM Audit (Playwright MCP Recipe 15)
When a test fails because a button is disabled (e.g. Save `[ ✓ ]`), never guess which field is invalid. Execute Recipe 15 via `browser_run_code_unsafe` on the active live page:
```javascript
() => {
  const invalids = Array.from(document.querySelectorAll('form .ng-invalid, input.ng-invalid, p-dropdown.ng-invalid'));
  return invalids.map(el => ({
    tag: el.tagName,
    name: el.getAttribute('name') || el.getAttribute('formcontrolname') || el.id,
    classes: el.className
  }));
}
```
This instantly highlights missing required inputs, pattern mismatches, or invalid dropdowns.

### Step 3: Targeted Single-TC Re-test (Zero Waste)
Never rerun an entire Test Suite to verify a 1-line locator or timing fix. Rerun only the targeted test case:
```bash
# Via KRE CLI (License mode):
katalonc -noSplash -runMode=console -projectPath="." -retry=0 -testCasePath="Test Cases/TC-xxx" -browserType="Chrome (headless)"

# Or verify live flow in 2 seconds via Playwright MCP script.
```
