---
name: security-dast-sentinel
description: "Run dynamic security audits: OWASP Top 10, security headers, IDOR, and token leakage. Use when running or planning DAST and security scans against a target app."
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

---

## 5. Passive vs Active Scan Taxonomy & Severity Levels

> *Borrowed and adapted from the OWASP ZAP scanning model (Apache-2.0, zaproxy/zaproxy).*

Structure every DAST engagement in two phases, and severity-tag every finding
so CI can gate on risk instead of raw counts:

| Phase | Traffic | Purpose | Hub Tooling |
| :--- | :--- | :--- | :--- |
| **Passive** | Zero traffic | Audit the OpenAPI/Swagger contract pre-flight: mutating endpoints without declared auth, unprotected admin paths, unbounded string props | `agent-qa fuzz-api --mode passive` |
| **Active** | Controlled attacks | Dispatch fuzz vectors against staging and evaluate the defect oracle | `agent-qa fuzz-api` (allowlist-guarded) |

Severity ladder (fixed mapping): `CRITICAL` (stacktrace/DB leak, auth bypass) →
`HIGH` (server crash 5xx, unprotected sensitive path) → `MEDIUM` (connection
errors, unverified targets) → `LOW` (SLA breaches, unbounded input) → `INFO`.

Rules:
1. **Never skip passive** — a contract that leaks an admin route costs zero
   requests to find; active scan only after passive findings are triaged.
2. **Gate on CRITICAL alone** — a run with any CRITICAL alarm fails CI
   regardless of total counts.
3. **An untested endpoint must never PASS** — connection failures are
   `CONNECTION_ERROR` findings, not green results (Truth Anchor).
4. **OpenAPI-driven breadth** — ingest the spec (JSON) so every path/method is
   enumerated; combine with authentication scripts from
   `auth-session-and-cookie-manager` before active scanning.
