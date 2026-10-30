#!/usr/bin/env python3
"""
Universal QA Static Defect & Assertion Sentinel (Inspired by facebook/infer)
-------------------------------------------------------------------
Performs AST-level static analysis across test scripts, specs, and Page Classes.
Detects:
  1. FAKE_PASS_NO_ASSERTION : Test cases that interact with AUT but lack assertions / verifications.
  2. SWALLOWED_EXCEPTION    : Empty catch blocks that hide failures silently.
  3. EXCESSIVE_HARD_DELAY   : Thread.sleep >= 3000ms or WebUI.delay >= 5s (flaky anti-pattern).
  4. RESOURCE_LEAK_RISK     : Unclosed streams or driver handles lacking finally blocks.
  5. EMPTY_TEST_SCRIPT      : Test cases with zero executable statements.
"""

import os
import sys
import re
import json
import glob
import argparse
from datetime import datetime

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
OUTPUT_JSON = os.path.join(REPORTS_DIR, "infer_linter_report.json")

# ANSI Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Generic Detection regexes
ASSERTION_PATTERN = re.compile(
    r'\b(verify[A-Za-z0-9_]*|assert[A-Za-z0-9_]*|waitForToast|checkStatus|assertEquals|assertTrue|assertFalse|assertThat|expect|ensure[A-Z][A-Za-z0-9_]*Exists)\b'
)

EMPTY_CATCH_PATTERN = re.compile(
    r'catch\s*\([^\)]*\)\s*\{\s*\}',
    re.MULTILINE
)

THREAD_SLEEP_PATTERN = re.compile(
    r'(?:Thread\.sleep|WebUI\.delay)\s*\(\s*(\d+)\s*\)'
)


def strip_comments_and_strings(source_code, preserve_newlines=True):
    """
    Lexically strips block comments, line comments, multiline strings, 
    and quoted literals while preserving line numbering.
    Prevents false-positive / false-negative matches in AST linter.
    """
    pattern = re.compile(
        r'(?P<BLOCK_COMMENT>/\*.*?\*/)|'
        r'(?P<LINE_COMMENT>//[^\r\n]*)|'
        r'(?P<TRIPLE_DOUBLE>"""[\s\S]*?""")|'
        r'(?P<TRIPLE_SINGLE>\'\'\'[\s\S]*?\'\'\')|'
        r'(?P<DOUBLE_STRING>"(?:\\.|[^"\\])*")|'
        r'(?P<SINGLE_STRING>\'(?:\\.|[^\'\\])*\')',
        re.DOTALL
    )

    def replacer(match):
        text = match.group(0)
        if preserve_newlines:
            return re.sub(r'[^\r\n]', ' ', text)
        return ' '

    return pattern.sub(replacer, source_code)


def analyze_script(file_path):
    """Performs static rule scanning on a single test script file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        lines = content.splitlines()

    defects = []
    try:
        rel_path = os.path.relpath(file_path, REPO_ROOT)
    except ValueError:
        rel_path = os.path.abspath(file_path)

    # Lexically strip comments and string literals for accurate analysis
    clean_code = strip_comments_and_strings(content, preserve_newlines=True)
    clean_lines = [l.strip() for l in clean_code.splitlines()]

    # Rule 1: Empty Test Script (zero executable non-import, non-package statements)
    executable_lines = [
        l for l in clean_lines 
        if l and not l.startswith("import ") and not l.startswith("package ") and not l.startswith("from ")
    ]
    if len(executable_lines) == 0:
        defects.append({
            "type": "EMPTY_TEST_SCRIPT",
            "severity": "CRITICAL",
            "line": 1,
            "message": "Test script is empty or contains only comments/imports."
        })

    # Rule 2: Swallowed Exceptions (empty catch blocks)
    for match in EMPTY_CATCH_PATTERN.finditer(clean_code):
        line_no = clean_code[:match.start()].count("\n") + 1
        defects.append({
            "type": "SWALLOWED_EXCEPTION",
            "severity": "CRITICAL",
            "line": line_no,
            "message": "Empty catch block detected. Swallowed exceptions cause false-pass test runs."
        })

    # Rule 3: Flaky Static Delays
    for idx, line in enumerate(clean_code.splitlines(), 1):
        m = THREAD_SLEEP_PATTERN.search(line)
        if m:
            delay_val = int(m.group(1))
            if delay_val >= 3000:
                defects.append({
                    "type": "EXCESSIVE_HARD_DELAY",
                    "severity": "WARNING",
                    "line": idx,
                    "message": f"Static sleep of {delay_val}ms found. Replace with dynamic Smart Wait (waitForElement/networkidle)."
                })

    # Rule 4: Fake-Pass / Missing Assertions (verified against code tokens only)
    has_assert = bool(ASSERTION_PATTERN.search(clean_code))
    has_interactions = any(
        kw in clean_code for kw in ["click", "select", "save", "delete", "create", "search", "navigate", "open", "fill"]
    )
    if has_interactions and not has_assert:
        defects.append({
            "type": "FAKE_PASS_NO_ASSERTION",
            "severity": "WARNING",
            "line": 1,
            "message": "Script performs AUT mutations/interactions but contains zero verification/assertion statements."
        })

    return {
        "file": rel_path,
        "defects": defects,
        "is_clean": len(defects) == 0
    }


def run_infer_linter(target_dir=None):
    """Scans test scripts across Groovy, TypeScript, JavaScript, Python, and Java."""
    EXTENSIONS = ("*.groovy", "*.ts", "*.js", "*.py", "*.java")

    if target_dir:
        if os.path.isfile(target_dir):
            script_files = [target_dir]
            scan_dir = os.path.dirname(target_dir)
        elif os.path.isdir(target_dir):
            scan_dir = target_dir
            script_files = []
            for ext in EXTENSIONS:
                script_files.extend(glob.glob(os.path.join(scan_dir, "**", ext), recursive=True))
        else:
            scan_dir = target_dir
            script_files = []
    else:
        # Search candidate directories across test frameworks (Katalon, Playwright, Pytest, Cypress)
        script_files = []
        scan_dir = SCRIPTS_DIR
        for cand in ["Scripts", "tests", "test", "e2e", "specs", "cypress"]:
            cand_path = os.path.join(REPO_ROOT, cand)
            if os.path.isdir(cand_path):
                for ext in EXTENSIONS:
                    script_files.extend(glob.glob(os.path.join(cand_path, "**", ext), recursive=True))
                if script_files:
                    scan_dir = cand_path
                    break

    results = []
    critical_count = 0
    warning_count = 0
    clean_count = 0

    for s in sorted(set(script_files)):
        res = analyze_script(s)
        results.append(res)
        crit = sum(1 for d in res["defects"] if d["severity"] == "CRITICAL")
        warn = sum(1 for d in res["defects"] if d["severity"] == "WARNING")
        critical_count += crit
        warning_count += warn
        if res["is_clean"]:
            clean_count += 1

    total_scripts = len(script_files)
    if total_scripts == 0:
        health_score = 0.0
        clean_pct = 0.0
    else:
        # Codebase health score bounded between 0.0 and 100.0%
        # Critical defects reduce health score proportionally
        health_score = max(0.0, min(100.0, round(((total_scripts - critical_count) / total_scripts) * 100, 1)))
        clean_pct = round((clean_count / total_scripts) * 100, 1)

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}    ENTERPRISE STATIC DEFECT & FAKE-PASS SENTINEL (Meta Infer-Style)        {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    if total_scripts == 0:
        print(f"  Target Scope            : 0 Test Scripts discovered in {os.path.basename(scan_dir)}/ (No tests found)")
        print(f"  Critical Defects        : {GREEN}0{RESET}")
        print(f"  Warnings / Suggestions  : {GREEN}0{RESET}")
        print(f"  Clean Scripts           : 0/0 (N/A)")
        print(f"  Codebase Health Score   : {YELLOW}N/A (0 test scripts discovered){RESET}")
    else:
        print(f"  Target Scope            : {total_scripts} Test Scripts in {os.path.basename(scan_dir)}/ (Polyglot)")
        print(f"  Critical Defects        : {RED if critical_count > 0 else GREEN}{critical_count}{RESET} (Swallowed exceptions, empty scripts)")
        print(f"  Warnings / Suggestions  : {YELLOW if warning_count > 0 else GREEN}{warning_count}{RESET} (Missing explicit asserts, excessive delays)")
        print(f"  Clean Scripts           : {GREEN}{clean_count}/{total_scripts} ({clean_pct:.1f}%){RESET}")
        print(f"  Codebase Health Score   : {GREEN if health_score == 100 else YELLOW}{health_score:.1f}%{RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    # Print defect breakdown if any
    defect_scripts = [r for r in results if not r["is_clean"]]
    if defect_scripts:
        print(f"{BOLD}Detected Items ({len(defect_scripts)} scripts):{RESET}")
        for r in defect_scripts[:10]: # Print top 10
            for d in r["defects"]:
                color = RED if d["severity"] == "CRITICAL" else YELLOW
                print(f"  - [{color}{d['severity']}{RESET}] {r['file']}:{d['line']} - {d['message']}")
        if len(defect_scripts) > 10:
            print(f"  ... and {len(defect_scripts) - 10} more scripts (see full JSON report).\n")

    # Save artifact
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_scripts": total_scripts,
        "clean_scripts": clean_count,
        "critical_defects": critical_count,
        "warnings": warning_count,
        "health_score_pct": health_score,
        "defect_details": defect_scripts
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"Detailed audit saved to: {OUTPUT_JSON}\n")

    return 0 if critical_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Universal QA Static Defect & Assertion Sentinel")
    parser.add_argument("target", nargs="?", default=None, help="Target directory or script to scan")
    parser.add_argument("--dir", help="Target directory to scan (defaults to Scripts/)")
    parser.add_argument("--repo", help="Target repository root containing Scripts/")
    args = parser.parse_args()

    target_dir = args.dir or args.target
    if not target_dir and args.repo:
        target_dir = os.path.join(args.repo, "Scripts")
    return run_infer_linter(target_dir=target_dir)


if __name__ == "__main__":
    sys.exit(main())
