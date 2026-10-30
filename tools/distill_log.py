#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/distill_log.py — Cross-Platform Log Distiller for Katalon KRE, Gradle, and Playwright
Filters out 90%+ passing step noise and outputs strictly actionable failure triage blocks.
Compatible with Windows, macOS, and Linux.
"""

import sys
import os
import re
import argparse

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def distill(log_text, max_lines=40):
    lines = log_text.splitlines()
    total_raw_lines = len(lines)
    
    # Noise filters
    noise_patterns = [
        re.compile(r'^\s*$'),
        re.compile(r'\[INFO\b|\bINFO:|\bINFO\s+', re.IGNORECASE),
        re.compile(r'\[DEBUG\b|\bDEBUG:|\bDEBUG\s+', re.IGNORECASE),
        re.compile(r'\[TRACE\b|\bTRACE:|\bTRACE\s+', re.IGNORECASE),
        re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}.*\b(?:INFO|DEBUG|TRACE)\b', re.IGNORECASE),
        re.compile(r'\bPASSED\b', re.IGNORECASE),
        re.compile(r'> Task :'),
        re.compile(r'SLF4J:'),
        re.compile(r'Loading class `com\.mysql'),
        re.compile(r'Starting ChromeDriver'),
        re.compile(r'Only local connections are allowed'),
        re.compile(r'DevTools listening on'),
        re.compile(r'Fontconfig warning:'),
        re.compile(r'Katalon Studio.*licensed to'),
    ]

    failure_indicators = [
        re.compile(r'\bFAILED\b'),
        re.compile(r'\bERROR\b'),
        re.compile(r'Exception\b'),
        re.compile(r'AssertionError'),
        re.compile(r'Caused by:'),
        re.compile(r'at (?:Enterprise\.|Script\d+|com\.kms)'),
        re.compile(r'TC-\d+.*FAILED'),
        re.compile(r'FAIL\s+.*(?:\.spec|\.test)'),
    ]

    tc_pattern = re.compile(r'(TC-\d+|test_[A-Za-z0-9_]+|[A-Za-z0-9_-]+\.(?:spec|test)\.[jt]sx?)')
    line_num_pattern = re.compile(r'((?:Script\d+|\w+Page|\w+\.(?:groovy|ts|js|py)):(\d+))|File "([^"]+)", line (\d+)')
    exception_pattern = re.compile(r'([A-Za-z0-9_.]*(?:Exception|Error)):?\s*(.*)')

    captured_failures = []
    failing_tcs = set()
    failing_locs = []

    in_failure_block = False
    failure_block = []

    for line in lines:
        # Check if line indicates failure
        is_fail_line = any(p.search(line) for p in failure_indicators)
        is_noise = any(p.search(line) for p in noise_patterns) and not is_fail_line

        # Detect TC identifier
        m_tc = tc_pattern.search(line)
        if m_tc and ("FAILED" in line or "ERROR" in line):
            failing_tcs.add(m_tc.group(1))

        # Detect script line number
        m_loc = line_num_pattern.search(line)
        if m_loc:
            failing_locs.append(m_loc.group(1) or f"{m_loc.group(3)}:{m_loc.group(4)}")

        if is_fail_line:
            in_failure_block = True
            failure_block.append(line.strip())
        elif in_failure_block:
            if is_noise or line.startswith("---") or line.startswith("==="):
                in_failure_block = False
                if failure_block:
                    captured_failures.append("\n".join(failure_block[:10]))
                    failure_block = []
            else:
                failure_block.append(line.strip())

    if failure_block:
        captured_failures.append("\n".join(failure_block[:10]))

    # Distillation Report
    output = []
    output.append("======================================================================")
    output.append("   🔍 LOG DISTILLER — AUTOMATED FAILURE TRIAGE SUMMARY                ")
    output.append("======================================================================")
    output.append(f"Total Raw Lines: {total_raw_lines:,} lines analyzed.")

    if not failing_tcs and not captured_failures:
        output.append("✅ ALL TESTS PASSED: Zero errors or failed steps detected.")
        output.append("======================================================================")
        return "\n".join(output)

    if failing_tcs:
        output.append(f"❌ FAILURES DETECTED: {len(failing_tcs)} Test Case(s) marked FAILED.")
        output.append(f"   Targeted TCs: {', '.join(sorted(failing_tcs))}")
    else:
        output.append(f"❌ FAILURES / ERRORS DETECTED: {len(captured_failures)} failure block(s) isolated.")
        
    if failing_locs:
        unique_locs = sorted(set(failing_locs))
        output.append(f"   Failing Script Location(s): {', '.join(unique_locs[:5])}")

    output.append("\n--- Distilled Failure Block(s) ---")
    joined_blocks = "\n---\n".join(captured_failures[:3])
    output.append(joined_blocks[:2000])

    output.append("======================================================================")
    return "\n".join(output)

# Public alias for MCP server compatibility
distill_log_content = distill

def main():
    parser = argparse.ArgumentParser(description="Distill terminal execution logs into high-signal failure blocks.")
    parser.add_argument("--file", "-f", help="Path to raw log file (reads from stdin if omitted).")
    parser.add_argument("--save-raw", "-s", default=None, help="Path to preserve raw log (omitted by default to prevent hub pollution).")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: Log file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8", errors="ignore") as fp:
            log_text = fp.read()
    else:
        if sys.stdin.isatty():
            print("Usage: python3 tools/distill_log.py --file <path> OR pipe stdout via stdin.")
            sys.exit(0)
        log_text = sys.stdin.read()

    # Preserve raw log on disk if explicitly requested
    if args.save_raw:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.save_raw)), exist_ok=True)
            with open(args.save_raw, "w", encoding="utf-8") as fp:
                fp.write(log_text)
        except Exception:
            pass

    summary = distill(log_text)
    print(summary)
    if args.save_raw and os.path.exists(args.save_raw):
        print(f"[Full raw log saved to file://{os.path.abspath(args.save_raw)}]")

if __name__ == "__main__":
    main()
