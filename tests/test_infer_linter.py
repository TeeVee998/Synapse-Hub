#!/usr/bin/env python3
"""
Unit Tests for infer_linter.py verifying the 8 Golden Test Cases (L1 - L8)
from Enterprise QA Hub roadmap.
"""

import os
import sys
import tempfile
import unittest

# Ensure tools directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import infer_linter


class TestInferLinter8Cases(unittest.TestCase):
    """Verifies all 8 Test Cases from sheet 'Ca kiểm thử linter'."""

    def _analyze_code(self, code: str, extension: str = ".ts"):
        with tempfile.NamedTemporaryFile("w", suffix=extension, delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        try:
            res = infer_linter.analyze_script(tmp_path)
            return res
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_l1_empty_catch_ts_and_groovy(self):
        """L1: Empty catch {} in TS and Groovy must be caught as CRITICAL."""
        ts_code = """
        try {
            await page.click('#submit');
        } catch (e) {
        }
        """
        res_ts = self._analyze_code(ts_code, ".ts")
        swallowed = [d for d in res_ts["defects"] if d["type"] == "SWALLOWED_EXCEPTION"]
        self.assertTrue(len(swallowed) > 0, "L1 TS: Empty catch must be caught")
        self.assertEqual(swallowed[0]["severity"], "CRITICAL")

        groovy_code = """
        try {
            WebUI.click(findTestObject('btn_submit'))
        } catch (Exception e) {
        }
        """
        res_gr = self._analyze_code(groovy_code, ".groovy")
        swallowed_gr = [d for d in res_gr["defects"] if d["type"] == "SWALLOWED_EXCEPTION"]
        self.assertTrue(len(swallowed_gr) > 0, "L1 Groovy: Empty catch must be caught")
        self.assertEqual(swallowed_gr[0]["severity"], "CRITICAL")

    def test_l2_groovy_interaction_without_verify(self):
        """L2: Script Groovy with interaction but missing assertion must trigger WARNING."""
        code = """
        CustomKeywords.'com.example.Helper.login'("user", "pass")
        WebUI.click(findTestObject('btn_save'))
        """
        res = self._analyze_code(code, ".groovy")
        warn = [d for d in res["defects"] if d["type"] == "FAKE_PASS_NO_ASSERTION"]
        self.assertTrue(len(warn) > 0, "L2: Interaction without assertion must be warned")
        self.assertEqual(warn[0]["severity"], "WARNING")

    def test_l3_tautological_assertions(self):
        """L3: expect(true).toBe(true), assert True, assert true, assert 1 == 1 caught as CRITICAL."""
        cases = [
            ("expect(true).toBe(true);", ".ts"),
            ("assert True", ".py"),
            ("assert true", ".groovy"),
            ("assert 1 == 1", ".py")
        ]
        for snippet, ext in cases:
            res = self._analyze_code(snippet, ext)
            taut = [d for d in res["defects"] if d["type"] == "TAUTOLOGICAL_ASSERTION"]
            self.assertTrue(len(taut) > 0, f"L3: Tautology '{snippet}' must be detected as CRITICAL")
            self.assertEqual(taut[0]["severity"], "CRITICAL")

    def test_l4_unawaited_playwright_assertion(self):
        """L4: expect(locator).toBeVisible() without await in TS/JS caught as CRITICAL."""
        code = """
        import { test, expect } from '@playwright/test';
        test('example', async ({ page }) => {
            expect(page.locator('#banner')).toBeVisible();
        });
        """
        res = self._analyze_code(code, ".ts")
        unawaited = [d for d in res["defects"] if d["type"] == "UNAWAITED_ASYNC_ASSERTION"]
        self.assertTrue(len(unawaited) > 0, "L4: Unawaited Playwright assertion must be caught")
        self.assertEqual(unawaited[0]["severity"], "CRITICAL")

    def test_l5_python_swallowed_exception(self):
        """L5: except Exception: pass or except: pass caught as CRITICAL."""
        py_code = """
        try:
            perform_login()
        except Exception:
            pass
        """
        res = self._analyze_code(py_code, ".py")
        swallowed = [d for d in res["defects"] if d["type"] == "SWALLOWED_EXCEPTION"]
        self.assertTrue(len(swallowed) > 0, "L5: Python except: pass must be caught")
        self.assertEqual(swallowed[0]["severity"], "CRITICAL")

    def test_l6_test_without_assertions(self):
        """L6: Test Python/TS with logic but no assertions must report WARNING."""
        code = """
        def test_order_flow():
            client = APIClient()
            client.authenticate()
        """
        res = self._analyze_code(code, "test_order.py")
        no_assert = [d for d in res["defects"] if "ASSERTION" in d["type"]]
        self.assertTrue(len(no_assert) > 0, "L6: Test file without assert must trigger warning")

    def test_l7_valid_short_groovy_script(self):
        """L7: Valid 1-2 line Groovy script with assertion must NOT be flagged as empty."""
        code = """
        CustomKeywords.'com.example.Helper.login'("user", "pass")
        assert WebUI.verifyElementPresent(findTestObject('dashboard'), 10)
        """
        res = self._analyze_code(code, ".groovy")
        empty = [d for d in res["defects"] if d["type"] == "EMPTY_TEST_SCRIPT"]
        self.assertEqual(len(empty), 0, "L7: Valid short script must not be flagged as empty")
        self.assertTrue(res["is_clean"], "L7: Script with assert and action should be clean")

    def test_l8_codebase_health_score_bounded(self):
        """L8: Codebase health score must always be bounded in [0.0, 100.0]."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create multiple failing scripts
            for i in range(5):
                fpath = os.path.join(tmp_dir, f"test_fail_{i}.py")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("try:\n    pass\nexcept:\n    pass\nassert True\n")
            
            # Run infer_linter on directory
            exit_code = infer_linter.run_infer_linter(tmp_dir)
            with open(infer_linter.OUTPUT_JSON, "r", encoding="utf-8") as rf:
                import json
                summary = json.load(rf)
            score = summary.get("health_score_pct", 0.0)
            self.assertGreaterEqual(score, 0.0, "L8: Health score cannot be negative")
            self.assertLessEqual(score, 100.0, "L8: Health score cannot exceed 100%")


if __name__ == "__main__":
    unittest.main()
