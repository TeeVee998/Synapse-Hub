#!/usr/bin/env python3
"""
Unit Tests for Hermetic State, Event-Driven Wait Weaver, and Config Decoupling
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from universal_ir import (
    ProjectIR, TestCaseIR, StepIR, ActionType,
    analyze_data_dependencies, resolve_hermetic_fixtures, DataDependencyType
)
from omni_emitter import OmniEmitter
from config_decoupler import ConfigDecoupler


class TestHermeticAndResilience(unittest.TestCase):

    def test_hermetic_data_dependency_resolver(self):
        # Create 2 coupled test cases
        tc1 = TestCaseIR(
            id="TC_01_Create_Order",
            title="Create New Order",
            steps=[
                StepIR(action=ActionType.CLICK, target="submitOrderBtn", description="Submit order"),
                StepIR(action=ActionType.CUSTOM_CALL, value="const order_id = 'ORD_998';", description="Extract order_id"),
            ],
            produced_variables=["order_id"]
        )

        tc2 = TestCaseIR(
            id="TC_02_Approve_Order",
            title="Approve Existing Order",
            steps=[
                StepIR(action=ActionType.CLICK, target="approveBtn", value="${order_id}", description="Click approve with order_id")
            ],
            consumed_variables=["order_id"]
        )

        project = ProjectIR(test_cases=[tc1, tc2])

        # 1. Analyze dependencies
        shared = analyze_data_dependencies(project)
        self.assertTrue(any(s.name == "order_id" for s in shared))
        order_var = next(s for s in shared if s.name == "order_id")
        self.assertIn(order_var.dep_type, [DataDependencyType.ID, DataDependencyType.ORDER_NUMBER])

        # 2. Resolve hermetic fixtures
        hermetic_project = resolve_hermetic_fixtures(project)
        self.assertGreaterEqual(len(hermetic_project.test_cases[1].steps), 2)
        # Verify first step of TC2 is now an isolated seed step
        first_step = hermetic_project.test_cases[1].steps[0]
        self.assertEqual(first_step.action, ActionType.API_CALL)
        self.assertIn("order_id", first_step.description)

    def test_omni_emitter_cross_engine_safe_interact(self):
        project = ProjectIR(name="HermeticDemo")
        tc = TestCaseIR(
            id="TC_01",
            title="Safe Click Demo",
            steps=[
                StepIR(action=ActionType.CLICK, target="confirmBtn", description="Click confirm button")
            ]
        )
        project.test_cases.append(tc)

        files = OmniEmitter.emit(project, "playwright-ts")
        self.assertIn("helpers/safeInteract.ts", files)
        self.assertIn("tests/HermeticDemo.spec.ts", files)

        spec_code = files["tests/HermeticDemo.spec.ts"]
        self.assertIn("safeInteract", spec_code)
        self.assertIn("fallbackToJsDispatch: true", spec_code)

    def test_config_decoupler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_auth.ts"
            test_file.write_text("""
                const baseUrl = "https://staging-v2.internal.company.com/api";
                const userPass = "SuperSecretPassword123!";
            """, encoding="utf-8")

            decoupler = ConfigDecoupler(tmpdir)
            findings = decoupler.scan()
            self.assertGreaterEqual(len(findings), 2)

            json_path, env_path = decoupler.export_configs()
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(env_path))

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIn("https://staging-v2.internal.company.com/api", data["APP_BASE_URL"])


if __name__ == "__main__":
    unittest.main()
