---
name: github-actions-templates
description: "Create production-ready GitHub Actions workflows for automated test suites and CI/CD."
---

# GitHub Actions CI/CD Patterns for Test Automation

> **Target:** Author secure, performant, and matrix-sharded GitHub Actions workflows for automated test execution, quality gate validation, and Allure reporting.

---

## 1. When to Use

- Configuring continuous integration pipelines for Playwright, Katalon, Pytest, or Newman.
- Setting up multi-OS and multi-version test execution matrices.
- Integrating automated Quality Gate DoD (`tools/verify_all.py`).
- Generating and publishing automated test report artifacts.

---

## 2. Standard Enterprise Test Workflow Template

Create in `.github/workflows/e2e_tests.yml`:

```yaml
name: Enterprise Automated E2E Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-matrix:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install Dependencies
        run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps chromium

      - name: Run Sharded Playwright Tests
        run: npx playwright test --shard=${{ matrix.shard }}

      - name: Upload Test Report & Screenshots
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-shard-${{ strategy.job-index }}
          path: playwright-report/
          retention-days: 14
```

---

## 3. Best Practices & Security Invariants

1. **Dependency Pinning:** Always pin third-party actions to full commit SHAs or major versions (`actions/checkout@v4`).
2. **Secret Masking:** Never hardcode credentials in workflow files; inject via `secrets.TEST_USER` and `secrets.TEST_PASS`.
3. **Artifact Retention:** Cap test video and screenshot artifacts to 7-14 days to prevent storage bloat.
4. **Concurrency Governance:** Cancel outdated in-flight runs on new PR commits using `concurrency: { group: ${{ github.ref }}, cancel-in-progress: true }`.
