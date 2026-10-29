#!/usr/bin/env python3
"""
Enterprise API Contract Drift & Breaking Change Sentinel
---------------------------------------------------------
Compares OpenAPI / Swagger specifications (v2 / v3) across versions to detect
breaking changes (deleted endpoints, removed fields, newly required parameters, type shifts)
before UI test suites run and fail due to backend contract drift.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Tuple

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def load_spec(file_path: str) -> Dict[str, Any]:
    """Loads an OpenAPI/Swagger spec from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Spec file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_specs(old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes breaking changes and non-breaking contract modifications between two specs.
    """
    breaking: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    info: List[Dict[str, str]] = []

    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    # 1. Check for removed endpoints (Paths)
    for path, old_methods in old_paths.items():
        if path not in new_paths:
            breaking.append({
                "type": "REMOVED_ENDPOINT",
                "path": path,
                "detail": f"Entire endpoint path was deleted: '{path}'"
            })
            continue

        new_methods = new_paths[path]

        # 2. Check for removed HTTP methods on existing path
        for method, old_op in old_methods.items():
            if method.lower() in ("parameters", "$ref", "summary", "description"):
                continue

            if method not in new_methods:
                breaking.append({
                    "type": "REMOVED_HTTP_METHOD",
                    "path": f"{method.upper()} {path}",
                    "detail": f"HTTP method '{method.upper()}' was deleted from path '{path}'"
                })
                continue

            new_op = new_methods[method]

            # 3. Check Parameters
            old_params = {p.get("name"): p for p in old_op.get("parameters", []) if isinstance(p, dict)}
            new_params = {p.get("name"): p for p in new_op.get("parameters", []) if isinstance(p, dict)}

            # Check for newly added REQUIRED parameters (Breaks existing clients)
            for p_name, p_info in new_params.items():
                if p_name not in old_params and p_info.get("required") is True:
                    breaking.append({
                        "type": "NEW_REQUIRED_PARAM",
                        "path": f"{method.upper()} {path}",
                        "detail": f"Added newly required parameter '{p_name}' in '{p_info.get('in', 'query')}'"
                    })

            # Check for changed parameter types or newly required existing parameters
            for p_name, old_p in old_params.items():
                if p_name in new_params:
                    new_p = new_params[p_name]
                    if not old_p.get("required") and new_p.get("required") is True:
                        breaking.append({
                            "type": "PARAM_NOW_REQUIRED",
                            "path": f"{method.upper()} {path}",
                            "detail": f"Parameter '{p_name}' was changed from optional to required"
                        })
                    
                    old_type = old_p.get("type") or old_p.get("schema", {}).get("type")
                    new_type = new_p.get("type") or new_p.get("schema", {}).get("type")
                    if old_type and new_type and old_type != new_type:
                        breaking.append({
                            "type": "PARAM_TYPE_CHANGED",
                            "path": f"{method.upper()} {path}",
                            "detail": f"Parameter '{p_name}' type shifted from '{old_type}' to '{new_type}'"
                        })

            # 4. Check Responses (Removed expected status codes)
            old_resps = old_op.get("responses", {})
            new_resps = new_op.get("responses", {})
            for status_code, old_resp in old_resps.items():
                if status_code in ("200", "201", "204") and status_code not in new_resps:
                    warnings.append({
                        "type": "REMOVED_SUCCESS_RESPONSE",
                        "path": f"{method.upper()} {path}",
                        "detail": f"Success response code '{status_code}' was removed or modified"
                    })

    # Non-breaking additions
    for path, new_methods in new_paths.items():
        if path not in old_paths:
            info.append({
                "type": "NEW_ENDPOINT_ADDED",
                "path": path,
                "detail": f"New endpoint added: '{path}' (Backward compatible)"
            })

    health_score = 100.0 if not breaking else max(0.0, 100.0 - (len(breaking) * 20.0))
    is_compatible = len(breaking) == 0

    return {
        "is_backward_compatible": is_compatible,
        "contract_health_score": health_score,
        "breaking_changes_count": len(breaking),
        "warnings_count": len(warnings),
        "additions_count": len(info),
        "breaking_changes": breaking,
        "warnings": warnings,
        "additions": info
    }


def generate_markdown_report(analysis: Dict[str, Any], old_path: str, new_path: str) -> str:
    status_icon = "✅ COMPATIBLE" if analysis["is_backward_compatible"] else "❌ BREAKING DRIFT DETECTED"
    lines = [
        "# API Contract Drift & Breaking Change Report",
        f"- **Baseline Spec:** `{old_path}`",
        f"- **Current Spec:** `{new_path}`",
        f"- **Verdict:** {status_icon} (Health Score: `{analysis['contract_health_score']:.1f}%`)",
        "",
        "## Summary Metrics",
        f"| Breaking Changes | Warnings | Compatible Additions |",
        f"| :---: | :---: | :---: |",
        f"| **{analysis['breaking_changes_count']}** | **{analysis['warnings_count']}** | **{analysis['additions_count']}** |",
        ""
    ]

    if analysis["breaking_changes"]:
        lines.append("## ❌ Breaking Changes (Action Required)")
        lines.append("| Type | Endpoint / Method | Root Cause Detail |")
        lines.append("| :--- | :--- | :--- |")
        for b in analysis["breaking_changes"]:
            lines.append(f"| `{b['type']}` | `{b['path']}` | {b['detail']} |")
        lines.append("")

    if analysis["warnings"]:
        lines.append("## ⚠️ Warnings & Potential Regressions")
        for w in analysis["warnings"]:
            lines.append(f"- **{w['path']}**: {w['detail']}")
        lines.append("")

    if analysis["additions"]:
        lines.append("## ℹ️ Compatible New Additions")
        for a in analysis["additions"]:
            lines.append(f"- **{a['path']}**: {a['detail']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="API Contract Drift & Schema Diff Sentinel")
    parser.add_argument("--old", "--baseline", dest="old_spec", required=True, help="Path to baseline OpenAPI/Swagger JSON")
    parser.add_argument("--new", "--current", dest="new_spec", required=True, help="Path to current OpenAPI/Swagger JSON")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    parser.add_argument("-o", "--output", dest="output_file", default=None, help="Save report to file")
    args = parser.parse_args()

    try:
        old_data = load_spec(args.old_spec)
        new_data = load_spec(args.new_spec)
    except Exception as e:
        print(f"❌ Error loading specs: {e}")
        return 1

    analysis = compare_specs(old_data, new_data)
    md_report = generate_markdown_report(analysis, args.old_spec, args.new_spec)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"✅ Drift report saved to: {args.output_file}")

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(md_report)

    return 0 if analysis["is_backward_compatible"] else 1


if __name__ == "__main__":
    sys.exit(main())
