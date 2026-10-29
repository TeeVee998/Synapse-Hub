#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/generate_api_matrix.py — OpenAPI / Swagger to E2E Testing Matrix Generator
Generates Positive, Boundary Value, Negative, and Edge-Case Fuzzing scenarios from API schemas.
Compatible with Windows, macOS, and Linux.
"""

import sys
import os
import json
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from fuzz_payloads import get_field_fuzz_scenarios
except ImportError:
    get_field_fuzz_scenarios = None


def generate_field_boundaries(field_name, field_schema):
    f_type = field_schema.get("type", "string")
    boundaries = []

    if f_type == "string":
        min_l = field_schema.get("minLength", 1)
        max_l = field_schema.get("maxLength", 50)
        boundaries.append({"scenario": f"{field_name} Empty String", "value": "", "expected": 400})
        boundaries.append({"scenario": f"{field_name} Below MinLength ({min_l - 1} chars)", "value": "A" * max(0, min_l - 1), "expected": 400 if min_l > 0 else 200})
        boundaries.append({"scenario": f"{field_name} Exact MaxLength ({max_l} chars)", "value": "A" * max_l, "expected": 200})
        boundaries.append({"scenario": f"{field_name} Exceed MaxLength ({max_l + 1} chars)", "value": "A" * (max_l + 1), "expected": 400})
        boundaries.append({"scenario": f"{field_name} Special & XSS Payload", "value": "<script>alert(1)</script>", "expected": 400})

        # --- Enterprise Edge-Case Fuzzing & Input Sanitization Scenarios ---
        if get_field_fuzz_scenarios:
            fuzz_items = get_field_fuzz_scenarios(field_name, "string")
            for item in fuzz_items:
                boundaries.append({
                    "scenario": item["scenario"],
                    "value": item["value"],
                    "expected": item["expected"]
                })
        else:
            boundaries.append({"scenario": f"{field_name} SQLi Polyglot Probe", "value": "' OR '1'='1' -- ", "expected": 400})
            boundaries.append({"scenario": f"{field_name} Unicode BiDi RTL Override", "value": "\u202E\u0041\u0042\u0043_AUTO_TX", "expected": 400})
            boundaries.append({"scenario": f"{field_name} Emoji Surrogate & ZWJ Sequence", "value": "👨‍👩‍👧‍👦_QA_TAG", "expected": 200})
            boundaries.append({"scenario": f"{field_name} Extreme Length 10^4 Buffer Stress", "value": "A" * 10000, "expected": 400})
            boundaries.append({"scenario": f"{field_name} Null Byte Truncation Injection", "value": "data\x00.json", "expected": 400})

    elif f_type in ("integer", "number"):
        minimum = field_schema.get("minimum", 0)
        maximum = field_schema.get("maximum", 1000)
        boundaries.append({"scenario": f"{field_name} Negative Value ({minimum - 1})", "value": minimum - 1, "expected": 400})
        boundaries.append({"scenario": f"{field_name} Boundary Minimum ({minimum})", "value": minimum, "expected": 200})
        boundaries.append({"scenario": f"{field_name} Boundary Maximum ({maximum})", "value": maximum, "expected": 200})
        boundaries.append({"scenario": f"{field_name} Exceed Maximum ({maximum + 1})", "value": maximum + 1, "expected": 400})
        boundaries.append({"scenario": f"{field_name} 32-bit Integer Overflow (2^31)", "value": 2147483648, "expected": 400})

    elif f_type == "boolean":
        boundaries.append({"scenario": f"{field_name} Invalid String Instead of Boolean", "value": "not_a_bool", "expected": 400})

    return boundaries


def parse_spec(spec_data):
    matrix = []
    paths = spec_data.get("paths", {})

    for endpoint, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue

            summary = details.get("summary", details.get("operationId", f"{method.upper()} {endpoint}"))
            req_body = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            properties = req_body.get("properties", {})
            required_fields = req_body.get("required", [])

            # 1. Happy Path
            matrix.append({
                "endpoint": endpoint,
                "method": method.upper(),
                "type": "POSITIVE",
                "name": f"TC_API_{method.upper()}_{endpoint.replace('/', '_')}_HappyPath",
                "description": f"Valid payload execution for {summary}",
                "expected_status": 200 if method.lower() == "get" else 201
            })

            # 2. Missing Required Fields (Negative)
            for req in required_fields:
                matrix.append({
                    "endpoint": endpoint,
                    "method": method.upper(),
                    "type": "NEGATIVE",
                    "name": f"TC_API_{method.upper()}_{endpoint.replace('/', '_')}_Missing_{req}",
                    "description": f"Submit request omitting required field '{req}'",
                    "expected_status": 400
                })

            # 3. Boundary Values & Edge-Case Fuzzing
            for fname, fschema in properties.items():
                b_list = generate_field_boundaries(fname, fschema)
                for b in b_list:
                    clean_scenario = b['scenario'].replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and')
                    val_str = str(b['value'])
                    if len(val_str) > 30:
                        val_str = val_str[:27] + "..."
                    matrix.append({
                        "endpoint": endpoint,
                        "method": method.upper(),
                        "type": "BOUNDARY",
                        "name": f"TC_API_{method.upper()}_{endpoint.replace('/', '_')}_{clean_scenario}",
                        "description": f"Boundary/Fuzz testing: {b['scenario']} with value '{val_str}'",
                        "expected_status": b["expected"]
                    })

    return matrix


def to_markdown(matrix):
    lines = []
    lines.append("# Automated E2E & API Contract Testing Matrix")
    lines.append("")
    lines.append("| ID | Method | Endpoint | Test Type | Scenario Description | Expected Status |")
    lines.append("| :--- | :---: | :--- | :---: | :--- | :---: |")

    for idx, tc in enumerate(matrix, 1):
        lines.append(f"| TC-API-{idx:03d} | `{tc['method']}` | `{tc['endpoint']}` | **{tc['type']}** | {tc['description']} | `{tc['expected_status']}` |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate E2E Positive, Boundary, and Negative test matrix from OpenAPI/Swagger schema.")
    parser.add_argument("--spec", "-s", help="Path to OpenAPI / Swagger JSON schema file.")
    parser.add_argument("--format", "-f", choices=["md", "json"], default="md", help="Output format (markdown or json).")
    parser.add_argument("--output", "-o", help="Output file path.")
    parser.add_argument("--sample", action="store_true", help="Generate a sample matrix using built-in demonstration schema.")
    args = parser.parse_args()

    if args.sample or not args.spec:
        sample_spec = {
            "paths": {
                "/api/v1/categories": {
                    "post": {
                        "summary": "Create new category",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["code", "name"],
                                        "properties": {
                                            "code": {"type": "string", "minLength": 3, "maxLength": 20},
                                            "name": {"type": "string", "minLength": 1, "maxLength": 100},
                                            "priority": {"type": "integer", "minimum": 1, "maximum": 100}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        spec_data = sample_spec
    else:
        if not os.path.exists(args.spec):
            print(f"Error: Specification file not found: {args.spec}", file=sys.stderr)
            sys.exit(1)
        with open(args.spec, "r", encoding="utf-8") as fp:
            spec_data = json.load(fp)

    matrix = parse_spec(spec_data)

    if args.format == "json":
        result = json.dumps(matrix, indent=2, ensure_ascii=False)
    else:
        result = to_markdown(matrix)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(result)
        print(f"✅ Matrix successfully generated to: {args.output} ({len(matrix)} test cases)")
    else:
        print(result)


if __name__ == "__main__":
    main()
