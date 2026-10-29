#!/usr/bin/env python3
"""
Auto-Bug Reporter & Root Cause Analysis (RCA) Ticket Generator
--------------------------------------------------------------
Transforms automated test failures into enterprise-ready Bug Reports
compatible with Jira, GitHub Issues, and Markdown.
Automatically performs RCA (AUT Bug vs Test Script Bug), extracts
reproduction steps, distills stacktraces (0 noise), and attaches evidence.
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime


class BugReporter:
    """Enterprise Automated Bug Ticket & RCA Generator."""

    @staticmethod
    def classify_root_cause(error_message: str, stack_trace: str) -> Dict[str, str]:
        """
        Classifies whether the failure is an Application Bug (AUT Bug)
        or an Automation Test Maintenance Bug (Test Bug).
        """
        combined = (error_message + " " + stack_trace).lower()

        # Application / Backend / Frontend Bugs
        if any(err in combined for err in ["500 internal server error", "502 bad gateway", "503 service unavailable", "504 gateway timeout"]):
            return {
                "type": "AUT_BACKEND_CRASH",
                "label": "AUT Bug (Backend Crash / Server 5xx)",
                "severity": "Blocker",
                "suggested_team": "Backend Engineering"
            }
        if any(err in combined for err in ["uncaught typeerror", "undefined is not a function", "cannot read property", "referenceerror", "uncaught syntaxerror"]):
            return {
                "type": "AUT_FRONTEND_EXCEPTION",
                "label": "AUT Bug (Unhandled Frontend Exception)",
                "severity": "Critical",
                "suggested_team": "Frontend Engineering"
            }
        if any(err in combined for err in ["assertionerror", "expected value", "expected condition failed", "verifyequal failed"]):
            return {
                "type": "AUT_BUSINESS_LOGIC_MISMATCH",
                "label": "AUT Bug (Business Logic / Assertion Mismatch)",
                "severity": "Major",
                "suggested_team": "Product / Dev Team"
            }

        # Automation Script Issues
        if any(err in combined for err in ["nosuchelementexception", "elementnotfound", "waiting for locator", "timeout 30000ms exceeded"]):
            return {
                "type": "TEST_LOCATOR_DRIFT",
                "label": "Test Script Bug (Locator Drift or Timeout)",
                "severity": "Minor",
                "suggested_team": "QA Automation"
            }
        if "staleelementreferenceexception" in combined:
            return {
                "type": "TEST_STALE_ELEMENT",
                "label": "Test Script Bug (DOM Re-render Race Condition)",
                "severity": "Minor",
                "suggested_team": "QA Automation"
            }

        return {
            "type": "AUT_DEFECT_SUSPECTED",
            "label": "Suspected Application Defect",
            "severity": "Major",
            "suggested_team": "Dev & QA Team"
        }

    @staticmethod
    def distill_stack_trace(raw_stack: str, max_lines: int = 5) -> str:
        """Filters noisy framework stack trace down to actionable lines."""
        lines = [l.strip() for l in raw_stack.splitlines() if l.strip()]
        actionable = []
        for l in lines:
            # Filter standard framework internals
            if any(internal in l for internal in ["at Module.", "node_modules", "org.gradle", "sun.reflect", "jdk.internal"]):
                continue
            actionable.append(l)
            if len(actionable) >= max_lines:
                break
        return "\n".join(actionable) if actionable else raw_stack[:300]

    @classmethod
    def generate_report(
        cls,
        test_id: str,
        test_title: str,
        error_message: str,
        stack_trace: str = "",
        screenshot_path: Optional[str] = None,
        steps_executed: Optional[List[str]] = None,
        environment: str = "Staging / Chrome Headless",
        format_type: str = "jira"
    ) -> str:
        """Generates a complete bug ticket string in Jira or Markdown format."""
        rca = cls.classify_root_cause(error_message, stack_trace)
        distilled_stack = cls.distill_stack_trace(stack_trace)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        steps = steps_executed or [
            f"1. Navigate to target application under test",
            f"2. Execute test workflow for {test_title}",
            f"3. Trigger operation causing failure: {error_message[:80]}"
        ]

        if format_type.lower() == "jira":
            report = [
                f"h2. [BUG][{rca['severity'].upper()}] {test_id}: {test_title} - {error_message[:90]}",
                "",
                f"* *Issue Type:* Bug",
                f"* *Root Cause Category:* {rca['label']}",
                f"* *Severity / Priority:* {rca['severity']}",
                f"* *Assigned Team:* {rca['suggested_team']}",
                f"* *Environment:* {environment}",
                f"* *Detected At:* {timestamp}",
                "",
                "h3. 1. Steps to Reproduce",
            ]
            for s in steps:
                report.append(f"# {s}")

            report.extend([
                "",
                "h3. 2. Expected Result",
                f"Operation completes successfully without errors, assertions pass.",
                "",
                "h3. 3. Actual Result",
                f"{{color:red}}*Failure:* {error_message}{{color}}",
                "",
                "h3. 4. Distilled Diagnostic Stack Trace",
                "{code:java}",
                distilled_stack,
                "{code}",
            ])

            if screenshot_path:
                report.extend([
                    "",
                    "h3. 5. Visual Evidence",
                    f"!{os.path.basename(screenshot_path)}|thumbnail!",
                    f"Local file: [^{screenshot_path}]"
                ])

            return "\n".join(report)

        # Markdown / GitHub Issues format
        md = [
            f"# [BUG][{rca['severity'].upper()}] {test_id}: {test_title}",
            "",
            f"> **Root Cause Analysis:** `{rca['label']}`  ",
            f"> **Severity:** **{rca['severity']}** | **Assigned To:** `{rca['suggested_team']}` | **Detected:** {timestamp}",
            "",
            "## 📌 1. Steps to Reproduce",
        ]
        for s in steps:
            md.append(f"- {s}")

        md.extend([
            "",
            "## 🎯 2. Expected Result",
            "Application executes workflow smoothly and passes all validations.",
            "",
            "## ❌ 3. Actual Result",
            f"**Error Encountered:**",
            f"```text\n{error_message}\n```",
            "",
            "## 🔍 4. Distilled Stack Trace (0-Noise)",
            f"```text\n{distilled_stack}\n```",
        ])

        if screenshot_path:
            md.extend([
                "",
                "## 📸 5. Visual Evidence",
                f"![Failure Evidence]({screenshot_path})"
            ])

        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Bug Reporter & RCA Ticket Generator")
    parser.add_argument("--test-id", default="TC_AUTO_001", help="Test Case Identifier")
    parser.add_argument("--title", required=True, help="Test Case Title")
    parser.add_argument("--error", required=True, help="Error message / exception")
    parser.add_argument("--stack", default="", help="Raw stack trace string or file path")
    parser.add_argument("--screenshot", default=None, help="Path to error screenshot")
    parser.add_argument("--format", choices=["jira", "md", "json"], default="jira", help="Output format")
    parser.add_argument("--out", default=None, help="Output file path")

    args = parser.parse_args()

    stack = args.stack
    if os.path.exists(stack):
        with open(stack, "r", encoding="utf-8", errors="replace") as f:
            stack = f.read()

    report = BugReporter.generate_report(
        test_id=args.test_id,
        test_title=args.title,
        error_message=args.error,
        stack_trace=stack,
        screenshot_path=args.screenshot,
        format_type=args.format
    )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ Bug report generated and saved to: {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
