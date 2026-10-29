#!/usr/bin/env python3
"""
Fast Zero-Token Failure Pinpointer for Katalon & Jenkins Reports.
Scans the latest Reports/**/JUnit_Report.xml, extracts failed Test Cases,
exact failed lines in Groovy/Script, and the root-cause exception.
Outputs < 100 tokens.

Usage:
    python3 tools/pinpoint_failure.py
    python3 tools/pinpoint_failure.py path/to/JUnit_Report.xml
"""
import os
import sys
import glob
import xml.etree.ElementTree as ET
import re

def find_latest_report():
    reports = glob.glob("Reports/**/JUnit_Report.xml", recursive=True)
    if not reports:
        return None
    reports.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return reports[0]

def parse_failures(xml_path):
    if not os.path.exists(xml_path):
        print(f"Error: {xml_path} does not exist.")
        return []

    tree = ET.parse(xml_path)
    root = tree.getroot()
    failures = []

    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")

    for suite in suites:
        for tc in suite.findall("testcase"):
            tc_name = tc.get("name", "Unknown")
            tc_time = tc.get("time", "0")
            fail = tc.find("failure")
            err = tc.find("error")
            target = fail if fail is not None else err

            if target is not None:
                msg = target.get("message", "")
                text = target.text or ""
                combined = (msg + "\n" + text).replace("&#xa;", "\n")

                # Extract Root Cause Reason
                reason_match = re.search(r"Reason:\s*(.+?)(?=\n\s*at|\Z)", combined, re.DOTALL)
                if reason_match:
                    reason = reason_match.group(1).strip()
                else:
                    lines = [l.strip() for l in combined.split("\n") if l.strip()]
                    reason = lines[0] if lines else "Unknown Error"

                # Extract Failed Line in Groovy Page / Script
                Enterprise_lines = re.findall(r"(?:Enterprise\.pages\.[\w]+|TC-[\w\s\u00C0-\u1EF9]+|Script\d+)\.groovy:\d+|(?:TC-[\w\s\u00C0-\u1EF9]+:\d+)", combined)

                failures.append({
                    "tc": tc_name.split("/")[-1],
                    "time": f"{float(tc_time):.1f}s",
                    "reason": reason.split("\n")[0][:180],
                    "failed_at": Enterprise_lines[:2] if Enterprise_lines else ["See JUnit report"]
                })

    return failures

def main():
    xml_path = sys.argv[1] if len(sys.argv) > 1 else find_latest_report()
    if not xml_path:
        print("No JUnit_Report.xml found in Reports/.")
        sys.exit(0)

    print(f"=== Report: {xml_path} ===")
    failures = parse_failures(xml_path)
    if not failures:
        print("✅ 100% PASSED: Zero failures found in report.")
        return

    print(f"❌ Found {len(failures)} Failed Test Case(s):")
    for i, f in enumerate(failures, 1):
        print(f"[{i}] {f['tc']} ({f['time']})")
        print(f"    Cause: {f['reason']}")
        print(f"    Line:  {', '.join(f['failed_at'])}")

if __name__ == "__main__":
    main()
