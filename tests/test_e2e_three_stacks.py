#!/usr/bin/env python3
"""
End-to-End Multi-Stack Verification Test (Task D3 Standard)
-----------------------------------------------------------
Validates the complete lifecycle:
  setup_project (--profile <fw>) -> verify_all -> analyze_project -> setup_project (--uninstall)
across three distinct target ecosystems:
  1. Playwright Test (TypeScript)
  2. Pytest (Python)
  3. Katalon Studio (Groovy)
"""

import os
import sys
import shutil
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import setup_project
import verify_all
import analyze_project


class TestE2EThreeStacks(unittest.TestCase):
    """End-to-end test verifying setup, gates DoD, and analysis across 3 target frameworks."""

    def setUp(self):
        self.temp_root = tempfile.mkdtemp(prefix="synapse_e2e_test_")

    def tearDown(self):
        if os.path.exists(self.temp_root):
            try:
                shutil.rmtree(self.temp_root)
            except Exception:
                pass

    def test_e2e_playwright_typescript_stack(self):
        """Playwright TS: setup --profile playwright -> verify_all -> analyze -> uninstall."""
        prj_dir = os.path.join(self.temp_root, "playwright_app")
        os.makedirs(os.path.join(prj_dir, "src", "pages"), exist_ok=True)
        os.makedirs(os.path.join(prj_dir, "tests"), exist_ok=True)

        with open(os.path.join(prj_dir, "playwright.config.ts"), "w", encoding="utf-8") as f:
            f.write("import { defineConfig } from '@playwright/test';\nexport default defineConfig({});\n")

        with open(os.path.join(prj_dir, "src", "pages", "LoginPage.ts"), "w", encoding="utf-8") as f:
            f.write("export class LoginPage {\n  async login() { return true; }\n}\n")

        with open(os.path.join(prj_dir, "tests", "auth.spec.ts"), "w", encoding="utf-8") as f:
            f.write("import { test, expect } from '@playwright/test';\ntest('login', async ({ page }) => {\n  await expect(page.locator('#welcome')).toBeVisible();\n});\n")

        # 1. Setup
        ret_setup = setup_project.run_setup(prj_dir, profile="playwright")
        self.assertEqual(ret_setup, 0, "Playwright setup must succeed")
        self.assertTrue(os.path.exists(os.path.join(prj_dir, "PROJECT_AI_GUIDE.md")))

        guide_content = open(os.path.join(prj_dir, "PROJECT_AI_GUIDE.md"), encoding="utf-8").read()
        self.assertIn("PLAYWRIGHT", guide_content)

        # 2. Verify Quality Gates
        ret_verify = verify_all.run_all_gates(prj_dir, mode="target")
        self.assertEqual(ret_verify, 0, "Playwright project must satisfy all Quality Gates")

        # 3. Analyze
        ret_analyze = analyze_project.run_full_analysis(prj_dir)
        self.assertEqual(ret_analyze, 0, "Playwright analysis must produce health report")
        self.assertTrue(os.path.exists(os.path.join(prj_dir, "PROJECT_HEALTH_REPORT.md")))

        # 4. Uninstall
        ret_uninst = setup_project.uninstall_setup(prj_dir)
        self.assertEqual(ret_uninst, 0, "Uninstall must cleanly remove artifacts")
        self.assertFalse(os.path.exists(os.path.join(prj_dir, "PROJECT_AI_GUIDE.md")))

    def test_e2e_pytest_python_stack(self):
        """Pytest: setup --profile pytest -> verify_all -> analyze -> uninstall."""
        prj_dir = os.path.join(self.temp_root, "pytest_service")
        os.makedirs(os.path.join(prj_dir, "pages"), exist_ok=True)
        os.makedirs(os.path.join(prj_dir, "tests"), exist_ok=True)

        with open(os.path.join(prj_dir, "pytest.ini"), "w", encoding="utf-8") as f:
            f.write("[pytest]\npython_files = test_*.py\n")

        with open(os.path.join(prj_dir, "pages", "account_page.py"), "w", encoding="utf-8") as f:
            f.write("class AccountPage:\n    def get_balance(self):\n        return 100\n")

        with open(os.path.join(prj_dir, "tests", "test_account.py"), "w", encoding="utf-8") as f:
            f.write("from pages.account_page import AccountPage\ndef test_balance():\n    page = AccountPage()\n    assert page.get_balance() == 100\n")

        # 1. Setup
        ret_setup = setup_project.run_setup(prj_dir, profile="pytest")
        self.assertEqual(ret_setup, 0, "Pytest setup must succeed")
        self.assertTrue(os.path.exists(os.path.join(prj_dir, "PROJECT_AI_GUIDE.md")))

        # 2. Verify
        ret_verify = verify_all.run_all_gates(prj_dir, mode="target")
        self.assertEqual(ret_verify, 0, "Pytest project must satisfy all Quality Gates")

        # 3. Analyze
        ret_analyze = analyze_project.run_full_analysis(prj_dir)
        self.assertEqual(ret_analyze, 0, "Pytest analysis must produce health report")

        # 4. Uninstall
        ret_uninst = setup_project.uninstall_setup(prj_dir)
        self.assertEqual(ret_uninst, 0, "Uninstall must cleanly remove artifacts")

    def test_e2e_katalon_studio_stack(self):
        """Katalon Studio: setup --profile katalon -> verify_all -> analyze -> uninstall."""
        prj_dir = os.path.join(self.temp_root, "katalon_suite")
        os.makedirs(os.path.join(prj_dir, "Keywords", "pages"), exist_ok=True)
        os.makedirs(os.path.join(prj_dir, "Scripts", "TC_Order"), exist_ok=True)

        with open(os.path.join(prj_dir, "order_suite.prj"), "w", encoding="utf-8") as f:
            f.write("<Project><name>OrderSuite</name></Project>\n")

        with open(os.path.join(prj_dir, "Keywords", "pages", "OrderPage.groovy"), "w", encoding="utf-8") as f:
            f.write("package pages\nclass OrderPage {\n  static void submitOrder() {}\n}\n")

        with open(os.path.join(prj_dir, "Scripts", "TC_Order", "Script.groovy"), "w", encoding="utf-8") as f:
            f.write("import pages.OrderPage\nOrderPage.submitOrder()\nassert WebUI.verifyTextPresent('SUCCESS', false)\n")

        # 1. Setup
        ret_setup = setup_project.run_setup(prj_dir, profile="katalon")
        self.assertEqual(ret_setup, 0, "Katalon setup must succeed")
        self.assertTrue(os.path.exists(os.path.join(prj_dir, "PROJECT_AI_GUIDE.md")))

        # 2. Verify
        ret_verify = verify_all.run_all_gates(prj_dir, mode="target")
        self.assertEqual(ret_verify, 0, "Katalon project must satisfy all Quality Gates")

        # 3. Analyze
        ret_analyze = analyze_project.run_full_analysis(prj_dir)
        self.assertEqual(ret_analyze, 0, "Katalon analysis must produce health report")

        # 4. Uninstall
        ret_uninst = setup_project.uninstall_setup(prj_dir)
        self.assertEqual(ret_uninst, 0, "Uninstall must cleanly remove artifacts")


if __name__ == "__main__":
    unittest.main()
