#!/usr/bin/env python3
"""
Golden Test Cases for tools/gherkin_suite.py (Gherkin BDD Suite Compiler)
-------------------------------------------------------------------------
Covers: parsing (Feature/Background/Rule/Tags), Scenario Outline expansion,
And/But role inheritance, doc strings & data tables, deterministic NL -> IR
mapping, coverage-gap analysis, error handling and Universal IR emission.
"""

import os
import sys
import json
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import gherkin_suite
from universal_ir import ActionType, AssertionType


FULL_FEATURE = """# language: en
@checkout @smoke
Feature: Checkout Flow
  Customers buy items and receive confirmation.

  Background:
    Given the user is logged in as "member"

  @happy
  Scenario: Pay with credit card
    When the user navigates to "https://shop.example.com/checkout"
    And the user fills in "4111-1111-1111-1111" into "Card Number"
    And the user clicks the "Pay Now" button
    Then the user should see "Order Confirmed"

  @data-driven
  Scenario Outline: Apply voucher <voucher>
    When the user enters "<code>" into "Voucher Input"
    And the user clicks the "Apply" button
    Then the total should show "<total>"

    @valid
    Examples:
      | voucher | code   | total |
      | percent | SAVE10 | 90    |
      | fixed   | SHIP0  | 100   |

    @edge
    Examples: Boundary rows
      | voucher | code | total |
      | expired | OLD1 | 200   |
"""


class GherkinSuiteGoldenTests(unittest.TestCase):
    """Golden cases T1-T10 for the Gherkin suite compiler."""

    @staticmethod
    def _compile_feature(code: str):
        with tempfile.NamedTemporaryFile("w", suffix=".feature", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        try:
            return gherkin_suite.compile_feature(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_t1_outline_expansion_and_substitution(self):
        """T1: Scenario Outline expands one case per Example row with substitution."""
        res = self._compile_feature(FULL_FEATURE)
        # 1 regular + 2 rows + 1 boundary row = 4 expanded cases
        self.assertEqual(res["totals"]["expanded_cases"], 4)
        outline_cases = [c for c in res["cases"] if "--row-" in c["id"]]
        self.assertEqual(len(outline_cases), 3)
        save10 = next(c for c in res["cases"] if "SAVE10" in json.dumps(c["steps"]))
        self.assertEqual(save10["id"], "checkout-flow--apply-voucher-voucher--row-1")
        self.assertTrue(save10["valid"])

    def test_t2_background_prepended_to_every_case(self):
        """T2: Background steps are inherited by every expanded case."""
        res = self._compile_feature(FULL_FEATURE)
        for case in res["cases"]:
            first = case["steps"][0]
            self.assertEqual(first["description"], "Given the user is logged in as \"member\"")

    def test_t3_and_but_role_inheritance(self):
        """T3: And/But steps inherit the concrete role of the previous keyword."""
        parser = gherkin_suite.GherkinParser()
        feature = parser.parse(
            "Feature: F\n"
            "  Scenario: S\n"
            "    Given a cart\n"
            "    And a coupon\n"
            "    When I click \"Pay\"\n"
            "    But the balance is low\n"
            "    Then I see \"Declined\"\n",
            filename="t3.feature")
        sc = feature.scenarios[0]
        roles = [s.role for s in sc.steps]
        self.assertEqual(roles, ["arrange", "arrange", "act", "act", "assert"])
        self.assertEqual(sc.steps[1].keyword, "Given")
        self.assertEqual(sc.steps[3].keyword, "When")

    def test_t4_docstring_and_table_attach_to_last_step(self):
        """T4: Doc strings and data tables attach to the most recent step."""
        parser = gherkin_suite.GherkinParser()
        feature = parser.parse(
            "Feature: F\n"
            "  Scenario: S\n"
            "    When I submit the payload\n"
            '      """\n'
            '      {"a": 1}\n'
            '      """\n'
            "      | key | value |\n"
            "      | a   | 1     |\n",
            filename="t4.feature")
        step = feature.scenarios[0].steps[0]
        self.assertEqual(step.docstring, '{"a": 1}')
        self.assertEqual(step.table_rows, [["key", "value"], ["a", "1"]])

    def test_t5_deterministic_verb_mapping(self):
        """T5: Common verbs map deterministically onto Universal IR actions."""
        res = self._compile_feature(FULL_FEATURE)
        pay = next(c for c in res["cases"] if c["name"].startswith("Pay with credit card"))
        actions = [s["action"] for s in pay["steps"]]
        self.assertIn(ActionType.GOTO.value, actions)
        self.assertIn(ActionType.FILL.value, actions)
        self.assertIn(ActionType.CLICK.value, actions)
        fill = next(s for s in pay["steps"] if s["action"] == ActionType.FILL.value)
        self.assertEqual(fill["value"], "4111-1111-1111-1111")
        self.assertEqual(fill["target"], "Card Number")
        assertion = next(s for s in pay["steps"] if s["action"] == ActionType.ASSERT.value)
        self.assertEqual(assertion["assertion_type"], AssertionType.CONTAINS_TEXT.value)
        self.assertEqual(assertion["expected"], "Order Confirmed")

    def test_t6_gap_g1_missing_assertion(self):
        """T6: G1 - scenario without any Then step triggers a coverage gap."""
        res = self._compile_feature(
            "Feature: F\n"
            "  Scenario: Act only\n"
            "    When I click \"Save\"\n")
        rules = [g["rule"] for g in res["gaps"]]
        self.assertIn("G1-MISSING_ASSERTION", rules)

    def test_t7_gap_g2_missing_negative_path(self):
        """T7: G2 - feature with only happy paths triggers a negative-path gap."""
        res = self._compile_feature(
            "Feature: Login\n"
            "  Scenario: Valid login\n"
            "    When I click \"Sign in\"\n"
            "    Then I see \"Welcome\"\n")
        rules = [g["rule"] for g in res["gaps"]]
        self.assertIn("G2-MISSING_NEGATIVE_PATH", rules)

    def test_t8_unresolved_parameter_is_error(self):
        """T8: Example header mismatch leaves <param> unresolved -> hard error."""
        res = self._compile_feature(
            "Feature: F\n"
            "  Scenario Outline: Pay\n"
            "    When I enter <amount> into \"Total\"\n"
            "    Then I see <amount>\n"
            "    Examples:\n"
            "      | amountx |\n"
            "      | 100     |\n")
        self.assertTrue(res["errors"], "Unresolved parameter must be reported as an error")
        self.assertEqual(res["health_score_pct"], 0.0)

    def test_t9_tags_parsed_at_all_levels(self):
        """T9: Feature, Rule-scenario and Examples tags are all captured."""
        parser = gherkin_suite.GherkinParser()
        feature = parser.parse(
            "@feature-tag\n"
            "Feature: F\n"
            "  @scenario-tag\n"
            "  Scenario: S\n"
            "    Given a cart\n"
            "    Then I see \"OK\"\n",
            filename="t9.feature")
        self.assertEqual(feature.tags, ["@feature-tag"])
        self.assertEqual(feature.scenarios[0].tags, ["@feature-tag", "@scenario-tag"])

    def test_t10_emit_ir_and_report_health_bounded(self):
        """T10: --emit-ir produces valid TestCaseIR dicts; health score is bounded."""
        with tempfile.NamedTemporaryFile("w", suffix=".feature", delete=False, encoding="utf-8") as f:
            f.write(FULL_FEATURE)
            tmp_path = f.name
        try:
            res = gherkin_suite.compile_feature(tmp_path)
            ir_dicts = [case["ir"] for case in res["_ir_cases"]]
            self.assertEqual(len(ir_dicts), 4)
            for ir in ir_dicts:
                self.assertTrue(ir["id"])
                self.assertTrue(ir["title"])
                self.assertTrue(ir["steps"], "IR case must contain steps")
                for step in ir["steps"]:
                    self.assertTrue(step["action"])
            self.assertGreaterEqual(res["health_score_pct"], 0.0)
            self.assertLessEqual(res["health_score_pct"], 100.0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_t11_unclosed_docstring_is_parse_error(self):
        """T11: An unterminated doc string is a hard parse error."""
        res = self._compile_feature(
            "Feature: F\n"
            "  Scenario: S\n"
            "    When I submit\n"
            '      """\n'
            "      broken\n")
        self.assertTrue(any("unterminated doc string" in e for e in res["errors"]))

    def test_t12_cli_end_to_end_exit_codes(self):
        """T12: CLI run returns 0 on a clean feature and 1 on authoring errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            good = os.path.join(tmp_dir, "good.feature")
            with open(good, "w", encoding="utf-8") as f:
                f.write(
                    "Feature: OK\n"
                    "  Scenario: Fine\n"
                    "    Given a cart\n"
                    "    When I click \"Buy\"\n"
                    "    Then I see \"Thanks\"\n"
                    "  Scenario: Invalid voucher\n"
                    "    When I enter \"BAD\" into \"Voucher\"\n"
                    "    Then I see \"Invalid voucher\"\n")
            self.assertEqual(gherkin_suite.run(good), 0)

            bad = os.path.join(tmp_dir, "bad.feature")
            with open(bad, "w", encoding="utf-8") as f:
                f.write(
                    "Feature: Broken\n"
                    "  Scenario Outline: Pay\n"
                    "    When I enter <amount> into \"Total\"\n"
                    "    Examples:\n"
                    "      | other |\n"
                    "      | 1     |\n")
            self.assertEqual(gherkin_suite.run(bad), 1)
            self.assertTrue(os.path.exists(gherkin_suite.OUTPUT_JSON))


if __name__ == "__main__":
    unittest.main()
