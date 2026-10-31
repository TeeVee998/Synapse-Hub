#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Thế Vị (@TeeVee998). All rights reserved.
# SPDX-License-Identifier: MIT
# Project: Synapse-Hub (https://github.com/TeeVee998/Synapse-Hub)

"""
tools/watch_mode.py — Incremental Watch Mode & Real-Time Test Engineering HUD
----------------------------------------------------------------------------
Continuously monitors target repository files for code changes and triggers
near-instant (< 100ms) incremental verification:
  1. UTF-8 No BOM validation
  2. Forbidden machine absolute path scan
  3. AST Static Defect / Fake-Pass Sentinel (Meta Infer-style)
  4. POM & Test Impact Blast Radius Scoping

Usage:
  python3 tools/watch_mode.py [target]
  python3 tools/watch_mode.py [target] --debounce 0.8
  python3 tools/watch_mode.py [target] --once
"""

import os
import sys
import time
import glob
import re
import argparse
from datetime import datetime
from typing import Dict, Set, List, Optional, Tuple

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

WATCH_EXTENSIONS = (
    ".groovy", ".tc", ".ts", ".js", ".py", ".glbl", ".json", ".feature", ".md"
)

IGNORED_DIRS = {
    ".git", ".gradle", "node_modules", "allure-results", "Screenshots",
    "Reports", "reports", "TestReports", "testreports", "bin", "Libs", ".settings",
    "graphify-out", "__pycache__", "agent_qa.egg-info", "dist", "build", ".pytest_cache"
}

IGNORED_FILES = {
    ".project", ".classpath", ".DS_Store", "memory_cache.db",
    "verify_all.py", "git_pre_commit_guard.py", "agent_canary.py", "watch_mode.py",
    "repo_map.txt", "repo_map.json", "PROJECT_HEALTH_REPORT.md", "PROJECT_STATE.md"
}

FORBIDDEN_PATH_PATTERNS = [
    (re.compile(r'file:///[a-zA-Z]:', re.IGNORECASE), "Machine file URI (file:///...)"),
    (re.compile(r'\b[a-zA-Z]:\\Users\\[a-zA-Z0-9_\-]+\\', re.IGNORECASE), "Windows User directory path"),
    (re.compile(r'\b/Users/[a-zA-Z0-9_\-]+/', re.IGNORECASE), "macOS/Unix User directory path"),
]

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
DIM = "\033[2m"


def check_file_bom(file_path: str) -> bool:
    """Returns True if file has UTF-8 BOM bytes."""
    try:
        with open(file_path, "rb") as fp:
            return fp.read(3) == b"\xef\xbb\xbf"
    except Exception:
        return False


def check_forbidden_paths(file_path: str) -> List[Tuple[int, str]]:
    """Returns list of (line_no, description) of forbidden absolute machine paths."""
    fname = os.path.basename(file_path)
    if fname in IGNORED_FILES:
        return []

    violations = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
            for line_no, line in enumerate(fp, 1):
                for pattern, desc in FORBIDDEN_PATH_PATTERNS:
                    if pattern.search(line):
                        violations.append((line_no, desc))
    except Exception:
        pass
    return violations


def run_incremental_linter(file_path: str) -> Tuple[bool, str]:
    """Runs fast AST check on modified script."""
    infer_script = os.path.join(SCRIPT_DIR, "infer_linter.py")
    if not os.path.exists(infer_script):
        return True, "infer_linter not found"

    try:
        import subprocess
        res = subprocess.run(
            [sys.executable, infer_script, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            return True, "Clean (0 AST Defects / 0 Fake Passes)"
        else:
            return False, res.stdout.strip() or res.stderr.strip()
    except Exception as e:
        return False, str(e)


def run_incremental_audit(file_path: str, target_dir: str) -> Dict[str, Any]:
    """Performs fast sub-100ms audit on a single changed file."""
    start_t = time.perf_counter()
    rel_path = os.path.relpath(file_path, target_dir)
    results = {
        "file": rel_path,
        "bom_pass": True,
        "path_pass": True,
        "lint_pass": True,
        "details": [],
        "duration_ms": 0.0
    }

    # 1. BOM Check
    if check_file_bom(file_path):
        results["bom_pass"] = False
        results["details"].append("UTF-8 BOM detected (Must be 100% UTF-8 No BOM)")

    # 2. Path Portability Check
    path_issues = check_forbidden_paths(file_path)
    if path_issues:
        results["path_pass"] = False
        for lno, desc in path_issues:
            results["details"].append(f"Line {lno}: {desc}")

    # 3. Incremental AST Linter for test automation scripts (e.g. Scripts/ in target projects)
    # Skip python unittests in hub tests/ directory
    norm_rel = rel_path.replace("\\", "/")
    is_target_script = norm_rel.startswith("Scripts/") or ("/Scripts/" in norm_rel)
    if is_target_script and file_path.endswith((".groovy", ".ts", ".js", ".py")):
        lint_ok, lint_msg = run_incremental_linter(file_path)
        if not lint_ok:
            results["lint_pass"] = False
            results["details"].append(f"AST Linter: {lint_msg}")

    results["duration_ms"] = round((time.perf_counter() - start_t) * 1000, 2)
    return results


def print_hud_banner(target_dir: str):
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}     ⚡ SYNAPSE-HUB REAL-TIME WATCH MODE SENTINEL (INCREMENTAL HUD)   {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{DIM}Watching directory : {RESET}{BOLD}{target_dir}{RESET}")
    print(f"{DIM}Monitored types    : {RESET}{CYAN}{', '.join(WATCH_EXTENSIONS)}{RESET}")
    print(f"{DIM}Trigger checks     : {RESET}UTF-8 No BOM, Absolute Paths, AST Fake-Pass Sentinel")
    print(f"{DIM}Press {RESET}{BOLD}Ctrl+C{RESET}{DIM} to pause or stop watching.\n{RESET}")


def print_audit_result(res: Dict[str, Any]):
    timestamp = datetime.now().strftime("%H:%M:%S")
    rel_path = res["file"]
    duration = res["duration_ms"]
    all_clean = res["bom_pass"] and res["path_pass"] and res["lint_pass"]

    if all_clean:
        print(f"[{timestamp}] {GREEN}✓ PASS{RESET} {BOLD}{rel_path}{RESET} {DIM}({duration}ms){RESET}")
    else:
        print(f"[{timestamp}] {RED}✗ FAIL{RESET} {BOLD}{rel_path}{RESET} {DIM}({duration}ms){RESET}")
        for d in res["details"]:
            print(f"   {RED}↳ {d}{RESET}")


def scan_file_states(target_dir: str) -> Dict[str, float]:
    """Scans all eligible files and records their mtime."""
    file_states = {}
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            if f.endswith(WATCH_EXTENSIONS):
                full_path = os.path.join(root, f)
                try:
                    file_states[full_path] = os.path.getmtime(full_path)
                except OSError:
                    pass
    return file_states


def watch_directory(target_dir: str, debounce: float = 0.8, run_once: bool = False) -> int:
    """Main watch loop with debouncing."""
    target_dir = os.path.abspath(target_dir)
    print_hud_banner(target_dir)

    known_states = scan_file_states(target_dir)
    print(f"{GREEN}● Watchdog active:{RESET} Indexed {len(known_states)} files. Ready for file changes...\n")

    if run_once:
        print(f"{CYAN}[ONCE MODE]{RESET} Executing one-time scan across {len(known_states)} indexed files...")
        failures = 0
        for fpath in sorted(known_states.keys()):
            res = run_incremental_audit(fpath, target_dir)
            if not (res["bom_pass"] and res["path_pass"] and res["lint_pass"]):
                print_audit_result(res)
                failures += 1
        if failures == 0:
            print(f"\n{GREEN}✅ [ALL PASS]{RESET} 100% of {len(known_states)} files passed incremental sentinel checks.")
            return 0
        else:
            print(f"\n{RED}❌ [FAIL]{RESET} {failures} files violated Quality Gates.")
            return 1

    try:
        while True:
            time.sleep(debounce)
            current_states = scan_file_states(target_dir)
            changed_files = []

            for fpath, mtime in current_states.items():
                if fpath not in known_states:
                    changed_files.append((fpath, "CREATED"))
                elif mtime > known_states[fpath]:
                    changed_files.append((fpath, "MODIFIED"))

            known_states = current_states

            if changed_files:
                for fpath, change_type in changed_files:
                    res = run_incremental_audit(fpath, target_dir)
                    print_audit_result(res)

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}🛑 [WATCH STOPPED]{RESET} Exiting Watch Mode Sentinel.")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Real-Time Incremental Watch Mode Sentinel")
    parser.add_argument("target", nargs="?", default=".", help="Directory to monitor (default: current directory)")
    parser.add_argument("--debounce", type=float, default=0.8, help="Debounce interval in seconds (default: 0.8)")
    parser.add_argument("--once", action="store_true", help="Run incremental scan once on all files and exit")
    args = parser.parse_args()

    return watch_directory(target_dir=args.target, debounce=args.debounce, run_once=args.once)


if __name__ == "__main__":
    sys.exit(main())
