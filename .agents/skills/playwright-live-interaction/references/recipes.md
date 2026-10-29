# Enterprise Playwright Code Recipes (20 Recipes)

All code recipes below execute directly via `browser_run_code_unsafe` with parameter `code: "async (page) => { ... }"`.

---

## Recipe 1: Authentication & Session Verification
```javascript
async (page) => {
  if (page.url().includes('/auth') || page.url().includes('/login')) {
    const user = process.env.APP_USERNAME || 'your_username';
    const pass = process.env.APP_PASSWORD || 'your_password';
    await page.locator('input[formcontrolname="username"]').fill(user);
    await page.locator('input[formcontrolname="password"]').fill(pass);
    await page.locator('button[type="submit"]').click();
    await page.waitForNavigation({ waitUntil: 'networkidle' });
  }
  return { currentUrl: page.url(), title: await page.title() };
}
```

## Recipe 2: Search, Filter & PrimeNG Table Verification (`p-table`)
```javascript
async (page) => {
  const searchInput = page.locator('input.p-inputtext[placeholder*="Tìm kiếm"], input[placeholder*="tên"], input[placeholder*="mã"]').first();
  await searchInput.fill('Hà Nội');
  await searchInput.press('Enter');
  await page.waitForTimeout(1000);

  const rowCount = await page.locator('p-table table tbody tr').count();
  const firstRowText = rowCount > 0 ? await page.locator('p-table table tbody tr').first().innerText() : '';
  return { rowCount, firstRowText };
}
```

## Recipe 3: PrimeNG Dropdown & MultiSelect (`p-dropdown`, `p-multiselect`)
```javascript
async (page) => {
  const dropdown = page.locator('p-dropdown[formcontrolname="status"], p-dropdown[name="status"]').first();
  await dropdown.click();
  await page.waitForTimeout(400);

  const option = page.locator('.p-dropdown-panel .p-dropdown-item').filter({ hasText: 'Đang hoạt động' }).first();
  await option.click();
  await page.waitForTimeout(300);

  return { selectedLabel: await dropdown.locator('.p-dropdown-label').innerText() };
}
```

## Recipe 4: Modal Dialogs & Popup Forms (`p-dialog`, `.card.popup-data`)
```javascript
async (page) => {
  await page.evaluate(() => {
    function setAngularInput(selector, val) {
      const el = document.querySelector(selector);
      if (el) {
        el.value = val;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
    const testCode = 'CCN_' + Math.floor(Date.now() / 1000);
    setAngularInput('input[formcontrolname="code"]', testCode);
    setAngularInput('input[formcontrolname="name"]', 'Cụm Công Nghiệp ' + testCode);
    setAngularInput('textarea[formcontrolname="address"]', 'Địa chỉ kiểm thử tự động');
  });

  const saveBtn = page.locator('button:has-text("Lưu"), button:has-text("Xác nhận"), button[title="Xác nhận"]').first();
  const isEnabled = !(await saveBtn.isDisabled());
  if (isEnabled) {
    await saveBtn.click();
    await page.waitForTimeout(1500);
  }
  return { isSaveButtonEnabled: isEnabled };
}
```

## Recipe 5: Confirm Dialog & Deletion (`p-confirmdialog`)
```javascript
async (page) => {
  await page.locator('p-table tbody tr button.p-button-danger, p-table tbody tr button[icon*="trash"]').first().click();
  await page.waitForTimeout(500);

  const confirmBtn = page.locator('.p-confirm-dialog-accept, button:has-text("Đồng ý"), button:has-text("Xóa")').first();
  await confirmBtn.click();
  await page.waitForTimeout(1000);

  const toastText = await page.locator('.p-toast-message-content').innerText().catch(() => 'No toast');
  return { toastText };
}
```

## Recipe 6: File Upload & Excel Import (`input[type="file"]`)
```javascript
async (page, customPath = 'Data Files/sample_import.xlsx') => {
  const fs = require('fs');
  const filePath = fs.existsSync(customPath) ? customPath : 'Data Files/sample_import.xlsx';
  await page.locator('input[type="file"]').setInputFiles(filePath);
  await page.waitForTimeout(1000);

  await page.locator('button:has-text("Tải lên"), button:has-text("Xác nhận")').first().click();
  await page.waitForTimeout(2000);
  return { status: "Uploaded", fileUsed: filePath };
}
```

## Recipe 7: OpenLayers GIS Canvas Interaction (`div.ol-viewport`)
```javascript
async (page) => {
  const canvas = page.locator('div.ol-viewport canvas').first();
  const box = await canvas.boundingBox();
  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;

  // Click polygon at non-overlapping offset (-180, -80)
  await page.mouse.click(cx - 180, cy - 80);
  await page.waitForTimeout(400);
  await page.mouse.click(cx - 150, cy - 80);
  await page.waitForTimeout(400);
  await page.mouse.click(cx - 150, cy - 50);
  await page.waitForTimeout(400);
  await page.mouse.dblclick(cx - 180, cy - 80);
  await page.waitForTimeout(1000);

  const result = await page.evaluate(() => {
    const error = document.querySelector('.text-danger, .invalid-feedback, editor-widget');
    return {
      hasError: !!error,
      errorText: error ? error.innerText : ''
    };
  });
  return result;
}
```

## Recipe 8: Advanced OpenLayers Map Inspection & VN2000 Coordinates
```javascript
async (page) => {
  return await page.evaluate(() => {
    const viewport = document.querySelector('div.ol-viewport');
    if (!viewport) return { error: "div.ol-viewport not found" };

    const map = viewport['__ol_map__'] || (window.map instanceof Object ? window.map : null);
    let mapInfo = {};
    if (map && map.getView) {
      const view = map.getView();
      mapInfo = {
        zoom: view.getZoom(),
        center: view.getCenter(),
        projection: view.getProjection() ? view.getProjection().getCode() : 'Unknown'
      };
    }
    const toolbarButtons = Array.from(document.querySelectorAll('.ol-control button, .map-toolbar button, .gis-tools button'))
      .map(b => ({ title: b.getAttribute('title') || b.innerText.trim(), className: b.className }));
    return { mapInfo, toolbarButtons };
  });
}
```

## Recipe 9: Two-Phase Search Workflow
```javascript
async (page) => {
  const searchToggleBtn = page.locator('button.p-button-icon-only[icon*="search"], button[title*="Tìm kiếm"], button:has-text("Tìm kiếm")').first();
  const searchInput = page.locator('input.p-inputtext[placeholder*="Tìm kiếm"], input[placeholder*="tên"], input[placeholder*="mã"]').first();

  if (!(await searchInput.isVisible())) {
    await searchToggleBtn.click();
    await page.waitForTimeout(300);
  }

  const keyword = 'CCN_TEST_2026';
  await searchInput.fill(keyword);
  await searchInput.press('Enter');
  await page.waitForTimeout(1000);

  const rowCount = await page.locator('p-table table tbody tr').count();
  const matched = rowCount > 0 && (await page.locator('p-table table tbody tr').first().innerText()).includes(keyword);
  return { rowCount, matched };
}
```

## Recipe 10: Intercepting PrimeNG Toasts (`p-toast`)
```javascript
async (page) => {
  const toastSelector = '.p-toast-message, .p-toast-message-content';
  try {
    const toast = await page.waitForSelector(toastSelector, { timeout: 4000 });
    const text = await toast.innerText();
    const isSuccess = (await toast.getAttribute('class') || '').includes('p-toast-message-success');
    return { success: true, text, isSuccess };
  } catch (e) {
    return { success: false, message: 'Toast did not appear or expired too quickly' };
  }
}
```

## Recipe 11: Record Deletion & Confirmation Dialog (`p-confirmdialog`)
```javascript
async (page, targetKeyword) => {
  const searchInput = page.locator('input.p-inputtext[placeholder*="Tìm kiếm"], input[placeholder*="tên"], input[placeholder*="mã"]').first();
  await searchInput.fill(targetKeyword);
  await searchInput.press('Enter');
  await page.waitForTimeout(1000);

  const deleteBtn = page.locator('p-table tbody tr:first-child button.p-button-danger, p-table tbody tr:first-child button[icon*="trash"]').first();
  await deleteBtn.click();
  await page.waitForTimeout(500);

  const confirmBtn = page.locator('.p-confirm-dialog-accept, .p-dialog-footer button:has-text("Xóa"), .p-dialog-footer button:has-text("Đồng ý"), button.p-button-danger:has-text("Xóa")').first();
  await confirmBtn.waitFor({ state: 'visible', timeout: 3000 });
  await confirmBtn.click();
  await page.waitForTimeout(1500);

  await searchInput.fill(targetKeyword);
  await searchInput.press('Enter');
  await page.waitForTimeout(1000);
  const remainingRows = await page.locator('p-table table tbody tr').count();
  const firstRowText = remainingRows > 0 ? await page.locator('p-table table tbody tr').first().innerText() : '';
  const isDeleted = remainingRows === 0 || !firstRowText.includes(targetKeyword) || firstRowText.includes('Không có dữ liệu');

  return { isDeleted, remainingRows, firstRowText };
}
```

## Recipe 12: PrimeNG Calendar Date Input (`p-calendar`)
```javascript
async (page) => {
  const dateValue = '25/10/2026';
  await page.evaluate(({ selector, val }) => {
    const calInput = document.querySelector(selector);
    if (calInput) {
      calInput.value = val;
      calInput.dispatchEvent(new Event('input', { bubbles: true }));
      calInput.dispatchEvent(new Event('change', { bubbles: true }));
      calInput.dispatchEvent(new Event('blur', { bubbles: true }));
    }
  }, { selector: 'p-calendar input, input[formcontrolname*="date"], input[formcontrolname*="Date"]', val: dateValue });

  await page.waitForTimeout(300);
  return { status: 'Date filled', value: dateValue };
}
```

## Recipe 13: PrimeNG MultiSelect Dropdown (`p-multiselect`)
```javascript
async (page, optionsToSelect = ['Công nghiệp chế biến', 'Điện lực']) => {
  const multiSelect = page.locator('p-multiselect').first();
  await multiSelect.click();
  await page.waitForSelector('.p-multiselect-panel', { state: 'visible', timeout: 3000 });
  await page.waitForTimeout(300);

  for (const optText of optionsToSelect) {
    const item = page.locator('.p-multiselect-item').filter({ hasText: optText }).first();
    if (await item.isVisible()) {
      await item.click();
      await page.waitForTimeout(200);
    }
  }

  const closeBtn = page.locator('.p-multiselect-close').first();
  if (await closeBtn.isVisible()) {
    await closeBtn.click();
  } else {
    await page.keyboard.press('Escape');
  }
  await page.waitForTimeout(300);
  return { selected: optionsToSelect };
}
```

## Recipe 14: Handling Stale Elements & Angular DOM Re-render Retries
```javascript
async (page, actionFn) => {
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await actionFn(page);
    } catch (err) {
      if (err.message.includes('Element is not attached to the DOM') || err.message.includes('stale') || attempt === maxRetries) {
        if (attempt === maxRetries) throw err;
        await page.waitForTimeout(500 * attempt);
      } else {
        throw err;
      }
    }
  }
}
```


## Recipe 15: Instant Angular Form Audit (Diagnose Disabled Save Button)
```javascript
async (page) => {
  return await page.evaluate(() => {
    const invalidInputs = Array.from(document.querySelectorAll('form .ng-invalid, input.ng-invalid, p-dropdown.ng-invalid, textarea.ng-invalid'));
    return invalidInputs.map(el => ({
      tag: el.tagName.toLowerCase(),
      control: el.getAttribute('formcontrolname') || el.getAttribute('name') || el.id || 'unnamed',
      placeholder: el.getAttribute('placeholder') || '',
      currentValue: el.value || el.innerText.trim()
    }));
  });
}
```

## Recipe 16: Smart Action Batching (Atomic Execution with Pause-on-Failure)
```javascript
async (page) => {
  return await page.evaluate(() => {
    const steps = [
      { name: 'fill_code', fn: () => { const el = document.querySelector("input[formcontrolname='code']"); el.value = 'CCN_TEST'; el.dispatchEvent(new Event('input', {bubbles: true})); } },
      { name: 'fill_name', fn: () => { const el = document.querySelector("input[formcontrolname='name']"); el.value = 'Cụm CN Test'; el.dispatchEvent(new Event('input', {bubbles: true})); } },
      { name: 'submit', fn: () => { document.querySelector("button[type='submit']").click(); } }
    ];

    for (let i = 0; i < steps.length; i++) {
      try {
        steps[i].fn();
      } catch (err) {
        return { status: 'FAILED', failedStep: i + 1, name: steps[i].name, error: err.message, url: location.href };
      }
    }
    return { status: 'SUCCESS', totalSteps: steps.length };
  });
}
```

## Recipe 17: Runtime Helper Injection (`window.__qa`)
```javascript
async (page) => {
  // Injects the centralized browser helper tools/browser_helpers.js
  const fs = require('fs');
  const helperCode = fs.readFileSync('tools/browser_helpers.js', 'utf8');
  await page.evaluate(helperCode);
  return await page.evaluate(() => ({
    version: window.__qa.__version,
    auditResults: window.__qa.audit()
  }));
}
```

## Recipe 18: Self-Healing Locator Fallback (`window.__qa.heal`)
```javascript
async (page, brokenXPath, expectedText) => {
  return await page.evaluate(({ xpath, text }) => {
    if (window.__qa) {
      return window.__qa.heal(xpath, text);
    }
    // Fallback search
    const buttons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes(text));
    return {
      candidates: buttons.map(b => `//button[contains(normalize-space(.), '${b.innerText.trim()}')]`)
    };
  }, { xpath: brokenXPath, text: expectedText });
}
```

## Recipe 19: Overlay-Proof Safe Click (`window.__qa.clickSafe`)
```javascript
async (page, selector) => {
  return await page.evaluate((sel) => {
    if (window.__qa) {
      return window.__qa.clickSafe(sel);
    }
    const el = document.querySelector(sel);
    if (!el) return false;
    document.querySelectorAll('.p-component-overlay').forEach(o => o.style.pointerEvents = 'none');
    el.click();
    return true;
  }, selector);
}
```

## Recipe 20: OpenLayers GIS Canvas Coordinate Inspector (`window.__qa.gisHUD`)
```javascript
async (page) => {
  return await page.evaluate(() => {
    if (window.__qa) {
      return window.__qa.gisHUD();
    }
    const vp = document.querySelector('.ol-viewport');
    if (!vp) return { status: 'NO_MAP' };
    const r = vp.getBoundingClientRect();
    return { width: r.width, height: r.height, safeCenter: { x: r.width / 2, y: r.height / 2 } };
  });
}
```
