---
name: wcag-audit-patterns
description: "Audit WCAG 2.2 accessibility (A/AA), keyboard navigation, and ARIA roles. Use when auditing accessibility against WCAG 2.2 A/AA criteria."
---

# WCAG 2.2 Accessibility Audit Patterns

Engineering standards for automated, continuous Web Content Accessibility Guidelines (WCAG 2.2 Level A and AA) auditing across enterprise web applications.

---

## 1. Core WCAG 2.2 Success Criteria Matrix

| Criterion | Rule Code | Requirement & Automated Assertion |
| :--- | :--- | :--- |
| **Non-text Content** | WCAG 1.1.1 | All `<img>` tags must possess non-empty `alt` attributes or `aria-hidden="true"` if decorative. |
| **Info and Relationships**| WCAG 1.3.1 | Form controls `<input>`, `<select>` must link to `<label>` via `id/for` or `aria-label`. |
| **Heading Structure** | WCAG 1.3.1 | Headings must not skip levels (e.g. `<h1>` followed immediately by `<h3>`). |
| **Contrast (Minimum)** | WCAG 1.4.3 | Normal text contrast ratio $\ge 4.5:1$; Large text ($\ge 18\text{pt}$ or bold $14\text{pt}$) $\ge 3:1$. |
| **Keyboard Navigable** | WCAG 2.1.1 | All interactive elements must be focusable via `Tab` with visible focus indicators. |
| **No Keyboard Trap** | WCAG 2.1.2 | Focus must not become permanently trapped in modal dialogs; `Esc` key must exit. |
| **Target Size (Minimum)**| WCAG 2.5.8 | Interactive targets must meet $24 \times 24\text{px}$ minimum clickable area (WCAG 2.2 new). |

---

## 2. Playwright Automated Accessibility Testing Patterns

### Pattern A: Integrating `@axe-core/playwright` for Comprehensive Audits
```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('verify WCAG 2.2 Level AA compliance on dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .exclude('.legacy-third-party-widget') // Explicitly scoped exclusion
    .analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
});
```

### Pattern B: Modal Keyboard Focus Trap and Escape Verification
```typescript
test('modal dialog traps keyboard focus and closes on Escape', async ({ page }) => {
  await page.goto('/settings');
  await page.getByRole('button', { name: 'Edit Profile' }).click();

  const modal = page.getByRole('dialog', { name: 'Edit Profile' });
  await expect(modal).toBeVisible();

  // Verify focus shifts into modal
  await expect(modal.getByRole('textbox', { name: 'Username' })).toBeFocused();

  // Press Escape and verify focus returns to trigger
  await page.keyboard.press('Escape');
  await expect(modal).toBeHidden();
  await expect(page.getByRole('button', { name: 'Edit Profile' })).toBeFocused();
});
```

---

## 3. Automated CLI Auditing via Tooling

Agent can automatically audit accessibility for any HTML file or live page URL via `tools/wcag_audit.py`:

```bash
# Audit a local HTML snapshot
python3 ~/.zcode/synapse-hub/tools/wcag_audit.py path/to/page.html -o docs/wcag_audit_report.md

# Audit a live application URL directly
python3 ~/.zcode/synapse-hub/tools/wcag_audit.py https://staging.example.com --url -o docs/wcag_audit_report.md
```
