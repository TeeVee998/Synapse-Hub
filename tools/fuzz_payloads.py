#!/usr/bin/env python3
"""
Enterprise Edge-Case Fuzzing & Input Sanitization Payload Catalog
------------------------------------------------------------------
Supplies standardized boundary, resilience, and sanitization payloads
for transforming functional automated test suites into robust input
sanitization and vulnerability boundary validators.

Categories Covered:
  1. SQLi Harmless Polyglots (no data destruction, tests parser escaping)
  2. XSS & Script Injection Polyglots
  3. Unicode BiDi / RTL Trojan Source & Zero-Width characters
  4. Multi-byte Emoji Surrogate Pairs & ZWJ Sequences
  5. Extreme Length Strings (10^4 buffer stress testing)
  6. Null Byte & Control Character Injections
  7. Numeric Precision & IEEE-754 Boundary Limits
"""

import sys
import json
import argparse
from typing import Dict, Any, List, Optional

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


FUZZ_PAYLOAD_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "sqli_polyglots": [
        {"name": "Standard Tautology", "payload": "' OR '1'='1' -- ", "expected_status": 400},
        {"name": "Inline Polyglot Comment", "payload": "SLEEP(0)/*'/*\"/*--", "expected_status": 400},
        {"name": "Union Select Null Probe", "payload": "1' UNION SELECT NULL, NULL, NULL -- ", "expected_status": 400},
        {"name": "Batched Query Delay Probe", "payload": "'; WAITFOR DELAY '0:0:0'--", "expected_status": 400},
        {"name": "Admin Comment Bypass", "payload": "admin' -- ", "expected_status": 400}
    ],
    "xss_polyglots": [
        {"name": "Standard Script Tag", "payload": "<script>alert(1)</script>", "expected_status": 400},
        {"name": "Image Tag OnError", "payload": "<img src=x onerror=console.warn('qa_xss')>", "expected_status": 400},
        {"name": "Universal Polyglot Vector", "payload": "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/\"/+/onmouseover=1+(alert)(1)//'>", "expected_status": 400},
        {"name": "SVG FromCharCode Injection", "payload": "\"><svg/onload=alert(String.fromCharCode(88,83,83))>", "expected_status": 400}
    ],
    "unicode_bidi_rtl": [
        {"name": "Right-to-Left Override (Trojan Source)", "payload": "\u202E\u0041\u0042\u0043_AUTO_TX", "expected_status": 400},
        {"name": "Zero-Width Space & Joiner Injection", "payload": "AUTO\u200B\u200C\u200D_DATA", "expected_status": 400},
        {"name": "Byte Order Mark (BOM) In-String", "payload": "\uFEFFAUTO_USER", "expected_status": 400},
        {"name": "Mixed BiDi Arabic/Latin", "payload": "USER_مرحبا_بالعالم_2026", "expected_status": 200}
    ],
    "emoji_surrogates": [
        {"name": "Complex ZWJ Family Sequence", "payload": "👨‍👩‍👧‍👦_QA_RECORD", "expected_status": 200},
        {"name": "Rainbow Flag Multi-Code", "payload": "🏳️‍🌈_FLAG_TAG", "expected_status": 200},
        {"name": "Unpaired Surrogate Pair Boundary", "payload": "\uD83D\uDE00\uD83D", "expected_status": 400},
        {"name": "4-Byte High Plane UTF-8", "payload": "🔥🚀⚡🧪✨", "expected_status": 200}
    ],
    "extreme_length": [
        {"name": "10^4 (10,000 Chars) Buffer Stress", "payload": "A" * 10000, "expected_status": 400},
        {"name": "1,024 Chars Text Block", "payload": "X" * 1024, "expected_status": 400},
        {"name": "Repetitive Delimiter Stress", "payload": "{\"test\": [" + ",".join(["1"] * 500) + "]}", "expected_status": 400}
    ],
    "null_byte_control": [
        {"name": "Null Byte Extension Truncation", "payload": "document\x00.pdf", "expected_status": 400},
        {"name": "URL Encoded Null Byte", "payload": "test%00.png", "expected_status": 400},
        {"name": "Carriage Return Linefeed Header Split", "payload": "test\r\nSet-Cookie: QA_LEAK=1", "expected_status": 400}
    ],
    "numeric_boundaries": [
        {"name": "32-bit Integer Max Overflow", "payload": 2147483648, "expected_status": 400},
        {"name": "32-bit Integer Min Underflow", "payload": -2147483649, "expected_status": 400},
        {"name": "64-bit BigInt Max Boundary", "payload": 9223372036854775807, "expected_status": 200},
        {"name": "JavaScript MAX_SAFE_INTEGER + 1", "payload": 9007199254740992, "expected_status": 400},
        {"name": "IEEE-754 Extreme Float Overflow", "payload": 1e308, "expected_status": 400},
        {"name": "Negative Zero Float", "payload": -0.0, "expected_status": 200}
    ]
}


def get_fuzz_payloads(category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Returns payloads filtered by category or the entire catalog."""
    if category and category.lower() != "all":
        cat_key = category.lower()
        if cat_key in FUZZ_PAYLOAD_CATALOG:
            return {cat_key: FUZZ_PAYLOAD_CATALOG[cat_key]}
        # Fuzzy match
        for k in FUZZ_PAYLOAD_CATALOG:
            if cat_key in k:
                return {k: FUZZ_PAYLOAD_CATALOG[k]}
    return FUZZ_PAYLOAD_CATALOG


def get_field_fuzz_scenarios(field_name: str, field_type: str = "string") -> List[Dict[str, Any]]:
    """
    Generates actionable test scenarios for a given field name and data type.
    """
    scenarios = []
    if field_type == "string":
        # 1. SQLi Polyglot
        scenarios.append({
            "scenario": f"{field_name} SQLi Polyglot Sanitization",
            "category": "SECURITY_SANITY",
            "value": FUZZ_PAYLOAD_CATALOG["sqli_polyglots"][0]["payload"],
            "expected": 400
        })
        # 2. XSS Probe
        scenarios.append({
            "scenario": f"{field_name} XSS Universal Polyglot",
            "category": "SECURITY_SANITY",
            "value": FUZZ_PAYLOAD_CATALOG["xss_polyglots"][1]["payload"],
            "expected": 400
        })
        # 3. BiDi RTL Trojan Source
        scenarios.append({
            "scenario": f"{field_name} Unicode BiDi RTL Override",
            "category": "RESILIENCE_UNICODE",
            "value": FUZZ_PAYLOAD_CATALOG["unicode_bidi_rtl"][0]["payload"],
            "expected": 400
        })
        # 4. Multi-byte Emoji Surrogate
        scenarios.append({
            "scenario": f"{field_name} Emoji Surrogate & ZWJ Sequence",
            "category": "RESILIENCE_UNICODE",
            "value": FUZZ_PAYLOAD_CATALOG["emoji_surrogates"][0]["payload"],
            "expected": 200
        })
        # 5. Extreme Length 10^4
        scenarios.append({
            "scenario": f"{field_name} 10^4 Chars Buffer Stress",
            "category": "RESILIENCE_OVERFLOW",
            "value": "A" * 10000,
            "expected": 400
        })
        # 6. Null Byte Injection
        scenarios.append({
            "scenario": f"{field_name} Null Byte Injection",
            "category": "SECURITY_SANITY",
            "value": "item\x00_test",
            "expected": 400
        })

    elif field_type in ("integer", "number"):
        for item in FUZZ_PAYLOAD_CATALOG["numeric_boundaries"]:
            scenarios.append({
                "scenario": f"{field_name} {item['name']}",
                "category": "RESILIENCE_NUMERIC",
                "value": item["payload"],
                "expected": item["expected_status"]
            })

    return scenarios


def main():
    parser = argparse.ArgumentParser(description="Edge-Case Fuzzing & Input Sanitization Payload Generator")
    parser.add_argument("--category", default="all", help="Payload category (sqli, xss, bidi, emoji, length, null, numeric, or all)")
    parser.add_argument("--field", default="", help="Optional field name to generate targeted boundary suite")
    parser.add_argument("--type", default="string", choices=["string", "integer", "number"], help="Field data type")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    if args.field:
        scenarios = get_field_fuzz_scenarios(args.field, field_type=args.type)
        if args.json:
            print(json.dumps(scenarios, indent=2, ensure_ascii=False))
        else:
            print(f"\n======================================================================")
            print(f"      EDGE-CASE FUZZING SCENARIOS FOR FIELD: '{args.field}' ({args.type.upper()})")
            print(f"======================================================================")
            for idx, sc in enumerate(scenarios, start=1):
                val_disp = repr(sc['value']) if len(str(sc['value'])) < 60 else repr(str(sc['value'])[:50] + "...")
                print(f"  [{idx:02d}] {sc['scenario']:<45} | Expected: HTTP {sc['expected']} | Value: {val_disp}")
            print()
        return 0

    catalog = get_fuzz_payloads(args.category)
    if args.json:
        print(json.dumps(catalog, indent=2, ensure_ascii=False))
    else:
        print(f"\n======================================================================")
        print(f"         ENTERPRISE EDGE-CASE FUZZING & SANITIZATION CATALOG          ")
        print(f"======================================================================")
        total_payloads = sum(len(items) for items in catalog.values())
        print(f"Categories: {len(catalog)} | Total Payloads: {total_payloads}\n")

        for cat, items in catalog.items():
            print(f"📁 [{cat.upper()}] ({len(items)} vectors):")
            for it in items:
                p_disp = repr(it['payload']) if len(str(it['payload'])) < 60 else repr(str(it['payload'])[:50] + "...")
                print(f"   • {it['name']:<35} -> HTTP {it['expected_status']} | {p_disp}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
