#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Thế Vị (@TeeVee998). All rights reserved.
# SPDX-License-Identifier: MIT
# Project: Synapse-Hub (https://github.com/TeeVee998/Synapse-Hub)

"""
tools/author_integrity.py — Author Attribution & Anti-Tamper Integrity Guard
-----------------------------------------------------------------------------
Verifies the cryptographic and textual provenance of Synapse Hub.
Enforces the mandatory Attribution condition of the MIT License:
  "The above copyright notice and this permission notice shall be included
   in all copies or substantial portions of the Software."

Checks:
  1. LICENSE file exists with original copyright notice (Thế Vị @TeeVee998).
  2. package.json maintains the original author attribution.
  3. README.md retains the original creator and repository provenance.
  4. pyproject.toml preserves the author declaration.
"""

import os
import sys
import json
import hashlib
from typing import Tuple, List, Optional

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ORIGINAL_AUTHOR_NAME = "Thế Vị"
ORIGINAL_AUTHOR_HANDLE = "@TeeVee998"
ORIGINAL_REPO_URL = "https://github.com/TeeVee998/Synapse-Hub"

# Pre-computed SHA-256 fingerprint of canonical author credentials
CANONICAL_AUTHOR_SIG = "ea09e6bd3428c00581a385ec13bb7d8cd7d9e800fbdd1094c6d5a7bfb4060475"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO_ROOT = os.path.dirname(SCRIPT_DIR)


def get_canonical_watermark() -> str:
    return f"{ORIGINAL_AUTHOR_NAME} ({ORIGINAL_AUTHOR_HANDLE}) <{ORIGINAL_REPO_URL}>"


def verify_author_fingerprint() -> bool:
    """Cryptographic validation that the canonical watermark matches the SHA-256 fingerprint."""
    watermark = get_canonical_watermark()
    computed = hashlib.sha256(watermark.encode("utf-8")).hexdigest()
    return computed == CANONICAL_AUTHOR_SIG


def assert_integrity_or_raise(repo_root: Optional[str] = None) -> bool:
    """
    Enforces author integrity and cryptographic provenance.
    If tampered with, immediately halts execution by raising a RuntimeError.
    Under MIT License, the original copyright notice in LICENSE is mandatory.
    """
    if not verify_author_fingerprint():
        raise RuntimeError(
            "🛑 CRITICAL INTEGRITY CORRUPTED: Canonical author fingerprint mismatch. "
            "Synapse Hub requires original author attribution ('Thế Vị @TeeVee998') to execute."
        )
    valid, violations = verify_author_attribution(repo_root)
    license_violations = [v for v in violations if "LICENSE" in v]
    if license_violations:
        err_msg = "🛑 CRITICAL INTEGRITY VIOLATION: Mandatory MIT copyright notice missing or altered.\n"
        for v in license_violations:
            err_msg += f"  • {v}\n"
        err_msg += "Under the MIT License, original author attribution to 'Thế Vị (@TeeVee998)' must be preserved in LICENSE."
        raise RuntimeError(err_msg)
    elif not valid:
        # Non-fatal warning for peripheral files (README/package.json) to allow flexible downstream fork usage
        for v in violations:
            print(f"[WARN] Attribution Notice: {v}", file=sys.stderr)
    return True


def verify_author_attribution(repo_root: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validates that the repository preserves the author attribution required by MIT license.
    Returns (is_valid, list_of_violations).
    """
    root = repo_root or DEFAULT_REPO_ROOT
    violations: List[str] = []

    # 1. Check LICENSE file
    license_path = os.path.join(root, "LICENSE")
    if not os.path.exists(license_path):
        violations.append("Missing LICENSE file. MIT License with author copyright notice is mandatory.")
    else:
        try:
            with open(license_path, "r", encoding="utf-8", errors="ignore") as f:
                lic_content = f.read()
            if ORIGINAL_AUTHOR_NAME not in lic_content or ORIGINAL_AUTHOR_HANDLE not in lic_content:
                violations.append("LICENSE file modified: original copyright notice for 'Thế Vị (@TeeVee998)' was removed or altered.")
            if ORIGINAL_REPO_URL not in lic_content:
                violations.append("LICENSE file modified: original repository URL was removed.")
        except Exception as e:
            violations.append(f"Could not read LICENSE file: {e}")

    # 2. Check package.json
    pkg_path = os.path.join(root, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                pkg_data = json.load(f)
            author_val = str(pkg_data.get("author", ""))
            if ORIGINAL_AUTHOR_NAME not in author_val or "TeeVee998" not in author_val:
                violations.append("package.json modified: 'author' field does not credit 'Thế Vị (@TeeVee998)'.")
        except Exception as e:
            violations.append(f"Could not read package.json: {e}")

    # 3. Check README.md
    readme_path = os.path.join(root, "README.md")
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                readme_content = f.read()
            if ORIGINAL_AUTHOR_NAME not in readme_content or ORIGINAL_AUTHOR_HANDLE not in readme_content:
                violations.append("README.md modified: author attribution for 'Thế Vị (@TeeVee998)' was removed.")
            if "TeeVee998/Synapse-Hub" not in readme_content:
                violations.append("README.md modified: upstream repository provenance link was removed.")
        except Exception as e:
            violations.append(f"Could not read README.md: {e}")

    # 4. Check pyproject.toml
    pyproject_path = os.path.join(root, "pyproject.toml")
    if os.path.exists(pyproject_path):
        try:
            with open(pyproject_path, "r", encoding="utf-8", errors="ignore") as f:
                pyproj_content = f.read()
            if ORIGINAL_AUTHOR_NAME not in pyproj_content:
                violations.append("pyproject.toml modified: author declaration does not include 'Thế Vị'.")
        except Exception as e:
            violations.append(f"Could not read pyproject.toml: {e}")

    is_valid = len(violations) == 0
    return is_valid, violations


def enforce_author_attribution(repo_root: Optional[str] = None, strict: bool = True) -> bool:
    """
    Enforces author attribution at runtime. If attribution is violated,
    displays a transparent copyright notice and halts execution if strict=True.
    """
    is_valid, violations = verify_author_attribution(repo_root)
    if not is_valid:
        CYAN = "\033[96m"
        RED = "\033[91m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        print(f"\n{BOLD}{RED}======================================================================{RESET}", file=sys.stderr)
        print(f"{BOLD}{RED}  🛑 [AUTHOR ATTRIBUTION & INTEGRITY VIOLATION DETECTED]               {RESET}", file=sys.stderr)
        print(f"{BOLD}{RED}======================================================================{RESET}", file=sys.stderr)
        print(f"{BOLD}Original Creator & Copyright Holder:{RESET} {ORIGINAL_AUTHOR_NAME} ({ORIGINAL_AUTHOR_HANDLE})", file=sys.stderr)
        print(f"{BOLD}Original Project Repository        :{RESET} {ORIGINAL_REPO_URL}", file=sys.stderr)
        print(f"{BOLD}Legal Notice                       :{RESET} Under the MIT License, you are free to use,", file=sys.stderr)
        print("                                     modify, and distribute this software, PROVIDED", file=sys.stderr)
        print("                                     that the original copyright notice is preserved.", file=sys.stderr)
        print("\nViolations detected:", file=sys.stderr)
        for v in violations:
            print(f"  • {v}", file=sys.stderr)
        print(f"\n{CYAN}👉 Please restore original author attribution to continue using Synapse Hub.{RESET}", file=sys.stderr)
        print(f"{RED}======================================================================{RESET}\n", file=sys.stderr)

        if strict:
            sys.exit(1)
        return False
    return True


if __name__ == "__main__":
    valid, viols = verify_author_attribution()
    if valid:
        print(f"✅ Author attribution is 100% verified intact: {get_canonical_watermark()}")
        sys.exit(0)
    else:
        enforce_author_attribution(strict=True)
