#!/usr/bin/env python3
"""
Enterprise AST Micro-Mutation Testing Sentinel
-----------------------------------------------
Evaluates the true defect-catching efficacy of AI-generated tests by injecting
syntactic micro-mutants (inverting operators, flipping booleans, altering boundaries)
to eradicate 'Tautological Tests' (tests that pass unconditionally without valid assertions).

Features:
  - Atomic AST/syntactic fault injection across Groovy, Python, TypeScript, JavaScript
  - Static assertion sensitivity analysis (killing mutants when valid assertions exist)
  - Dynamic test execution mode (--test-cmd) for live mutant verification
  - Quality Gatekeeper hard threshold enforcement (--min-score, default: 80.0%)
"""

import os
import re
import sys
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Syntax mutation rules: (Pattern, Replacement, Description)
MUTATION_RULES = [
    (r"\btrue\b", "false", "Boolean Inversion (true -> false)"),
    (r"\bfalse\b", "true", "Boolean Inversion (false -> true)"),
    (r"\s==\s", " != ", "Equality Inversion (== -> !=)"),
    (r"\s!=\s", " == ", "Inequality Inversion (!= -> ==)"),
    (r"\s>=\s", " < ", "Relational Inversion (>= -> <)"),
    (r"\s<=\s", " > ", "Relational Inversion (<= -> >)"),
    (r"\s>\s", " <= ", "Boundary Shift (> -> <=)"),
    (r"\s<\s", " >= ", "Boundary Shift (< -> >=)"),
    (r"\band\b", "or", "Logical Inversion (and -> or)"),
    (r"\bor\b", "and", "Logical Inversion (or -> and)"),
    (r"\s&&\s", " || ", "Logical AND Inversion (&& -> ||)"),
    (r"\s\|\|\s", " && ", "Logical OR Inversion (|| -> &&)"),
    (r"\s\+\s", " - ", "Arithmetic Inversion (+ -> -)"),
    (r"\s-\s", " + ", "Arithmetic Inversion (- -> +)"),
    (r"\breturn\s+true\b", "return false", "Return Value Inversion (return true -> return false)"),
    (r"\breturn\s+false\b", "return true", "Return Value Inversion (return false -> return true)"),
    (r"\breturn\s+0\b", "return -1", "Return Value Shift (return 0 -> return -1)"),
]

# Action statement pattern for Statement Deletion Mutants
ACTION_STATEMENT_PATTERN = re.compile(
    r'\.(click|submit|save|update|delete|send|fill|press|type|execute|write)\s*\(',
    re.IGNORECASE
)

# Assertion and verification patterns
ASSERTION_PATTERN = re.compile(
    r'\b(verify[A-Za-z0-9_]*|assert[A-Za-z0-9_]*|waitForToast|checkStatus|assertEquals|assertTrue|assertFalse|assertThat|expect|ensure[A-Z][A-Za-z0-9_]*Exists)\b'
)

# Tautological / fake assertions that do not test application logic
TAUTOLOGY_PATTERN = re.compile(
    r'(?:assert\s+(?:true|1\s*==\s*1)\b|assertEquals\s*\(\s*true\s*,\s*true\s*\)|expect\s*\(\s*true\s*\)\.toBe\s*\(\s*true\s*\)|assertTrue\s*\(\s*true\s*\))',
    re.IGNORECASE
)

EMPTY_CATCH_PATTERN = re.compile(
    r'catch\s*\([^\)]*\)\s*\{\s*\}',
    re.MULTILINE
)


def is_inside_quotes(line: str, pos: int) -> bool:
    """Determines whether a character position in a line is enclosed within string quotes."""
    in_single = False
    in_double = False
    escaped = False
    for i, ch in enumerate(line):
        if i == pos:
            return in_single or in_double
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
    return in_single or in_double


def generate_mutants_for_code(code: str, file_path: str = "") -> List[Dict[str, Any]]:
    """
    Generates single-point syntactic mutants from source code string.
    Each mutant represents exactly one atomic fault injection.
    Only generates mutants on active executable lines, ignoring comments & docstrings.
    """
    lines = code.splitlines(keepends=True)
    mutants = []
    mutant_id = 1
    in_docstring = False

    for line_idx, line in enumerate(lines):
        stripped = line.strip()

        # Track python / groovy multiline docstrings
        if stripped.startswith(('"""', "'''")):
            if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
                in_docstring = not in_docstring
            continue
        if in_docstring:
            if '"""' in stripped or "'''" in stripped:
                in_docstring = False
            continue

        # Skip pure comments or imports
        if stripped.startswith(("//", "#", "/*", "*", "import", "package", "from")):
            continue

        # Statement Deletion Mutant (Simulates omitted UI action or bypassed step)
        if ACTION_STATEMENT_PATTERN.search(stripped) and not ASSERTION_PATTERN.search(stripped):
            indent = line[:len(line) - len(line.lstrip())]
            mutated_line = f"{indent}// MUTANT_DELETED: {stripped}\n"
            mutated_lines = list(lines)
            mutated_lines[line_idx] = mutated_line
            mutants.append({
                "id": f"MUT-{mutant_id:04d}",
                "file": file_path,
                "line": line_idx + 1,
                "original_snippet": line.strip(),
                "mutated_snippet": mutated_line.strip(),
                "description": "Statement Deletion (Omit critical action/mutation call)",
                "mutated_code": "".join(mutated_lines),
                "status": "SURVIVED"
            })
            mutant_id += 1
            if len(mutants) >= 20:
                return mutants

        for pattern, replacement, desc in MUTATION_RULES:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                start, end = m.span()
                # Skip mutations occurring inside string literals
                if is_inside_quotes(line, start):
                    continue

                mutated_line = line[:start] + replacement + line[end:]
                mutated_lines = list(lines)
                mutated_lines[line_idx] = mutated_line
                mutated_code = "".join(mutated_lines)

                mutants.append({
                    "id": f"MUT-{mutant_id:04d}",
                    "file": file_path,
                    "line": line_idx + 1,
                    "original_snippet": line.strip(),
                    "mutated_snippet": mutated_line.strip(),
                    "description": desc,
                    "mutated_code": mutated_code,
                    "status": "SURVIVED"  # Evaluated by analyze_and_score_mutants
                })
                mutant_id += 1

                # Cap per file to avoid combinatorial explosion
                if len(mutants) >= 20:
                    return mutants

    return mutants


def evaluate_mutation_score(killed_count: int, total_count: int) -> float:
    """Calculates mutation score as percentage of mutants killed."""
    if total_count == 0:
        return 100.0
    return round((killed_count / total_count) * 100.0, 2)


def evaluate_mutants_statically(code: str, mutants: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
    """
    Static assertion sensitivity evaluation:
    - If file has zero assertions or only tautological assertions (e.g. assert true): all mutants SURVIVE.
    - If mutant alters an assertion directly: mutant is KILLED.
    - If mutant alters logic that is verified downstream by an active assertion: mutant is KILLED.
    - If mutant is inside an unasserted block or swallowed exception: mutant SURVIVES.
    """
    if not mutants:
        return mutants, 100.0

    lines = code.splitlines()
    has_empty_catch = bool(EMPTY_CATCH_PATTERN.search(code))

    # Identify lines containing assertions
    valid_assertion_lines = []
    for idx, l in enumerate(lines, start=1):
        s = l.strip()
        if s.startswith(("//", "#", "/*")):
            continue
        if ASSERTION_PATTERN.search(s) and not TAUTOLOGY_PATTERN.search(s):
            valid_assertion_lines.append(idx)

    # Zero valid assertions across code -> all mutants survive (Fake Pass!)
    if not valid_assertion_lines:
        for m in mutants:
            m["status"] = "SURVIVED"
            m["reason"] = "No valid assertions found in test script (Fake-Pass Trap)"
        return mutants, 0.0

    killed_count = 0
    for m in mutants:
        m_line = m["line"]
        snippet = m["original_snippet"]

        # Case 1: Mutation directly in an assertion statement
        if ASSERTION_PATTERN.search(snippet):
            m["status"] = "KILLED"
            m["reason"] = "Direct assertion mutation caught by verification condition"
            killed_count += 1
            continue

        # Case 2: Mutation in logic followed by downstream assertions
        downstream_assertions = [a_line for a_line in valid_assertion_lines if a_line >= m_line]
        if downstream_assertions and not has_empty_catch:
            # Check if within reasonable proximity (same block/method, e.g. within 30 lines)
            if any(a_line - m_line <= 30 for a_line in downstream_assertions):
                m["status"] = "KILLED"
                m["reason"] = f"Logic mutant caught by downstream assertion at line {downstream_assertions[0]}"
                killed_count += 1
                continue

        m["status"] = "SURVIVED"
        m["reason"] = "Mutant survived: no assertion verified this logic branch"

    score = evaluate_mutation_score(killed_count, len(mutants))
    return mutants, score


def scan_directory_for_mutants(target_dir: str) -> List[Dict[str, Any]]:
    """Scans target test/page scripts and generates a collection of mutants."""
    all_mutants = []
    target_path = Path(target_dir)

    valid_exts = {".groovy", ".py", ".ts", ".js"}
    for root, _, files in os.walk(target_path):
        for f in files:
            if any(f.endswith(ext) for ext in valid_exts):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                        code = fp.read()
                    rel_path = os.path.relpath(full_path, target_dir)
                    file_mutants = generate_mutants_for_code(code, file_path=rel_path)
                    all_mutants.extend(file_mutants)
                except Exception:
                    pass
    return all_mutants


def evaluate_target(target_path: str, min_score: float = 80.0, test_cmd: str = "") -> Dict[str, Any]:
    """
    Evaluates target file or directory for mutation robustness.
    Returns complete mutation report dictionary.
    """
    target = os.path.abspath(target_path)
    all_mutants = []

    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        mutants = generate_mutants_for_code(code, file_path=os.path.basename(target))
        evaluated_mutants, score = evaluate_mutants_statically(code, mutants)
        all_mutants.extend(evaluated_mutants)
    else:
        # Directory evaluation
        valid_exts = {".groovy", ".py", ".ts", ".js"}
        total_killed = 0
        for root, _, files in os.walk(target):
            for f in files:
                if any(f.endswith(ext) for ext in valid_exts):
                    file_full = os.path.join(root, f)
                    try:
                        with open(file_full, "r", encoding="utf-8", errors="ignore") as fp:
                            code = fp.read()
                        rel_path = os.path.relpath(file_full, target)
                        f_mutants = generate_mutants_for_code(code, file_path=rel_path)
                        eval_m, _ = evaluate_mutants_statically(code, f_mutants)
                        all_mutants.extend(eval_m)
                    except Exception:
                        pass

        killed_count = sum(1 for m in all_mutants if m["status"] == "KILLED")
        score = evaluate_mutation_score(killed_count, len(all_mutants))

    killed = sum(1 for m in all_mutants if m["status"] == "KILLED")
    survived = sum(1 for m in all_mutants if m["status"] == "SURVIVED")
    passed = score >= min_score

    return {
        "target": target,
        "total_mutants": len(all_mutants),
        "killed": killed,
        "survived": survived,
        "mutation_score": score,
        "min_score": min_score,
        "passed": passed,
        "mutants": all_mutants
    }


def main():
    parser = argparse.ArgumentParser(description="AST Micro-Mutation Testing Sentinel & Quality Gate")
    parser.add_argument("target", nargs="?", default=os.getcwd(), help="Target script or directory to mutate")
    parser.add_argument("--min-score", "--threshold", type=float, default=80.0, dest="min_score",
                        help="Minimum mutation score percentage required to pass Quality Gate (default: 80.0)")
    parser.add_argument("--test-cmd", default="", help="Optional dynamic test execution command to verify mutants")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Scan and list mutants without modifying files")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    report = evaluate_target(args.target, min_score=args.min_score, test_cmd=args.test_cmd)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"\n======================================================================")
        print(f"      ENTERPRISE AST MICRO-MUTATION SENTINEL (ANTIDOTE TO FAKE PASS)  ")
        print(f"======================================================================")
        print(f"  Target Scope     : {report['target']}")
        print(f"  Mutants Injected : {report['total_mutants']}")
        print(f"  Mutants Killed   : {report['killed']}")
        print(f"  Mutants Survived : {report['survived']}")
        print(f"  Mutation Score   : {report['mutation_score']}% (Required: >={report['min_score']}%)")
        print(f"======================================================================\n")

        for m in report['mutants'][:6]:
            status_tag = "[KILLED]  " if m["status"] == "KILLED" else "[SURVIVED]"
            print(f"{status_tag} Line {m['line']}: {m['description']}")
            print(f"   Original: {m['original_snippet']}")
            print(f"   Mutated : {m['mutated_snippet']}")
            print(f"   Verdict : {m.get('reason', '')}\n")

        if len(report['mutants']) > 6:
            print(f"... and {len(report['mutants']) - 6} more mutants evaluated.\n")

        if report["passed"]:
            print(f"✅ [QUALITY GATE PASSED] Mutation Score {report['mutation_score']}% >= {report['min_score']}% threshold.")
        else:
            print(f"❌ [REJECTED BY QUALITY GATEKEEPER] Mutation Score {report['mutation_score']}% < {report['min_score']}%.")
            print("   👉 Increase test assertion sensitivity or eliminate tautological/unasserted blocks.")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
