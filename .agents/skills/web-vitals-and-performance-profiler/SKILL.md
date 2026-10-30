---
name: web-vitals-and-performance-profiler
description: "Measure Core Web Vitals (LCP, CLS, INP) and network waterfalls via CDP."
---

# Web Vitals & Performance Profiler Skill

> **Target:** Detect user-experience bottlenecks, layout shifts, sluggish API responses, and render-blocking assets automatically during headless test execution.

---

## 1. Core Principles

1. **Performance as an Assertion:**
   - Functional tests must double as non-functional guardrails. If a critical workflow takes > 10 seconds to load, it should fail performance budgets.
2. **Google Core Web Vitals Metrics:**
   - **LCP (Largest Contentful Paint):** Target $\le 2.5\text{s}$ (Good).
   - **CLS (Cumulative Layout Shift):** Target $\le 0.1$ (Good).
   - **TTFB (Time to First Byte):** Target $\le 800\text{ms}$ (Good).
3. **Observation-Masked Telemetry:**
   - Never dump thousands of CDP trace lines into context. Only output calculated metric scores and flagged slow endpoints (> 1500ms).

---

## 2. Standard Playwright Performance Measurement

### Pattern A: Extracting Core Web Vitals via JavaScript Evaluation
```typescript
import { test, expect } from '@playwright/test';

test('audit core web vitals on dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  const performanceTiming = JSON.parse(
    await page.evaluate(() => JSON.stringify(window.performance.timing))
  );

  const ttfb = performanceTiming.responseStart - performanceTiming.navigationStart;
  const domLoadTime = performanceTiming.domContentLoadedEventEnd - performanceTiming.navigationStart;

  console.log(`[PERF] TTFB: ${ttfb}ms | DOM Load: ${domLoadTime}ms`);
  expect(ttfb).toBeLessThan(1500); // 1.5s threshold
});
```

### Pattern B: Tracking Slow Network Endpoints
```typescript
test('detect slow backend microservices', async ({ page }) => {
  const slowRequests: { url: string; duration: number }[] = [];

  page.on('response', (response) => {
    const timing = response.timing();
    const duration = timing.responseEnd;
    if (duration > 2000) {
      slowRequests.push({ url: response.url(), duration });
    }
  });

  await page.goto('/reports');
  await page.waitForLoadState('networkidle');

  expect(slowRequests).toHaveLength(0); // Fail if any endpoint took > 2s
});
```
