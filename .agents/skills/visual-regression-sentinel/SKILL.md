---
name: visual-regression-sentinel
description: "Run pixel and layout shift visual regression checks with anti-flake masking."
---

# Visual Regression Sentinel Skill

> **Target:** Catch unintended UI rendering defects, CSS breakages, alignment shifts, and missing visual assets across viewports without manual visual inspection.

---

## 1. Core Principles

1. **Anti-Flakiness Masking:**
   - Always mask dynamic elements (timers, timestamps, random avatars, ads, blinking carets) before capturing baselines.
2. **Perceptual Diffing over Strict Pixel Match:**
   - Use SSIM (Structural Similarity Index) or perceptual threshold (`threshold: 0.2`) to tolerate minor antialiasing discrepancies between GPU rendering pipelines.
3. **Deterministic Viewports:**
   - Standardize viewport dimensions (`1920x1080` for Desktop, `390x844` for Mobile) and disable animations (`animations: 'disabled'`).

---

## 2. Standard Playwright Visual Assertion Patterns

### Pattern A: Full-Page Screenshot with Dynamic Masking
```typescript
await expect(page).toHaveScreenshot('landing-page.png', {
  fullPage: true,
  animations: 'disabled',
  mask: [
    page.locator('.dynamic-timestamp'),
    page.locator('.live-ticker-banner'),
    page.locator('[data-testid="unique-id-badge"]')
  ],
  maxDiffPixelRatio: 0.02 // Allow 2% tolerance
});
```

### Pattern B: Component-Level Snapshot
```typescript
// Isolate critical component to avoid cascade failures from header/footer changes
const dataTable = page.locator('.custom-data-table');
await expect(dataTable).toHaveScreenshot('table-component-default.png', {
  threshold: 0.1
});
```

### Pattern C: Color Mode / Responsive Variations
```typescript
// Test Dark Mode
await page.emulateMedia({ colorScheme: 'dark' });
await expect(page).toHaveScreenshot('dashboard-dark.png');
```

---

## 3. Visual Failure Autopsy Protocol
When visual regression fails:
1. Review generated diff image: `*-diff.png`.
2. Determine if it is a **Real Regression** (CSS bug, broken layout) or **Intentional Redesign**.
3. If intentional redesign: update baseline snapshots via `npx playwright test --update-snapshots`.
4. If bug: file bug report with side-by-side artifact comparison.
