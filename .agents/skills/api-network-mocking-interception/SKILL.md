---
name: api-network-mocking-interception
description: "Intercept HTTP/GraphQL traffic, stub routes, and simulate chaos network failures. Use when stubbing, mocking, or intercepting network calls during UI or API tests."
---

# API Network Mocking, Interception & Resilience Skill

> **Target:** Eliminate flaky tests caused by backend dependencies, slow microservices, or inconsistent staging data by intercepting browser-level network requests, and verify frontend resilience against network faults and degradations.

---

## 1. Core Principles

1. **Deterministic State over Staging Data:**
   - UI tests should verify front-end state rendering and user interactions, not whether the backend DB is seeded.
   - Use route interception (`page.route()`) to return predictable JSON contracts (success, 400 Bad Request, 500 Server Error).

2. **Zero Network Latency:**
   - Mock external telemetry, 3rd party analytics, fonts, and heavy media assets to speed up execution by 3x-5x.

3. **Fault Injection & Chaos Verification:**
   - Test UI resiliency against network timeouts, dropped connections, upstream gateway outages (502/503/504), and malformed schemas without altering real server code.
   - Guard against White Screen of Death (WSOD) when sudden network loss or circuit-breaking events occur.

---

## 2. Playwright Route Interception Standard Patterns

### Pattern A: Static JSON Response Stubbing
```typescript
// Stub user profile API
await page.route('**/api/v1/user/profile', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      id: 'USR_AUTO_99',
      username: 'qa_sentinel',
      roles: ['ADMIN_OPERATOR'],
      permissions: ['READ', 'WRITE', 'EXECUTE']
    })
  });
});
```

### Pattern B: Modifying Live Responses (HAR / Passthrough Mutation)
```typescript
// Intercept real response and inject edge-case field
await page.route('**/api/v1/reports', async (route) => {
  const response = await route.fetch();
  const json = await response.json();
  json.totalItems = 999999; // Test UI overflow / pagination edge case
  await route.fulfill({ response, json });
});
```

### Pattern C: Simulating Network Failures & Delays
```typescript
// Simulate 500 Internal Server Error
await page.route('**/api/v1/checkout', async (route) => {
  await route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ errorCode: 'ERR_PAYMENT_DOWN', message: 'Gateway unreachable' })
  });
});

// Simulate High Latency (Slow 3G)
await page.route('**/api/v1/heavy-list', async (route) => {
  await new Promise(res => setTimeout(res, 3000));
  await route.continue();
});
```

---

## 3. Chaos & Network Degradation Patterns

### Pattern D: Emulating Extreme Latency & Jitter via CDP
```typescript
const client = await page.context().newCDPSession(page);
await client.send('Network.emulateNetworkConditions', {
  offline: false,
  latency: 3500, // 3.5s roundtrip latency
  downloadThroughput: ((500 * 1024) / 8), // 500 kbps
  uploadThroughput: ((500 * 1024) / 8),
  connectionType: 'cellular3g',
});

await page.goto('/orders');
// Verify UI displays loading skeleton/spinner and submit button is disabled in-flight
const submitBtn = page.locator('button[type="submit"]');
if (await submitBtn.isVisible()) {
  await expect(submitBtn).toBeDisabled();
}
```

### Pattern E: Simulating Gateway Drops (502/503/504) & Circuit Breaker Recovery
```typescript
let attemptCount = 0;
await page.route('**/api/v1/orders/submit', async (route) => {
  attemptCount++;
  if (attemptCount <= 2) {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Upstream gateway overloaded' }),
    });
  } else {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, orderId: 'ORD_HEALED_99' }),
    });
  }
});
```

### Pattern F: Sudden Offline Disconnection & Reconnection
```typescript
// 1. Cut network abruptly
await context.setOffline(true);
await page.click('[data-testid="nav-reports"]').catch(() => {});

// 2. Assert Zero White Screen of Death (WSOD) & Offline alert
const bodyContent = await page.evaluate(() => document.body.innerText.trim());
expect(bodyContent.length, 'Page must not be blank').toBeGreaterThan(20);

// 3. Restore connectivity
await context.setOffline(false);
await page.reload();
await expect(page.locator('h1')).toBeVisible();
```

---

## 4. Best Practices Checklist
- [ ] Always declare routes **before** calling `page.goto()`.
- [ ] Use regex or glob patterns with caution; avoid intercepting Vite/Webpack bundling scripts.
- [ ] Critical forms must disable submit buttons during in-flight network transit to prevent duplicate requests.
- [ ] HTTP 502/503/504 errors must trigger user-friendly notifications, never raw JSON dumps or blank screens.
- [ ] For teardown, unroute specific patterns or reset context per test.
