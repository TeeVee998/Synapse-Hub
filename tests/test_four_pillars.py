#!/usr/bin/env python3
"""
Automated Test Suite for the 4 Ultimate Pillars of QC Automation
-----------------------------------------------------------------
Verifies:
  1. Auto-Bug Reporter & RCA Ticket Generator (bug_reporter.py)
  2. API Network Mocking & Chaos Shield (network_mock_shield.py)
  3. Smart Visual Masker & Anti-Flake Engine (smart_visual_masker.py)
  4. CI/CD Silent Self-Healing Pipeline Hook (ci_healing_hook.py)
"""

import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

from bug_reporter import BugReporter
from network_mock_shield import NetworkMockShield
from smart_visual_masker import SmartVisualMasker
from ci_healing_hook import CIHealingHook


class TestFourUltimatePillars(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Bug Reporter & RCA Tests
    # -------------------------------------------------------------------------
    def test_bug_reporter_rca_classification(self):
        """Validates that RCA correctly separates AUT Bugs from Test Script Bugs."""
        # Backend 500 error
        rca_500 = BugReporter.classify_root_cause("HTTP 500 Internal Server Error", "at CheckoutController.pay()")
        self.assertEqual(rca_500["type"], "AUT_BACKEND_CRASH")
        self.assertEqual(rca_500["severity"], "Blocker")

        # Frontend Uncaught TypeError
        rca_fe = BugReporter.classify_root_cause("Uncaught TypeError: Cannot read property 'map' of undefined", "at UserList.tsx:42")
        self.assertEqual(rca_fe["type"], "AUT_FRONTEND_EXCEPTION")
        self.assertEqual(rca_fe["severity"], "Critical")

        # Automation Locator Timeout
        rca_loc = BugReporter.classify_root_cause("Timeout 30000ms exceeded waiting for locator('#btn')", "")
        self.assertEqual(rca_loc["type"], "TEST_LOCATOR_DRIFT")
        self.assertEqual(rca_loc["severity"], "Minor")

    def test_bug_reporter_jira_and_markdown_output(self):
        """Validates Jira markup and GitHub Markdown report generation."""
        report_jira = BugReporter.generate_report(
            test_id="TC_PAY_001",
            test_title="Checkout Payment Flow",
            error_message="500 Internal Server Error on /api/orders",
            stack_trace="at Module.checkout (Checkout.js:10)\nat processTicksAndRejections (task_queues:95)",
            format_type="jira"
        )
        self.assertIn("h2. [BUG][BLOCKER] TC_PAY_001", report_jira)
        self.assertIn("{code:java}", report_jira)
        self.assertIn("Steps to Reproduce", report_jira)

        report_md = BugReporter.generate_report(
            test_id="TC_PAY_001",
            test_title="Checkout Payment Flow",
            error_message="500 Internal Server Error on /api/orders",
            format_type="md"
        )
        self.assertIn("# [BUG][BLOCKER] TC_PAY_001", report_md)
        self.assertIn("## 📌 1. Steps to Reproduce", report_md)

    # -------------------------------------------------------------------------
    # 2. Network Mock Shield Tests
    # -------------------------------------------------------------------------
    def test_network_mock_presets(self):
        """Validates network mock preset resolution and code generation."""
        preset = NetworkMockShield.get_preset("payment_success")
        self.assertEqual(preset["status"], 200)
        self.assertEqual(preset["body"]["status"], "SUCCESS")

        ts_code = NetworkMockShield.generate_playwright_ts("**/api/checkout", status=200, body=preset["body"], delay_ms=100)
        self.assertIn("await page.route('**/api/checkout'", ts_code)
        self.assertIn("status: 200", ts_code)
        self.assertIn("setTimeout", ts_code)

        py_code = NetworkMockShield.generate_playwright_python("**/api/checkout", status=402)
        self.assertIn("page.route('**/api/checkout'", py_code)
        self.assertIn("status=402", py_code)

        cy_code = NetworkMockShield.generate_cypress_js("**/api/checkout", method="POST", status=500)
        self.assertIn("cy.intercept('POST', '**/api/checkout'", cy_code)

    # -------------------------------------------------------------------------
    # 3. Smart Visual Masker Tests
    # -------------------------------------------------------------------------
    def test_smart_visual_masker_css_and_snippets(self):
        """Validates anti-flake CSS and Playwright screenshot options."""
        css = SmartVisualMasker.get_anti_flake_css()
        self.assertIn("animation: none !important;", css)
        self.assertIn("caret-color: transparent !important;", css)

        snippet = SmartVisualMasker.generate_playwright_ts_options()
        self.assertIn("toHaveScreenshot", snippet)
        self.assertIn("page.locator('.timestamp')", snippet)
        self.assertIn("page.locator('.avatar')", snippet)

        js_script = SmartVisualMasker.generate_browser_mask_script()
        self.assertIn("document.querySelectorAll", js_script)
        self.assertIn("data-visual-masked", js_script)

    # -------------------------------------------------------------------------
    # 4. CI/CD Silent Self-Healing Hook Tests
    # -------------------------------------------------------------------------
    def test_ci_healing_hook_evaluation_and_patch(self):
        """Validates that CIHealingHook updates file in-place and drafts PR description."""
        sample_file = os.path.join(self.temp_dir, "LoginPage.ts")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("readonly btnSubmit = page.locator('//button[@id=\"old_submit\"]');")

        result = CIHealingHook.evaluate_and_heal(
            file_path=sample_file,
            failed_locator='//button[@id="old_submit"]',
            healed_locator='//button[@id="new_submit"]',
            test_id="TC_LOGIN_01",
            confidence=0.98
        )

        self.assertTrue(result["applied"])
        self.assertEqual(result["test_id"], "TC_LOGIN_01")
        self.assertIn("auto-heal/tc_login_01", result["branch"])
        self.assertIn("fix(locators): auto-heal", result["pr_title"])
        self.assertIn("Autonomous CI/CD Self-Healing Report", result["pr_body"])

        # Verify file on disk is patched
        with open(sample_file, "r", encoding="utf-8") as f:
            patched_content = f.read()
        self.assertIn('//button[@id="new_submit"]', patched_content)
        self.assertNotIn('//button[@id="old_submit"]', patched_content)


if __name__ == "__main__":
    unittest.main()
