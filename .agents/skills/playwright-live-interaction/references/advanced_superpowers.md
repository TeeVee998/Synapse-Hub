# 5 Advanced Superpowers & 5 AI Paradigms for Playwright Live Interaction

In-depth technical reference for complex testing scenarios across enterprise web test suites.

---

## 1. Five Native Advanced Superpowers

### 1.1. Zero-Second Auth (Bypass Login Form)
```javascript
// Step 1: Save storage state after login
async (page) => {
  await page.context().storageState({ path: '.agents/session.json' });
  return { status: "Session saved successfully" };
}

// Step 2: Load stored session in subsequent contexts
const context = await browser.newContext({ storageState: '.agents/session.json' });
```

### 1.2. Network Interception & Direct Seeding
```javascript
async (page) => {
  page.on('request', request => {
    if (request.url().includes('/api/') && request.method() === 'POST') {
      console.log('API URL:', request.url());
      console.log('Headers:', request.headers());
      console.log('Payload:', request.postData());
    }
  });
}
```

### 1.3. Accessibility Tree (AOM Snapshot — 90% Token Reduction)
```javascript
async (page) => {
  const a11yTree = await page.accessibility.snapshot({
    interestingOnly: true // Captures interactive elements only
  });
  return a11yTree;
}
```

### 1.4. Multi-Context Dual Role Testing (Parallel Roles)
```javascript
async (browser) => {
  const specialistContext = await browser.newContext();
  const leaderContext = await browser.newContext();

  const pageSpecialist = await specialistContext.newPage();
  const pageLeader = await leaderContext.newPage();

  // Specialist submits dossier
  await pageSpecialist.goto('https://app.example.com/planning');
  // Leader reviews and approves
  await pageLeader.goto('https://app.example.com/planning-approval');
}
```

### 1.5. API Route Mocking (Negative Scenarios & Fault Injection)
```javascript
async (page) => {
  await page.route('**/api/**', route => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Database connection failed!' })
    });
  });

  await page.locator('button:has-text("Lưu")').click();
  await page.waitForTimeout(500);
  const toastMsg = await page.locator('.p-toast-message').innerText();
  return { toastMsg };
}
```

---

## 2. Five AI Engineering Paradigms

### 2.1. Self-Healing Locator Engine (Multi-Tier Fallback)
```javascript
async (page, targetName) => {
  const strategies = [
    () => page.locator(`button[formcontrolname="${targetName}"]`),
    () => page.getByRole('button', { name: targetName }),
    () => page.locator(`button:has-text("${targetName}")`),
    () => page.locator(`button[title*="${targetName}"]`),
    () => page.locator(`.p-button:has-text("${targetName}")`)
  ];

  for (const getLocator of strategies) {
    const loc = getLocator();
    if (await loc.count() > 0 && await loc.first().isVisible()) {
      return loc.first(); // Self-healed successfully
    }
  }
  throw new Error(`Self-healing failed: Element not found: ${targetName}`);
}
```

### 2.2. Multimodal Visual Verification (GIS & Layout)
```javascript
async (page) => {
  const mapElement = page.locator('div.ol-viewport');
  const screenshotBuffer = await mapElement.screenshot({ path: '.agents/screenshots/gis_canvas_live.png' });
  const box = await mapElement.boundingBox();
  return {
    isRenderedProperly: box && box.width > 300 && box.height > 200,
    width: box ? box.width : 0,
    height: box ? box.height : 0,
    screenshotPath: '.agents/screenshots/gis_canvas_live.png'
  };
}
```

### 2.3. Autonomous Exploratory Fuzzing (Edge & Crash Hunting)
```javascript
async (page) => {
  const edgePayloads = [
    "'-DROP TABLE--",
    "<script>alert(1)</script>",
    "-99999999",
    "   ",
    "A".repeat(500)
  ];
  const results = [];
  const input = page.locator('input[formcontrolname="code"]').first();

  for (const payload of edgePayloads) {
    await input.fill(payload);
    await page.locator('button:has-text("Lưu"), button:has-text("Xác nhận")').first().click();
    await page.waitForTimeout(600);

    const hasCrash = await page.evaluate(() => {
      const text = document.body.innerText;
      return text.includes('500 Internal') || text.includes('HttpErrorResponse');
    });
    results.push({ payload, hasCrash });
  }
  return results;
}
```

### 2.4. CDP Deep Profiling (RAM & Heap Monitoring)
```javascript
async (page) => {
  const memoryInfo = await page.evaluate(() => {
    return window.performance && window.performance.memory ? {
      usedJSHeapSizeMB: (window.performance.memory.usedJSHeapSize / (1024 * 1024)).toFixed(2),
      totalJSHeapSizeMB: (window.performance.memory.totalJSHeapSize / (1024 * 1024)).toFixed(2)
    } : { note: "Memory API only available in Chromium" };
  });
  return memoryInfo;
}
```

### 2.5. Multi-Agent Swarm Orchestration
For swarm roles (Lead Orchestrator, Live Explorer, Code Crafter, Test Runner, Quality Gatekeeper, Scribe), refer to [swarm_orchestration.md](swarm_orchestration.md).
