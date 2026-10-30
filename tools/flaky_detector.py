#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Flaky Test Detector & Quarantine Sentinel
---------------------------------------------------
Executes a target test scenario N times (default: 5) or parses historical JUnit XML
reports to calculate the Flakiness Index, detect state flips, query persistent SQLite telemetry,
and automatically isolate unstable tests via source-code @quarantine annotation.

Features:
  1. Multi-Run Repeat Execution & Live State-Flip Detection
  2. Multi-Day Historical Telemetry Query from memory_cache.db
  3. Automatic Source Code Isolation (--isolate) across Groovy, TS, Python test scripts
  4. Quarantine Board JSON & Allure/CI metadata export
"""

import os
import re
import sys
import glob
import json
import time
import shlex
import argparse
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from cache_resolver import record_test_telemetry, get_flaky_telemetry
except ImportError:
    record_test_telemetry = None
    get_flaky_telemetry = None

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_command(cmd: str, timeout: int = 300) -> Tuple[int, str, str, float]:
    """Executes a command safely without shell=True and returns (returncode, stdout, stderr, elapsed_ms)."""
    start = time.time()
    try:
        args = shlex.split(cmd, posix=sys.platform != "win32")
        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return res.returncode, res.stdout, res.stderr, elapsed_ms
    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return -1, "", "Execution timed out", elapsed_ms


def calculate_flakiness(runs: List[bool]) -> Dict[str, Any]:
    """
    Given a list of boolean statuses [True, False, True, ...],
    calculates pass rate, flip count, and flakiness tier.
    """
    total = len(runs)
    if total == 0:
        return {
            "total": 0,
            "passes": 0,
            "failures": 0,
            "pass_rate": 0.0,
            "flips": 0,
            "flaky_ratio": 0.0,
            "status": "NO_DATA",
            "quarantine": False
        }

    passes = sum(1 for r in runs if r)
    failures = total - passes
    pass_rate = round((passes / total) * 100, 1)

    # Count transitions (Pass -> Fail or Fail -> Pass)
    flips = 0
    for i in range(len(runs) - 1):
        if runs[i] != runs[i + 1]:
            flips += 1

    flaky_ratio = round((flips / max(1, total - 1)), 3) if total > 1 else (0.0 if failures == 0 else 1.0)

    if pass_rate == 100.0:
        status = "STABLE"
        quarantine = False
    elif pass_rate == 0.0:
        status = "DETERMINISTIC_FAIL"
        quarantine = False
    elif pass_rate >= 80.0:
        status = "MILD_FLAKE"
        quarantine = (flips >= 2 or flaky_ratio >= 0.15)
    else:
        status = "SEVERE_FLAKE"
        quarantine = True

    return {
        "total": total,
        "passes": passes,
        "failures": failures,
        "pass_rate": pass_rate,
        "flips": flips,
        "flaky_ratio": flaky_ratio,
        "status": status,
        "quarantine": quarantine
    }


def parse_junit_reports(glob_pattern: str) -> Dict[str, List[bool]]:
    """Parses JUnit XML report files and aggregates pass/fail counts by test case."""
    test_results: Dict[str, List[bool]] = {}
    files = glob.glob(glob_pattern, recursive=True)
    if not files:
        print(f"⚠️  No JUnit XML reports found matching: {glob_pattern}")
        return test_results

    for f in files:
        try:
            tree = ET.parse(f)
            root = tree.getroot()
            for tc in root.iter("testcase"):
                name = tc.attrib.get("name", "unknown")
                classname = tc.attrib.get("classname", "")
                full_id = f"{classname}#{name}" if classname else name
                has_failure = tc.find("failure") is not None or tc.find("error") is not None
                is_passed = not has_failure
                test_results.setdefault(full_id, []).append(is_passed)
        except Exception as e:
            print(f"⚠️  Could not parse {f}: {e}")

    return test_results


def benchmark_live_command(cmd: str, iterations: int = 5, test_id: Optional[str] = None) -> Dict[str, Any]:
    """Executes a live test command N times to observe flakiness in real time."""
    effective_id = test_id or f"CMD_{abs(hash(cmd)) % 100000}"
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      ENTERPRISE FLAKY TEST SENTINEL (Multi-Run Verification)        {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Target Command     : {cmd}")
    print(f"  Test Identifier    : {effective_id}")
    print(f"  Repetition Count   : {iterations} consecutive iterations")
    print(f"  Timestamp          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    runs = []
    latencies = []
    for i in range(1, iterations + 1):
        sys.stdout.write(f"  [Run {i}/{iterations}] Executing... ")
        sys.stdout.flush()
        code, stdout, stderr, ms = run_command(cmd)
        is_pass = (code == 0)
        runs.append(is_pass)
        latencies.append(ms)

        # Record to SQLite historical telemetry
        if record_test_telemetry:
            try:
                record_test_telemetry(
                    test_id=effective_id,
                    status="PASS" if is_pass else "FAIL",
                    is_retry=1 if i > 1 else 0,
                    duration_ms=ms,
                    error_signature="NON_ZERO_EXIT" if not is_pass else "",
                    context=cmd
                )
            except Exception:
                pass

        status_str = f"{GREEN}PASS{RESET}" if is_pass else f"{RED}FAIL (Exit {code}){RESET}"
        print(f"{status_str} ({ms} ms)")

    stats = calculate_flakiness(runs)
    stats["test_id"] = effective_id
    stats["latencies_ms"] = latencies
    stats["avg_latency_ms"] = round(sum(latencies) / max(1, len(latencies)), 2)
    stats["command"] = cmd

    # Print Scorecard
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}                   FLAKINESS DIAGNOSTIC SCORECARD                     {RESET}")
    print(f"{BOLD}======================================================================{RESET}")
    print(f"  Pass Rate          : {stats['pass_rate']}% ({stats['passes']}/{stats['total']} passes)")
    print(f"  Status Flips       : {stats['flips']} transitions")
    print(f"  Flaky Ratio        : {stats['flaky_ratio'] * 100:.1f}%")
    print(f"  Average Runtime    : {stats['avg_latency_ms']} ms")
    print(f"  Stability Status   : {stats['status']}")

    if stats["quarantine"]:
        print(f"  Recommendation     : {RED}{BOLD}[QUARANTINE REQUIRED]{RESET} Tag with @quarantine immediately!")
    else:
        print(f"  Recommendation     : {GREEN}[SUITE APPROVED]{RESET} Test is deterministic.")
    print(f"======================================================================\n")

    # Persist Report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_file = os.path.join(REPORTS_DIR, "quarantine_board.json")
    with open(report_file, "w", encoding="utf-8") as fp:
        json.dump(stats, fp, indent=2)
    print(f"Detailed telemetry saved to: {report_file}")

    return stats


def auto_quarantine_test_file(test_id: str, target_dir: str = ".") -> bool:
    """
    Searches repository test files and automatically annotates the flaky test method
    with @quarantine or @tag("quarantine") or test.fixme().
    """
    clean_id = test_id.split("#")[-1].strip()
    annotated = False

    for root, _, files in os.walk(target_dir):
        # Skip node_modules and dot folders
        if any(p in root for p in ("node_modules", ".git", "__pycache__", "reports")):
            continue

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in (".groovy", ".ts", ".js", ".py"):
                continue

            file_path = os.path.join(root, f)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()

                # If test_id matches file or method inside file
                if clean_id in content or f in test_id:
                    lines = content.splitlines(keepends=True)
                    new_lines = []
                    file_modified = False

                    for idx, line in enumerate(lines):
                        # Detect test declaration
                        if clean_id in line and not line.strip().startswith("//"):
                            # Check if already quarantined
                            if idx > 0 and "@quarantine" in lines[idx - 1]:
                                continue

                            # Inject quarantine tag based on language
                            indent = line[:len(line) - len(line.lstrip())]
                            if ext == ".groovy":
                                tag = f"{indent}// @quarantine - Auto-quarantined due to flakiness > 15%\n{indent}@Tag('quarantine')\n"
                            elif ext in (".ts", ".js"):
                                tag = f"{indent}// @quarantine - Auto-quarantined due to flakiness > 15%\n"
                                if "test(" in line:
                                    line = line.replace("test(", "test.fixme(")
                            elif ext == ".py":
                                tag = f"{indent}@pytest.mark.quarantine\n"
                            else:
                                tag = f"{indent}// @quarantine\n"

                            new_lines.append(tag)
                            new_lines.append(line)
                            file_modified = True
                            annotated = True
                        else:
                            new_lines.append(line)

                    if file_modified:
                        with open(file_path, "w", encoding="utf-8") as fp:
                            fp.writelines(new_lines)
                        print(f"🔒 [QUARANTINE APPLIED] Injected quarantine annotation into: {file_path}")
            except Exception as e:
                print(f"⚠️ Could not patch {file_path}: {e}")

    return annotated


def main():
    parser = argparse.ArgumentParser(description="Enterprise Flaky Test Detector & Quarantine Sentinel")
    parser.add_argument("--cmd", "-c", default=None, help="Test command to execute repeatedly")
    parser.add_argument("--repeat", "-r", type=int, default=5, help="Number of repetitions (default: 5)")
    parser.add_argument("--test-id", default=None, help="Custom identifier for the test scenario")
    parser.add_argument("--reports", default=None, help="Glob pattern for JUnit XML reports to analyze")
    parser.add_argument("--history", action="store_true", help="Query 30-day historical flakiness from SQLite telemetry")
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days (default: 30)")
    parser.add_argument("--threshold", type=float, default=0.15, help="Flaky ratio quarantine threshold (default: 0.15)")
    parser.add_argument("--isolate", action="store_true", help="Automatically inject @quarantine tag into source files")
    parser.add_argument("--target-dir", default=".", help="Root directory of test files to patch")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.history:
        if not get_flaky_telemetry:
            print("❌ SQLite cache resolver not available.")
            sys.exit(1)

        candidates = get_flaky_telemetry(days=args.days, threshold=args.threshold)
        if args.json:
            print(json.dumps(candidates, indent=2))
        else:
            print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
            print(f"{BOLD}{CYAN}      HISTORICAL FLAKINESS TELEMETRY ({args.days}-DAY WINDOW)            {RESET}")
            print(f"{BOLD}{CYAN}======================================================================{RESET}")
            print(f"  Quarantine Threshold : {args.threshold * 100:.1f}% flaky ratio")
            print(f"  Total Candidates     : {len(candidates)}\n")

            quarantined_count = 0
            for c in candidates:
                is_q = c["quarantine_recommended"]
                tag = f"{RED}[QUARANTINE]{RESET}" if is_q else f"{GREEN}[STABLE]{RESET}"
                print(f"  • {tag} {BOLD}{c['test_id']}{RESET}")
                print(f"    Runs: {c['total_runs']} | Passes: {c['pass_count']} | Fails: {c['fail_count']} | Retry Passes: {c['retry_pass_count']}")
                print(f"    Flaky Ratio: {c['flaky_ratio'] * 100:.1f}% | Avg Latency: {c['avg_duration_ms']} ms\n")

                if is_q:
                    quarantined_count += 1
                    if args.isolate:
                        auto_quarantine_test_file(c["test_id"], target_dir=args.target_dir)

            print(f"======================================================================")
            print(f"Quarantine Recommendations: {quarantined_count}/{len(candidates)}")
        sys.exit(0)

    elif args.cmd:
        stats = benchmark_live_command(args.cmd, iterations=args.repeat, test_id=args.test_id)
        if stats["quarantine"] and args.isolate:
            auto_quarantine_test_file(stats["test_id"], target_dir=args.target_dir)
        sys.exit(1 if stats["quarantine"] else 0)

    elif args.reports:
        results = parse_junit_reports(args.reports)
        quarantine_candidates = []
        for test_id, runs in results.items():
            st = calculate_flakiness(runs)
            st["test_id"] = test_id

            # Ingest into SQLite telemetry
            if record_test_telemetry:
                for idx, is_p in enumerate(runs):
                    try:
                        record_test_telemetry(
                            test_id=test_id,
                            status="PASS" if is_p else "FAIL",
                            is_retry=1 if idx > 0 else 0,
                            duration_ms=0.0,
                            context=args.reports
                        )
                    except Exception:
                        pass

            if st["quarantine"]:
                quarantine_candidates.append(st)

        print(f"\nAnalyzed {len(results)} distinct test scenarios from reports.")
        print(f"Quarantine Candidates Detected: {len(quarantine_candidates)}")
        for qc in quarantine_candidates:
            print(f"  - {RED}{qc['test_id']}{RESET}: Pass rate {qc['pass_rate']}%, Flips: {qc['flips']}")
            if args.isolate:
                auto_quarantine_test_file(qc["test_id"], target_dir=args.target_dir)

        report_file = os.path.join(REPORTS_DIR, "quarantine_board.json")
        with open(report_file, "w", encoding="utf-8") as fp:
            json.dump(quarantine_candidates, fp, indent=2)
        sys.exit(1 if quarantine_candidates else 0)

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
