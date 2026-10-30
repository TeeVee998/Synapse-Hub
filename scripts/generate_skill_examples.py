#!/usr/bin/env python3
"""
Generates standard examples/ directory and realistic fixtures for all skills (Task B3).
"""

import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SKILLS_DIR = os.path.join(REPO_ROOT, ".agents", "skills")

EXAMPLES_MAP = {
    'agent-orchestration-multi-agent-optimize': ('swarm_workload_config.json', json.dumps({
        'swarm': 'LeadQAOrchestrator',
        'subagents': ['live-explorer', 'pom-crafter', 'test-runner', 'failure-analyst', 'quality-gatekeeper'],
        'tokenBudgetPerAgent': 1200,
        'concurrency': 3
    }, indent=2)),
    'antigravity-test-sentinel': ('dod_gate_policy.json', json.dumps({
        'policyName': 'Enterprise-DoD-Gate-0-to-8',
        'enforceGates': ['Gate-0-Integrity', 'Gate-1-UTF8-NoBOM', 'Gate-3-CleanPOM', 'Gate-7-InferLinter', 'Gate-8-MicroMutator'],
        'minMutationScore': 80.0
    }, indent=2)),
    'api-network-mocking-interception': ('network_route_stub.json', json.dumps({
        'route': '**/api/v1/checkout',
        'method': 'POST',
        'status': 200,
        'response': {'orderId': 'ORD-AUTO-998822', 'status': 'CONFIRMED'}
    }, indent=2)),
    'api-spec-to-e2e-matrix': ('sample_openapi.json', json.dumps({
        'openapi': '3.0.0',
        'info': {'title': 'Payment API', 'version': '1.0.0'},
        'paths': {
            '/payments': {
                'post': {
                    'summary': 'Create payment',
                    'responses': {'201': {'description': 'Created'}}
                }
            }
        }
    }, indent=2)),
    'architecture-decision-records': ('0001-record-architecture-decisions.md', """# 1. Record architecture decisions

Date: 2026-10-30

## Status
Accepted

## Context
We need to record technical architecture decisions in ADR format.

## Decision
We will use Markdown ADR files stored in docs/adr/.
"""),
    'auth-session-and-cookie-manager': ('storage_state_sample.json', json.dumps({
        'cookies': [
            {'name': 'session_id', 'value': 'sess_auto_998', 'domain': 'example.com', 'path': '/'}
        ],
        'origins': []
    }, indent=2)),
    'backend-load-and-stress-patterns': ('k6_load_test_sample.js', """import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  const res = http.get('https://test.k6.io');
  check(res, { 'status was 200': (r) => r.status == 200 });
  sleep(1);
}
"""),
    'bats-testing-patterns': ('cli_runner_test.bats', """#!/usr/bin/env bats

@test 'verify CLI returns version' {
  run python3 tools/cli.py --version
  [ "$status" -eq 0 ]
}
"""),
    'code-refactoring-refactor-clean': ('refactored_page_sample.groovy', """package pages

class UserManagementPage extends BasePage {
    static final String USER_TABLE_ROW = "table#users tbody tr"

    static boolean verifyUserActive(String email) {
        return verifyElementPresent(uniqueLocator(USER_TABLE_ROW, email))
    }
}
"""),
    'db-state-verifier-and-seeder': ('db_fixture_seed.json', json.dumps({
        'table': 'tenants',
        'operation': 'INSERT',
        'records': [
            {'tenant_id': 'AUTO_TENANT_01', 'status': 'ACTIVE', 'plan': 'ENTERPRISE'}
        ],
        'teardown': 'DELETE FROM tenants WHERE tenant_id = :tenant_id'
    }, indent=2)),
    'e2e-testing-patterns': ('playwright_sharded_config.ts', """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: 2,
  workers: process.env.CI ? 4 : undefined,
  use: {
    headless: true,
    trace: 'on-first-retry',
  },
});
"""),
    'failure-autopsy-and-healing': ('sample_junit_failure.xml', """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="AuthenticationSuite" tests="1" failures="1">
    <testcase name="testLoginFailure" classname="AuthTest">
      <failure message="Timeout 30000ms exceeded waiting for locator('#submit-btn')" type="ElementNotFoundError"/>
    </testcase>
  </testsuite>
</testsuites>
"""),
    'file-and-report-validator': ('sample_export_schema.json', json.dumps({
        'expectedHeaders': ['Order ID', 'Customer Name', 'Amount', 'Date', 'Status'],
        'rowCountRange': [1, 5000],
        'dateFormat': 'YYYY-MM-DD'
    }, indent=2)),
    'flaky-test-sentinel-and-quarantine': ('quarantine_registry.json', json.dumps({
        'quarantinedTests': [
            {
                'testId': 'TC-CHECKOUT-881',
                'flakinessScore': 0.35,
                'reason': 'Intermittent 3rd-party payment gateway timeout',
                'quarantineDate': '2026-10-30',
                'ticket': 'QA-1204'
            }
        ]
    }, indent=2)),
    'github-actions-templates': ('matrix_test_pipeline.yml', """name: Automated E2E Matrix
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx playwright test
"""),
    'graphify-impact-analyzer': ('dependency_blast_radius.json', json.dumps({
        'modifiedFile': 'src/pages/CheckoutPage.ts',
        'impactedSuites': ['tests/e2e/checkout.spec.ts', 'tests/e2e/payment.spec.ts'],
        'blastRadiusScore': 'LOW_ISOLATED'
    }, indent=2)),
    'katalon-cli-runner': ('headless_kre_exec.sh', """#!/bin/sh
# Execute headless Katalon suite with automatic process cleanup
katalonc -noSplash -runMode=console -projectPath="$1" -testSuitePath="Test Suites/SmokeSuite" -browserType="Chrome (headless)"
"""),
    'lam-script-generator': ('user_story_sample.md', """# User Story: User Password Reset Flow
As a registered customer,
I want to request a password reset email,
So that I can regain access if I forget my password.

## Acceptance Criteria:
1. Submitting registered email displays "Reset link dispatched".
2. Submitting empty email highlights field in red with validation error.
"""),
    'playwright-live-interaction': ('live_probe_script.js', """// Playwright Live Interactive Probe Helper
const targetLocator = page.locator("[data-testid='submit-order']");
const isVisible = await targetLocator.isVisible();
const boundingBox = await targetLocator.boundingBox();
console.log({ isVisible, boundingBox });
"""),
    'security-dast-sentinel': ('dast_scan_config.json', json.dumps({
        'targetUrl': 'https://staging.internal.example.com',
        'checks': ['OWASP_TOP_10', 'HEADER_SECURITY', 'TOKEN_EXPOSURE', 'SQLI_PROBING'],
        'failOnSeverity': 'HIGH'
    }, indent=2)),
    'self-healing-locator': ('aom_diff_sample.json', json.dumps({
        'brokenLocator': '#old-checkout-btn',
        'historicalAttributes': {'role': 'button', 'text': 'Confirm Order', 'testid': 'checkout-submit'},
        'currentAOMSnapshot': [
            {'role': 'button', 'name': 'Confirm Order', 'testid': 'checkout-submit-v2'}
        ],
        'healedLocator': "button[data-testid='checkout-submit-v2']"
    }, indent=2)),
    'skillspector-security-guard': ('safe_mcp_config.json', json.dumps({
        'mcpServers': {
            'playwright-live': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-playwright'],
                'sandboxPolicy': 'HEADLESS_VIRTUAL_DISPLAY'
            }
        }
    }, indent=2)),
    'synthetic-test-data-generator': ('idempotent_data_recipe.json', json.dumps({
        'entity': 'user',
        'prefix': 'AUTO_',
        'timestampPattern': 'EPOCH_MS',
        'fields': {
            'email': 'AUTO_USER@example-qa.com',
            'phone': '+15551234567'
        }
    }, indent=2)),
    'token-and-context-optimizer': ('distilled_log_sample.txt', """[RAW CLI LOG: 3,200 lines truncated by distill_log.py]
FAILED tests/checkout.spec.ts:42:15 -> TimeoutError: Waiting for selector `button.order-confirm`
Status: 1 failed, 12 passed in 14.2s
"""),
    'visual-regression-sentinel': ('visual_mask_rules.json', json.dumps({
        'maskSelectors': ['.dynamic-timestamp', '.live-chart-canvas', '.user-avatar-badge'],
        'thresholdSSIM': 0.98,
        'maxDiffPixels': 25
    }, indent=2)),
    'wcag-audit-patterns': ('wcag_compliance_checklist.json', json.dumps({
        'conformanceLevel': 'AA',
        'criteria': ['1.4.3 Contrast (Minimum)', '2.1.1 Keyboard', '2.4.7 Focus Visible', '4.1.2 Name, Role, Value'],
        'auditTool': 'axe-core'
    }, indent=2)),
    'web-vitals-and-performance-profiler': ('cwv_budget_policy.json', json.dumps({
        'LCP_ms': 2500,
        'CLS_score': 0.1,
        'INP_ms': 200,
        'networkThrottle': 'Fast 3G'
    }, indent=2))
}


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    count = 0
    for skill, (filename, content) in EXAMPLES_MAP.items():
        ex_dir = os.path.join(SKILLS_DIR, skill, 'examples')
        os.makedirs(ex_dir, exist_ok=True)
        fpath = os.path.join(ex_dir, filename)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1
    print(f"[OK] Generated examples for {count} skills.")


if __name__ == "__main__":
    main()
