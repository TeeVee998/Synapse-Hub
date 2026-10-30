---
name: custom-security-headers-audit
description: Audits web endpoints for mandatory HTTP security headers (CSP, HSTS, X-Content-Type-Options) with compliance grading.
version: 1.0.0
category: verification_and_resilience
---

# Custom Security Headers Audit Skill

## Overview
Evaluates target web applications and API gateways against OWASP ASVS v4.0 Section 14 (Configuration) security header requirements.

## Key Capabilities
- Evaluates Content-Security-Policy (CSP) strength.
- Verifies Strict-Transport-Security (HSTS) with preloading.
- Asserts presence of `X-Content-Type-Options: nosniff`.
- Asserts presence of `X-Frame-Options: DENY` or `SAMEORIGIN`.
- Checks Referrer-Policy and Permissions-Policy.

## Usage
Execute the bundled audit tool against an endpoint or mock response headers:

```bash
python tools/custom_security_headers.py --headers examples/audit_fixture.json --report report.json
```

## Evidence & Verification
- Emits structured JSON and Markdown audit reports with CVSS severity rankings.
- Zero external runtime dependencies (relies purely on standard library).
