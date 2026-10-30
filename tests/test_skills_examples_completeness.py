#!/usr/bin/env python3
"""
Test Skills Examples Completeness (Task B3 Standard)
-----------------------------------------------------
Verifies that all 28 skills declared in skills_manifest.json contain
a valid examples/ directory with at least one representative file.
"""

import os
import json
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MANIFEST_PATH = os.path.join(REPO_ROOT, "skills_manifest.json")
SKILLS_DIR = os.path.join(REPO_ROOT, ".agents", "skills")


class TestSkillsExamplesCompleteness(unittest.TestCase):
    """Verifies that 100% of skills include demonstrable examples/."""

    def setUp(self):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
        self.declared_skills = [s["id"] for s in self.manifest.get("skills", [])]

    def test_all_declared_skills_have_examples_directory(self):
        """Assert that every skill in manifest contains examples/ with valid files."""
        expected_total = self.manifest.get("totalSkills", 29)
        self.assertEqual(len(self.declared_skills), expected_total, f"Manifest must declare exactly {expected_total} skills")

        missing_examples = []
        for skill_id in self.declared_skills:
            ex_dir = os.path.join(SKILLS_DIR, skill_id, "examples")
            if not os.path.isdir(ex_dir):
                missing_examples.append(f"{skill_id}: missing examples/ directory")
            else:
                files = os.listdir(ex_dir)
                if not files:
                    missing_examples.append(f"{skill_id}: examples/ directory is empty")

        self.assertEqual(
            len(missing_examples), 0,
            f"All skills must have examples: {missing_examples}"
        )


if __name__ == "__main__":
    unittest.main()
