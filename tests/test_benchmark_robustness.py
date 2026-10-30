#!/usr/bin/env python3
"""
Test Benchmark Robustness & Anti-Fake Pass Verification (D1 Standard)
---------------------------------------------------------------------
Verifies that the benchmark evaluation harness does NOT fake pass:
When DOM snapshots are poisoned, or locator targets do not exist,
the challenge MUST return FAIL.
"""

import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
EVAL_DIR = os.path.join(REPO_ROOT, "benchmarks", "qa_eval")
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)

from eval_runner import BenchmarkEvaluator


class TestBenchmarkRobustness(unittest.TestCase):
    """Verifies that the benchmark harness properly fails on unresolvable input."""

    def setUp(self):
        self.evaluator = BenchmarkEvaluator()

    def test_broken_locator_with_unmatched_dom_fails(self):
        """When DOM snapshot does not match the broken locator or keywords, challenge must FAIL."""
        failing_challenge = {
            "id": "QA-CHALLENGE-FAIL-01",
            "name": "Completely Missing Element Trap",
            "category": "locator_drift",
            "difficulty": "HARD",
            "failure_vector": {
                "type": "LOCATOR_DRIFT",
                "broken_locator": "#completely-deleted-modal-btn",
                "dom_snapshot": "<div class='empty-container'><p>No actions available</p></div>"
            },
            "expected_resolution": {
                "healed_locator": "#non-existent-healed-id",
                "strategy": "SHOULD_FAIL"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 300
            }
        }

        result = self.evaluator.evaluate_challenge(failing_challenge)
        self.assertFalse(result["resolved"], "Challenge with poisoned DOM must NOT resolve successfully")
        self.assertEqual(result["status"], "FAILED", "Status must be FAILED")

    def test_timing_race_with_hardcoded_sleep_fails(self):
        """When timing challenge uses hardcoded Thread.sleep without smart waits, it must FAIL."""
        bad_timing_challenge = {
            "id": "QA-CHALLENGE-FAIL-02",
            "name": "Brittle Sleep Antipattern",
            "category": "timing_and_race",
            "difficulty": "MEDIUM",
            "failure_vector": {
                "type": "FLAKY_SLEEP",
                "code": "Thread.sleep(5000)"
            },
            "expected_resolution": {
                "healed_code": "Thread.sleep(10000)",  # Still using bad sleep
                "strategy": "BRITTLE_SLEEP"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 300
            }
        }

        result = self.evaluator.evaluate_challenge(bad_timing_challenge)
        self.assertFalse(result["resolved"], "Timing challenge with Thread.sleep must FAIL")
        self.assertEqual(result["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
