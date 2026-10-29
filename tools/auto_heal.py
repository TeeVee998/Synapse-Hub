#!/usr/bin/env python3
"""
Enterprise Closed-Loop Autonomous Test Healer Engine
-----------------------------------------------------
Diagnoses test failures in 0.1s from JUnit XML and terminal logs, queries the 
semantic memory cache for proven patches, and orchestrates targeted re-tests.
Dispatched automatically by AI Agents when test runs encounter failures.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, SCRIPT_DIR)

import pinpoint_failure
import cache_resolver
import project_state
import heuristic_locator_matcher

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def diagnose_and_plan_heal(target_dir, junit_xml_path=None):
    """
    Parses test failure, checks memory cache, updates project state watchpoints,
    and returns a structured healing plan.
    """
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}           AUTONOMOUS CLOSED-LOOP TEST HEALING SENTINEL               {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"📁 Target Project  : {target_dir}")

    # 1. Pinpoint failure from JUnit XML or logs
    failure_info = None
    if junit_xml_path and os.path.exists(junit_xml_path):
        failures = pinpoint_failure.parse_junit_xml(junit_xml_path)
        if failures:
            failure_info = failures[0]

    if not failure_info:
        # Search for any recent report in Reports/
        reports_dir = os.path.join(target_dir, "Reports")
        if os.path.exists(reports_dir):
            for root, _, files in os.walk(reports_dir):
                for f in files:
                    if f.endswith(".xml"):
                        parsed = pinpoint_failure.parse_junit_xml(os.path.join(root, f))
                        if parsed:
                            failure_info = parsed[0]
                            break
                if failure_info:
                    break

    if not failure_info:
        print("  [INFO] Zero active JUnit XML failures detected on disk.")
        return {"status": "NO_FAILURE_DETECTED"}

    err_sig = failure_info.get("message", failure_info.get("type", "UnknownError"))
    test_name = failure_info.get("name", "UnknownTest")
    failing_file = failure_info.get("file", "UnknownFile")
    line_num = failure_info.get("line", "?")

    print(f"  ❌ Failing Test   : {test_name}")
    print(f"  📍 Source Location: {failing_file}:{line_num}")
    print(f"  ⚠️ Error Signature: {err_sig[:120]}...\n")

    # 2. Query 0-token memory cache & 3-layer heuristic matcher
    print(f"{BOLD}[1/2] Checking 3-Layer Heuristic Matcher & Memory Cache...{RESET}")
    cache_solution = cache_resolver.query_cache(err_sig, threshold=0.35)

    # 2b. Query Episodic Reflexion Memory (Top 2 historical lessons)
    lessons = cache_resolver.query_lessons(f"{test_name} {err_sig}", limit=2)

    plan = {
        "status": "HEALING_PLAN_READY",
        "test_name": test_name,
        "failing_file": failing_file,
        "line": line_num,
        "error_signature": err_sig,
        "cache_match": bool(cache_solution),
        "heuristic_match": None,
        "recommended_patch": None,
        "episodic_lessons": [l["lesson_summary"] for l in lessons]
    }

    if lessons:
        print(f"  {CYAN}🧠 [EPISODIC REFLEXION] Top Historical Lessons for Context:{RESET}")
        for idx, l in enumerate(lessons, 1):
            print(f"     {idx}. [{l['page_context']}]: {l['lesson_summary']}")

    if cache_solution:
        print(f"  {GREEN}[MATCH] Found cached resolution (Score: {cache_solution['score']:.2f}):{RESET}")
        print(f"  💡 Prescribed Fix : {cache_solution['solution']}")
        plan["recommended_patch"] = cache_solution["solution"]
    else:
        # Check if error message contains broken locator pattern
        loc_candidate_m = re.search(r"locator\(['\"]([^'\"]+)['\"]\)|By\.[a-zA-Z]+\(['\"]([^'\"]+)['\"]\)", err_sig)
        if loc_candidate_m:
            broken_loc = loc_candidate_m.group(1) or loc_candidate_m.group(2)
            heuristic_res = heuristic_locator_matcher.HeuristicLocatorMatcher.match(broken_loc, dom_snapshot=[])
            plan["heuristic_match"] = heuristic_res
            if heuristic_res.get("matched"):
                print(f"  {GREEN}[HEURISTIC L{heuristic_res['layer']}] 0-Token match ({heuristic_res['confidence']*100:.1f}%): {heuristic_res['healed_locator']}{RESET}")
                plan["recommended_patch"] = f"Update locator to: {heuristic_res['healed_locator']}"
            else:
                print("  [MISS] Heuristic confidence < 85%. Fallback to Live DOM exploration.")
                plan["recommended_patch"] = "Inspect element using Playwright Live Explorer and apply resilient locator / smart wait."
        else:
            print("  [MISS] No direct cache match. AI Agent will inspect live DOM/AOM via Playwright.")
            plan["recommended_patch"] = "Inspect element using Playwright Live Explorer and apply resilient locator / smart wait."

    # 3. Anchor watchpoint in PROJECT_STATE.md
    print(f"\n{BOLD}[2/2] Anchoring Watchpoint in PROJECT_STATE.md...{RESET}")
    try:
        project_state.update_state(
            target_dir=target_dir,
            watchpoint=f"{test_name} -> {failing_file}:{line_num}",
            gate_status="HEALING_IN_PROGRESS"
        )
        print("  [OK] Project state watchpoint updated.")
    except Exception as e:
        print(f"  ⚠️ Could not update PROJECT_STATE.md: {e}")

    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")
    return plan


def record_heal_lesson(page_context, error_signature, root_cause, failed_attempt, successful_fix, lesson_summary):
    """Saves a 2-line practical lesson learned into SQLite after successful healing."""
    return cache_resolver.record_lesson(
        page_context=page_context,
        error_signature=error_signature,
        root_cause=root_cause,
        failed_attempt=failed_attempt,
        successful_fix=successful_fix,
        lesson_summary=lesson_summary
    )


def main():
    parser = argparse.ArgumentParser(description="Autonomous Closed-Loop Test Healer")
    parser.add_argument("target", nargs="?", default=os.getcwd(), help="Target project root directory")
    parser.add_argument("--xml", default=None, help="Path to JUnit XML test report")
    parser.add_argument("--record-lesson", default=None, help="Record a 2-line lesson learned after healing")
    parser.add_argument("--context", default="GLOBAL", help="Page context for the recorded lesson")
    parser.add_argument("--error", default="UnknownError", help="Error signature for the recorded lesson")
    parser.add_argument("--fix", default="", help="Successful fix for the recorded lesson")
    args = parser.parse_args()

    if args.record_lesson:
        ok = record_heal_lesson(
            page_context=args.context,
            error_signature=args.error,
            root_cause="Autonomous Healer Diagnosis",
            failed_attempt="",
            successful_fix=args.fix,
            lesson_summary=args.record_lesson
        )
        if ok:
            print(f"✅ [EPISODIC REFLEXION] Lesson recorded for '{args.context}': {args.record_lesson}")
        return 0

    target_dir = os.path.abspath(args.target)
    plan = diagnose_and_plan_heal(target_dir, junit_xml_path=args.xml)
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
