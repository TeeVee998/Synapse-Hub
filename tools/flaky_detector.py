#!/usr/bin/env python3
"""
Enterprise Flaky Test Detector & Quarantine Sentinel
---------------------------------------------------
Executes a target test scenario N times (default: 5) or parses historical JUnit XML
reports to calculate the Flakiness Index, detect state flips, and recommend quarantine isolation.

Usage:
  python tools/flaky_detector.py --repeat 5 --cmd "python -m unittest tests/test_tools.py"
  python tools/flaky_detector.py --reports "reports/**/junit*.xml"
"""

import os
import sys
import glob
import json
import time
import argparse
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_command(cmd, timeout=300):
    """Executes a shell command and returns (returncode, stdout, stderr, elapsed_ms)."""
    start = time.time()
    try:
        res = subprocess.run(
            cmd,
            shell=True,
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


def calculate_flakiness(runs):
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

    if pass_rate == 100.0:
        status = "STABLE"
        quarantine = False
    elif pass_rate == 0.0:
        status = "DETERMINISTIC_FAIL"
        quarantine = False
    elif pass_rate >= 80.0:
        status = "MILD_FLAKE"
        quarantine = (flips >= 2)
    else:
        status = "SEVERE_FLAKE"
        quarantine = True

    return {
        "total": total,
        "passes": passes,
        "failures": failures,
        "pass_rate": pass_rate,
        "flips": flips,
        "status": status,
        "quarantine": quarantine
    }


def parse_junit_reports(glob_pattern):
    """Parses JUnit XML report files and aggregates pass/fail counts by test case."""
    test_results = {}
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


def benchmark_live_command(cmd, iterations=5):
    """Executes a live test command N times to observe flakiness in real time."""
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      ENTERPRISE FLAKY TEST SENTINEL (Multi-Run Verification)        {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Target Command     : {cmd}")
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
        status_str = f"{GREEN}PASS{RESET}" if is_pass else f"{RED}FAIL (Exit {code}){RESET}"
        print(f"{status_str} ({ms} ms)")

    stats = calculate_flakiness(runs)
    stats["latencies_ms"] = latencies
    stats["avg_latency_ms"] = round(sum(latencies) / max(1, len(latencies)), 2)
    stats["command"] = cmd

    # Print Scorecard
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}                   FLAKINESS DIAGNOSTIC SCORECARD                     {RESET}")
    print(f"{BOLD}======================================================================{RESET}")
    print(f"  Pass Rate          : {stats['pass_rate']}% ({stats['passes']}/{stats['total']} passes)")
    print(f"  Status Flips       : {stats['flips']} transitions")
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


def main():
    parser = argparse.ArgumentParser(description="Enterprise Flaky Test Detector & Quarantine Sentinel")
    parser.add_argument("--cmd", "-c", default=None, help="Test command to execute repeatedly")
    parser.add_argument("--repeat", "-r", type=int, default=5, help="Number of repetitions (default: 5)")
    parser.add_argument("--reports", default=None, help="Glob pattern for JUnit XML reports to analyze")
    args = parser.parse_args()

    if args.cmd:
        stats = benchmark_live_command(args.cmd, iterations=args.repeat)
        sys.exit(1 if stats["quarantine"] else 0)
    elif args.reports:
        results = parse_junit_reports(args.reports)
        quarantine_candidates = []
        for test_id, runs in results.items():
            st = calculate_flakiness(runs)
            st["test_id"] = test_id
            if st["quarantine"]:
                quarantine_candidates.append(st)

        print(f"\nAnalyzed {len(results)} distinct test scenarios from reports.")
        print(f"Quarantine Candidates Detected: {len(quarantine_candidates)}")
        for qc in quarantine_candidates:
            print(f"  - {RED}{qc['test_id']}{RESET}: Pass rate {qc['pass_rate']}%, Flips: {qc['flips']}")

        report_file = os.path.join(REPORTS_DIR, "quarantine_board.json")
        with open(report_file, "w", encoding="utf-8") as fp:
            json.dump(quarantine_candidates, fp, indent=2)
        sys.exit(1 if quarantine_candidates else 0)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
