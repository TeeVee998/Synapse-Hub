#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Thế Vị (@TeeVee998). All rights reserved.
# SPDX-License-Identifier: MIT
# Project: Synapse-Hub (https://github.com/TeeVee998/Synapse-Hub)

"""
tests/test_author_integrity.py
-------------------------------
Unit tests for Author Attribution & Anti-Tamper Integrity Guard (tools/author_integrity.py).
"""

import os
import sys
import tempfile
import unittest

# Ensure tools/ is on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import author_integrity
import verify_all


class TestAuthorIntegrity(unittest.TestCase):

    def test_canonical_watermark_contains_author(self):
        wm = author_integrity.get_canonical_watermark()
        self.assertIn("Thế Vị", wm)
        self.assertIn("@TeeVee998", wm)
        self.assertIn("https://github.com/TeeVee998/Synapse-Hub", wm)

    def test_current_repo_passes_integrity(self):
        valid, violations = author_integrity.verify_author_attribution(REPO_ROOT)
        self.assertTrue(valid, f"Current repo failed author attribution: {violations}")
        self.assertEqual(len(violations), 0)

    def test_missing_license_detected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            valid, violations = author_integrity.verify_author_attribution(tmp_dir)
            self.assertFalse(valid)
            self.assertTrue(any("LICENSE" in v for v in violations))

    def test_tampered_license_detected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a LICENSE with altered copyright notice
            with open(os.path.join(tmp_dir, "LICENSE"), "w", encoding="utf-8") as f:
                f.write("MIT License\nCopyright (c) 2026 John Doe. All rights reserved.\n")
            valid, violations = author_integrity.verify_author_attribution(tmp_dir)
            self.assertFalse(valid)
            self.assertTrue(any("LICENSE file modified" in v for v in violations))

    def test_tampered_package_json_detected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create valid LICENSE
            with open(os.path.join(tmp_dir, "LICENSE"), "w", encoding="utf-8") as f:
                f.write("Copyright (c) 2026 Thế Vị (@TeeVee998)\nhttps://github.com/TeeVee998/Synapse-Hub\n")
            # Create tampered package.json
            with open(os.path.join(tmp_dir, "package.json"), "w", encoding="utf-8") as f:
                f.write('{"name": "tampered", "author": "John Doe <john@example.com>"}\n')
            valid, violations = author_integrity.verify_author_attribution(tmp_dir)
            self.assertFalse(valid)
            self.assertTrue(any("package.json modified" in v for v in violations))

    def test_tampered_readme_detected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create valid LICENSE
            with open(os.path.join(tmp_dir, "LICENSE"), "w", encoding="utf-8") as f:
                f.write("Copyright (c) 2026 Thế Vị (@TeeVee998)\nhttps://github.com/TeeVee998/Synapse-Hub\n")
            # Create tampered README.md
            with open(os.path.join(tmp_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write("# Generic Project\nNo author attribution here.\n")
            valid, violations = author_integrity.verify_author_attribution(tmp_dir)
            self.assertFalse(valid)
            self.assertTrue(any("README.md modified" in v for v in violations))

    def test_enforce_attribution_non_strict_returns_false_on_tamper(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Empty temp dir will fail verification
            result = author_integrity.enforce_author_attribution(repo_root=tmp_dir, strict=False)
            self.assertFalse(result)

    def test_gate_0_in_verify_all(self):
        self.assertTrue(verify_all.gate_0_author_integrity(REPO_ROOT, mode="HUB"))
        self.assertTrue(verify_all.gate_0_author_integrity(REPO_ROOT, mode="TARGET"))

    def test_cryptographic_fingerprint_valid(self):
        self.assertTrue(author_integrity.verify_author_fingerprint())

    def test_assert_integrity_or_raise_passes_on_canonical_repo(self):
        self.assertTrue(author_integrity.assert_integrity_or_raise(REPO_ROOT))

    def test_cryptographic_fingerprint_mismatch_raises_runtime_error(self):
        orig_sig = author_integrity.CANONICAL_AUTHOR_SIG
        try:
            author_integrity.CANONICAL_AUTHOR_SIG = "0000000000000000000000000000000000000000000000000000000000000000"
            self.assertFalse(author_integrity.verify_author_fingerprint())
            with self.assertRaises(RuntimeError) as ctx:
                author_integrity.assert_integrity_or_raise(REPO_ROOT)
            self.assertIn("CRITICAL INTEGRITY CORRUPTED", str(ctx.exception))
        finally:
            author_integrity.CANONICAL_AUTHOR_SIG = orig_sig


if __name__ == "__main__":
    unittest.main()
