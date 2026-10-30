#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/newman_analyzer.py — Enterprise Newman Test Results Analyzer & CI/CD Quality Gate
---------------------------------------------------------------------------------------
Parses Postman / Newman CLI execution reports (JSON format), calculates statistical
pass/fail rates, triages failed assertions with root causes, evaluates latency SLAs,
and enforces deterministic Quality Gates in CI/CD pipelines (Exit Code 0 vs 1).

Features:
  1. Universal Newman JSON Ingestion: Reads standard `--reporters json` exports.
  2. Multi-Metric Aggregation:
     - Total Executions, Passed/Failed Requests, Error Rate (%)
     - Total pm.test Assertions, Failed Assertions, Pass Ratio (%)
     - Latency statistics (Average, Min, Max response time in ms)
  3. Failure Triage & RCA Engine:
     - Isolates exact failing Request Name, HTTP Method, and URL
     - Highlights exact `pm.test` assertion name and Chai error details
     - Distinguishes between HTTP 4xx/5xx crashes vs Schema / Assertion mismatches
  4. CI/CD SLA Quality Gate:
     - `--max-failures <int>`: Zero-tolerance or configurable failure threshold
     - `--sla-avg <ms>`: Average latency SLA threshold
     - Returns deterministic Exit Code 0 on PASS, 1 on FAIL
  5. PR Reporting: Generates clean GitHub/GitLab Markdown reports and JSON telemetry.

Usage:
  newman run collection.json -e env.json -r cli,json --reporter-json-export report.json
  python tools/newman_analyzer.py report.json --max-failures 0 --sla-avg 500
  agent-qa analyze-newman report.json --markdown pr_api_report.md
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Enforce UTF-8 stdout encoding for Windows/macOS/Linux console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_newman_json(report_path: str) -> Dict[str, Any]:
    """Parses standard Newman JSON execution report."""
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Newman report file not found: {report_path}")

    with open(report_path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    run = data.get("run", {})
    stats = run.get("stats", {})
    timings = run.get("timings", {})
    executions = run.get("executions", [])
    failures = run.get("failures", [])

    # Stats extraction
    req_stats = stats.get("requests", {})
    total_requests = req_stats.get("total", 0)
    failed_requests = req_stats.get("failed", 0)
    passed_requests = total_requests - failed_requests

    assert_stats = stats.get("assertions", {})
    total_assertions = assert_stats.get("total", 0)
    failed_assertions = assert_stats.get("failed", 0)
    passed_assertions = total_assertions - failed_assertions

    # Latencies
    response_times = run.get("timings", {}).get("responseAverage", 0)
    min_time = run.get("timings", {}).get("responseMin", 0)
    max_time = run.get("timings", {}).get("responseMax", 0)

    # Detailed Request Breakdown
    request_rows: List[Dict[str, Any]] = []
    for ex in executions:
        item = ex.get("item", {})
        req = ex.get("request", {})
        resp = ex.get("response", {})

        name = item.get("name", "Unknown Request")
        method = req.get("method", "GET")
        url_obj = req.get("url", {})
        url_str = url_obj if isinstance(url_obj, str) else url_obj.get("raw", "/")
        status_code = resp.get("code", 0) if resp else 0
        resp_time = resp.get("responseTime", 0) if resp else 0

        # Assertions inside this execution
        assertions_list = ex.get("assertions", [])
        ex_assert_total = len(assertions_list)
        ex_assert_failed = sum(1 for a in assertions_list if a.get("error"))

        request_rows.append({
            "name": name,
            "method": method,
            "url": url_str,
            "status_code": status_code,
            "response_time_ms": resp_time,
            "assertions_total": ex_assert_total,
            "assertions_failed": ex_assert_failed,
            "passed": (ex_assert_failed == 0 and status_code < 400 and status_code > 0)
        })

    # Triage Failures
    triaged_failures: List[Dict[str, str]] = []
    for f in failures:
        err = f.get("error", {})
        source = f.get("source", {})
        cursor = f.get("cursor", {})
        
        req_name = source.get("name", cursor.get("ref", "Request"))
        assert_name = err.get("test", err.get("name", "Assertion Failure"))
        message = err.get("message", "Unknown assertion error")

        triaged_failures.append({
            "request_name": req_name,
            "assertion_name": assert_name,
            "message": message
        })

    error_rate = (failed_requests / total_requests * 100.0) if total_requests > 0 else 0.0
    pass_ratio = (passed_assertions / total_assertions * 100.0) if total_assertions > 0 else 100.0

    return {
        "collection_name": data.get("collection", {}).get("info", {}).get("name", "Postman Collection"),
        "total_requests": total_requests,
        "failed_requests": failed_requests,
        "passed_requests": passed_requests,
        "error_rate_pct": round(error_rate, 2),
        "total_assertions": total_assertions,
        "failed_assertions": failed_assertions,
        "passed_assertions": passed_assertions,
        "assertion_pass_ratio_pct": round(pass_ratio, 2),
        "latency": {
            "avg_ms": round(float(response_times), 2),
            "min_ms": round(float(min_time), 2),
            "max_ms": round(float(max_time), 2)
        },
        "requests": request_rows,
        "failures": triaged_failures
    }


def evaluate_newman_sla(
    summary: Dict[str, Any],
    max_failures: int = 0,
    sla_avg: Optional[float] = None
) -> Tuple[bool, List[str]]:
    """Evaluates computed Newman summary against CI/CD SLA gates."""
    violations: List[str] = []

    total_failed = summary["failed_requests"] + summary["failed_assertions"]
    if total_failed > max_failures:
        violations.append(f"Failed Tests SLA Breached: {total_failed} failures > allowable limit ({max_failures})")

    avg_latency = summary["latency"]["avg_ms"]
    if sla_avg is not None and avg_latency > sla_avg:
        violations.append(f"Average Latency SLA Breached: {avg_latency}ms > {sla_avg}ms threshold")

    passed = (len(violations) == 0)
    return passed, violations


def format_cli_table(summary: Dict[str, Any]) -> str:
    """Formats requests into a clean CLI table."""
    headers = ["Method", "Request Name", "Status", "Latency", "Asserts (Pass/Fail)"]
    col_w = [8, 36, 8, 12, 20]

    lines = []
    header_str = " | ".join(h.ljust(col_w[i]) for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * col_w[i] for i in range(len(headers)))

    lines.append(header_str)
    lines.append(sep_str)

    for r in summary["requests"]:
        req_name = r["name"]
        if len(req_name) > 34:
            req_name = req_name[:31] + "..."
        assert_info = f"{r['assertions_total'] - r['assertions_failed']} / {r['assertions_total']}"
        status_display = str(r["status_code"]) if r["status_code"] > 0 else "FAIL"

        lines.append(" | ".join([
            f"[{r['method']}]".ljust(col_w[0]),
            req_name.ljust(col_w[1]),
            status_display.center(col_w[2]),
            f"{r['response_time_ms']} ms".rjust(col_w[3]),
            assert_info.center(col_w[4])
        ]))

    return "\n".join(lines)


def generate_markdown_report(summary: Dict[str, Any], passed: bool, violations: List[str]) -> str:
    """Generates Pull Request Markdown report."""
    status_badge = "✅ **PASSED (100% QUALITY GATE MET)**" if passed else "❌ **FAILED (QUALITY GATE BREACHED)**"

    lines = [
        f"# 📬 Postman / Newman API Automated Test Report: `{summary['collection_name']}`",
        "",
        f"- **Quality Gate Status:** {status_badge}",
        f"- **Total Requests Executed:** `{summary['total_requests']}` ({summary['failed_requests']} failed)",
        f"- **Total Assertions Checked:** `{summary['total_assertions']}` ({summary['failed_assertions']} failed)",
        f"- **Assertion Pass Ratio:** `{summary['assertion_pass_ratio_pct']}%`",
        f"- **Average Response Latency:** `{summary['latency']['avg_ms']} ms` (Min: `{summary['latency']['min_ms']} ms`, Max: `{summary['latency']['max_ms']} ms`)",
        "",
    ]

    if violations:
        lines.extend([
            "### ⚠️ CI/CD Quality Gate Violations",
            ""
        ])
        for v in violations:
            lines.append(f"- 🔴 `{v}`")
        lines.append("")

    if summary["failures"]:
        lines.extend([
            "### 🔍 Failed Assertions Triage (Root Cause)",
            "",
            "| Request Name | Failed pm.test Assertion | Error Details |",
            "| :--- | :--- | :--- |"
        ])
        for f in summary["failures"]:
            lines.append(f"| `{f['request_name']}` | **{f['assertion_name']}** | `{f['message']}` |")
        lines.append("")

    lines.extend([
        "### 📊 Detailed Endpoint Execution Breakdown",
        "",
        "| Method | Request Name | Status Code | Latency | Assertions | Result |",
        "| :---: | :--- | :---: | :---: | :---: | :---: |"
    ])

    for r in summary["requests"]:
        verdict = "✅ PASS" if r["passed"] else "❌ FAIL"
        lines.append(f"| `{r['method']}` | {r['name']} | `{r['status_code']}` | `{r['response_time_ms']} ms` | `{r['assertions_total'] - r['assertions_failed']}/{r['assertions_total']}` | {verdict} |")

    lines.extend([
        "",
        "---",
        "*Report auto-generated by Synapse-Hub `newman_analyzer.py` - Enterprise API Quality Gate.*"
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Postman / Newman Test Results Analyzer & CI/CD Quality Gatekeeper."
    )
    parser.add_argument("report_file", nargs="?", help="Path to Newman JSON report file (--reporters json).")
    parser.add_argument("--max-failures", type=int, default=0, help="Allowable failed requests / assertions threshold. Default: 0.")
    parser.add_argument("--sla-avg", type=float, default=None, help="Average Latency threshold in ms (fails if exceeded).")
    parser.add_argument("--markdown", "-m", help="Path to export Markdown report.")
    parser.add_argument("--json", "-j", help="Path to export JSON summary.")
    parser.add_argument("--sample", action="store_true", help="Generate and analyze a mock Newman test dataset.")

    args = parser.parse_args()

    if args.sample or not args.report_file:
        import tempfile
        temp_file = os.path.join(tempfile.gettempdir(), "sample_newman_report.json")
        sample_data = {
            "collection": {"info": {"name": "Enterprise Banking & Billing API"}},
            "run": {
                "stats": {
                    "requests": {"total": 4, "failed": 0},
                    "assertions": {"total": 12, "failed": 1}
                },
                "timings": {
                    "responseAverage": 185.5,
                    "responseMin": 120.0,
                    "responseMax": 340.0
                },
                "executions": [
                    {
                        "item": {"name": "1. User Authentication (Login)"},
                        "request": {"method": "POST", "url": {"raw": "https://api.staging.enterprise.local/api/v1/auth/login"}},
                        "response": {"code": 200, "responseTime": 145},
                        "assertions": [
                            {"assertion": "Status code is 200", "error": None},
                            {"assertion": "Response time is below 500ms", "error": None},
                            {"assertion": "Response matches OpenAPI JSON Schema", "error": None}
                        ]
                    },
                    {
                        "item": {"name": "2. Get Account Balance"},
                        "request": {"method": "GET", "url": {"raw": "https://api.staging.enterprise.local/api/v1/accounts/me"}},
                        "response": {"code": 200, "responseTime": 120},
                        "assertions": [
                            {"assertion": "Status code is 200", "error": None},
                            {"assertion": "Response matches OpenAPI JSON Schema", "error": None}
                        ]
                    },
                    {
                        "item": {"name": "3. Transfer Funds (Dynamic Idempotency)"},
                        "request": {"method": "POST", "url": {"raw": "https://api.staging.enterprise.local/api/v1/transfers"}},
                        "response": {"code": 201, "responseTime": 340},
                        "assertions": [
                            {"assertion": "Status code is 201", "error": None},
                            {"assertion": "Response matches OpenAPI JSON Schema", "error": None},
                            {"assertion": "Transfer status is COMPLETED", "error": {"message": "expected 'PENDING' to equal 'COMPLETED'"}}
                        ]
                    },
                    {
                        "item": {"name": "4. Audit Transaction Log"},
                        "request": {"method": "GET", "url": {"raw": "https://api.staging.enterprise.local/api/v1/transfers/last"}},
                        "response": {"code": 200, "responseTime": 137},
                        "assertions": [
                            {"assertion": "Status code is 200", "error": None},
                            {"assertion": "Response matches OpenAPI JSON Schema", "error": None}
                        ]
                    }
                ],
                "failures": [
                    {
                        "source": {"name": "3. Transfer Funds (Dynamic Idempotency)"},
                        "error": {
                            "test": "Transfer status is COMPLETED",
                            "message": "expected 'PENDING' to equal 'COMPLETED'"
                        }
                    }
                ]
            }
        }
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)
        args.report_file = temp_file
        print(f"🔬 [SAMPLE MODE] Generated synthetic Newman report: {temp_file}")

    summary = parse_newman_json(args.report_file)
    passed, violations = evaluate_newman_sla(
        summary,
        max_failures=args.max_failures,
        sla_avg=args.sla_avg
    )

    print("\n" + "=" * 90)
    print(f"  POSTMAN / NEWMAN API AUTOMATED TEST MATRIX: {summary['collection_name']}")
    print("=" * 90)
    print(format_cli_table(summary))
    print("=" * 90)
    print(f"Total Requests   : {summary['total_requests']} (Passed: {summary['passed_requests']} | Failed: {summary['failed_requests']})")
    print(f"Total Assertions : {summary['total_assertions']} (Passed: {summary['passed_assertions']} | Failed: {summary['failed_assertions']})")
    print(f"Pass Ratio       : {summary['assertion_pass_ratio_pct']}% | Avg Latency: {summary['latency']['avg_ms']} ms")
    print("-" * 90)

    # Print SLA Verdict
    print(f"🎯 [QUALITY GATE SLA VERDICT]")
    if passed:
        print("✅ ALL API FUNCTIONAL & SLA GATES PASSED! Safe to merge/deploy.")
    else:
        print("❌ API QUALITY GATE BREACHED:")
        for v in violations:
            print(f"   🔴 {v}")
        if summary["failures"]:
            print("\n🔍 Failing Assertions Breakdown:")
            for f in summary["failures"]:
                print(f"   • [{f['request_name']}] -> {f['assertion_name']}: {f['message']}")

    # Export Markdown
    if args.markdown:
        md = generate_markdown_report(summary, passed, violations)
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown)) or ".", exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n📄 Markdown Report exported: {args.markdown}")

    # Export JSON
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"📊 JSON Metrics exported: {args.json}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
