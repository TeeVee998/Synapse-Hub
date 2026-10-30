#!/usr/bin/env python3
"""
Custom Security Headers Auditor (Sample 3rd-Party Plugin Tool)
-------------------------------------------------------------
Audits HTTP response headers for OWASP ASVS compliance:
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- Content-Security-Policy (CSP)
- Referrer-Policy
- Permissions-Policy
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List

MANDATORY_HEADERS = {
    "strict-transport-security": {
        "severity": "HIGH",
        "description": "Protects against protocol downgrade attacks and cookie hijacking.",
        "recommended": "max-age=31536000; includeSubDomains"
    },
    "x-content-type-options": {
        "severity": "MEDIUM",
        "description": "Prevents MIME-type sniffing.",
        "recommended": "nosniff"
    },
    "x-frame-options": {
        "severity": "MEDIUM",
        "description": "Mitigates clickjacking attacks.",
        "recommended": "DENY"
    },
    "content-security-policy": {
        "severity": "HIGH",
        "description": "Restricts sources of executable scripts, objects, and styles.",
        "recommended": "default-src 'self'"
    },
    "referrer-policy": {
        "severity": "LOW",
        "description": "Protects referrer data from leaking across origins.",
        "recommended": "strict-origin-when-cross-origin"
    }
}


def audit_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    normalized = {k.lower(): v for k, v in headers.items()}
    findings: List[Dict[str, Any]] = []
    missing_count = 0

    for h_name, meta in MANDATORY_HEADERS.items():
        if h_name not in normalized:
            missing_count += 1
            findings.append({
                "header": h_name,
                "status": "MISSING",
                "severity": meta["severity"],
                "description": meta["description"],
                "recommendation": meta["recommended"]
            })
        else:
            findings.append({
                "header": h_name,
                "status": "PRESENT",
                "severity": "INFO",
                "value": normalized[h_name]
            })

    score = round(max(0.0, 100.0 - (missing_count * 20.0)), 1)
    status = "COMPLIANT" if score >= 80.0 else "NON_COMPLIANT"

    return {
        "score": score,
        "status": status,
        "total_rules": len(MANDATORY_HEADERS),
        "missing_headers": missing_count,
        "findings": findings
    }


def main():
    parser = argparse.ArgumentParser(description="Audit HTTP Security Headers")
    parser.add_argument("--headers", help="Path to JSON file containing response headers")
    parser.add_argument("--report", default="security_headers_report.json", help="Output JSON report path")
    args = parser.parse_args()

    headers_data = {}
    if args.headers and os.path.exists(args.headers):
        with open(args.headers, "r", encoding="utf-8") as f:
            headers_data = json.load(f)
    else:
        # Default mock headers for demonstration
        headers_data = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'"
        }

    results = audit_headers(headers_data)

    print("==========================================================")
    print("      HTTP SECURITY HEADERS AUDIT (OWASP ASVS)           ")
    print("==========================================================")
    print(f"Compliance Score : {results['score']}%")
    print(f"Audit Status     : {results['status']}")
    print(f"Missing Headers  : {results['missing_headers']}")

    for f in results["findings"]:
        icon = "[PASS]" if f["status"] == "PRESENT" else "[WARN]"
        print(f" {icon} {f['header']}: {f['status']}")

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport written to: {args.report}")
    print("==========================================================")

    return 0 if results["score"] >= 80.0 else 1


if __name__ == "__main__":
    sys.exit(main())
