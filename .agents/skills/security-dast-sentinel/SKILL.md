---
name: security-dast-sentinel
description: "Run dynamic security audits: OWASP Top 10, security headers, IDOR, and token leakage."
---

# Security DAST Sentinel (Dynamic Application Security & OWASP Top 10)

> **Purpose:** Automated Dynamic Application Security Testing (DAST) and defensive runtime verification across enterprise web applications and APIs. Bridges functional automated testing with OWASP Top 10 compliance gates.
>
> [!IMPORTANT] Authorization & Scope of Engagement
> Dynamic security testing and fuzzing must **ONLY** be conducted against environments, domains, and applications for which explicit written authorization and testing agreements are established. Never direct automated security payloads or fuzzers against third-party production infrastructure.

---

## 1. Core Defensive Scope & OWASP Top 10

| OWASP Category | Threat Vector | Automated Defensive Check | Assertion Target |
| :--- | :--- | :--- | :--- |
| **A01: Broken Access Control** | BOLA / IDOR | Swapping User A token into User B resource URI | HTTP `403` or `404` (Never `200`) |
| **A01: Broken Access Control** | CORS Misconfiguration | Sending untrusted `Origin` with `Credentials: include` | Must NOT reflect origin with `Credentials: true` |
| **A02: Cryptographic Failures** | Missing HSTS | Inspecting headers on HTTPS endpoints | `Strict-Transport-Security: max-age=...` |
| **A05: Security Misconfiguration** | Missing Security Headers | Passive audit on page navigations & API responses | CSP, X-Frame-Options, nosniff |
| **A05: Security Misconfiguration** | Verbose Error Disclosure | Fuzzing invalid inputs to trigger errors | Response must NOT contain `SQLException` or stacktrace |
| **A09: Logging & Secrets Leak** | Sensitive Data Leakage | Regex scan on responses and local storage | Zero plaintext passwords, API keys, or private keys |

---

## 2. Automated Security Headers Audit (Playwright TypeScript)

```typescript
import { test, expect } from '@playwright/test';

test('DAST: Verify mandatory HTTP security headers', async ({ page }) => {
  const response = await page.goto('/dashboard');
  expect(response).not.toBeNull();
  const headers = response!.headers();

  // 1. Clickjacking & MIME Sniffing
  expect(['DENY', 'SAMEORIGIN']).toContain(headers['x-frame-options']?.toUpperCase());
  expect(headers['x-content-type-options']).toBe('nosniff');

  // 2. Strict Transport Security & CSP
  if (page.url().startsWith('https://')) {
    expect(headers['strict-transport-security']).toContain('max-age=');
  }
  expect(headers['content-security-policy']).toBeTruthy();
});
```

---

## 3. BOLA / IDOR Defense Check

```typescript
test('DAST: Tenant B cannot access Tenant A entity', async ({ request }) => {
  // Tenant B attempts to read Tenant A resource
  const readAttempt = await request.get('/api/v1/invoices/10042', {
    headers: { 'Authorization': `Bearer ${tokenTenantB}` }
  });
  expect([403, 404], 'Cross-tenant resource must be forbidden').toContain(readAttempt.status());
});
```

---

## 4. Environment Allowlist Guard

- Automated security checks, fuzzing (`tools/api_fuzzer.py`), and DB sandboxing (`tools/db_sandbox.py`) enforce non-production allowlists (`localhost`, `staging`, `dev`, `qa`, `sandbox`).
- Fuzzing production hosts without `SYNAPSE_ALLOW_PROD_FUZZ=1` is automatically blocked.
