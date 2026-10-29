---
name: auth-session-and-cookie-manager
description: Manage browser authentication sessions, JWT tokens, storageState, and multi-user roles for zero-second logins. Use on-demand when tests require authentication bypass or multi-role workflows.
---

# Auth Session & Cookie Manager Skill

> **Target:** Eliminate repetitive, slow UI login forms by saving, refreshing, and injecting browser storage states, cookies, and JWT bearer tokens directly into execution contexts.

---

## 1. Core Principles

1. **Zero-Second Auth Protocol:**
   - Execute UI authentication once to produce a verified `session.json` / `storageState.json`.
   - All subsequent test cases inject this saved state directly at context initialization.
2. **Multi-Role Context Isolation:**
   - Maintain distinct session fixtures for different privilege tiers (e.g. `admin_state.json`, `reviewer_state.json`, `viewer_state.json`).
3. **Session Freshness & Auto-Refresh:**
   - Inspect token expiry timestamp (`exp` in JWT payload); auto-refresh via API endpoint if token lifetime has elapsed.

---

## 2. Standard Playwright Implementation Patterns

### Pattern A: Generating and Reusing Storage State
```typescript
// 1. One-time Setup fixture (e.g. auth.setup.ts)
import { test as setup, expect } from '@playwright/test';

const adminFile = '.auth/admin_state.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', process.env.ADMIN_USER!);
  await page.fill('#password', process.env.ADMIN_PASS!);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard');
  
  await page.context().storageState({ path: adminFile });
});
```

### Pattern B: Injecting Session Directly (Zero-Second Login)
```typescript
// Reusing authenticated session without loading login form
import { test } from '@playwright/test';

test.use({ storageState: '.auth/admin_state.json' });

test('access protected admin table directly', async ({ page }) => {
  await page.goto('/admin/users'); // Opens already logged in
  // Continue immediately with business actions
});
```

### Pattern C: Multi-Context Dual Role Testing (Maker vs Checker)
```typescript
test('dual-role transaction approval', async ({ browser }) => {
  // Context 1: Staff creates proposal
  const staffContext = await browser.newContext({ storageState: '.auth/staff_state.json' });
  const staffPage = await staffContext.newPage();
  await staffPage.goto('/proposals/new');
  // ... submit proposal ...

  // Context 2: Manager reviews and approves
  const managerContext = await browser.newContext({ storageState: '.auth/manager_state.json' });
  const managerPage = await managerContext.newPage();
  await managerPage.goto('/proposals/pending');
  // ... approve proposal ...
});
```
