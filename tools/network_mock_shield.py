#!/usr/bin/env python3
"""
API Network Mocking & Chaos Fault Injection Shield
--------------------------------------------------
Zero-Token Route Interception and Chaos Network Resilience Generator.
Decouples UI automation tests from unstable backend staging services,
rate limits, and 3rd-party payment gateways (Stripe, VNPAY, SMS OTP).
"""

import os
import json
import argparse
from typing import Dict, Any, Optional


class NetworkMockShield:
    """Zero-Token Network Interception & Chaos Fault Generator."""

    PRESETS = {
        "payment_success": {
            "status": 200,
            "body": {"status": "SUCCESS", "transactionId": "TX_MOCK_999888", "amount": 100.0, "currency": "USD"},
            "description": "Simulates successful 3rd-party payment gateway transaction"
        },
        "payment_declined": {
            "status": 402,
            "body": {"status": "FAILED", "code": "INSUFFICIENT_FUNDS", "message": "Card declined by issuing bank"},
            "description": "Simulates credit card decline / insufficient funds"
        },
        "auth_401_expired": {
            "status": 401,
            "body": {"error": "Unauthorized", "message": "JWT token expired. Please re-authenticate."},
            "description": "Simulates expired authentication session"
        },
        "auth_403_forbidden": {
            "status": 403,
            "body": {"error": "Forbidden", "message": "Insufficient permissions to access resource."},
            "description": "Simulates RBAC permission denial"
        },
        "rate_limit_429": {
            "status": 429,
            "body": {"error": "Too Many Requests", "retryAfter": 60},
            "description": "Simulates API rate limit throttling"
        },
        "server_crash_500": {
            "status": 500,
            "body": {"error": "Internal Server Error", "traceId": "ERR_500_MOCK"},
            "description": "Simulates unhandled backend exception"
        },
        "service_down_503": {
            "status": 503,
            "body": {"error": "Service Unavailable", "message": "Backend microservice unreachable"},
            "description": "Simulates backend downtime"
        }
    }

    THROTTLING_PROFILES = {
        "slow_3g": {"downloadThroughput": 500 * 1024 // 8, "uploadThroughput": 500 * 1024 // 8, "latency": 400},
        "fast_3g": {"downloadThroughput": 1.6 * 1024 * 1024 // 8, "uploadThroughput": 750 * 1024 // 8, "latency": 150},
        "high_latency": {"downloadThroughput": 10 * 1024 * 1024, "uploadThroughput": 5 * 1024 * 1024, "latency": 2500},
        "offline": {"offline": True, "downloadThroughput": 0, "uploadThroughput": 0, "latency": 0}
    }

    @classmethod
    def generate_playwright_ts(cls, url_pattern: str, status: int = 200, body: Optional[Dict[str, Any]] = None, delay_ms: int = 0) -> str:
        """Generates Playwright TypeScript route interception code."""
        body_json = json.dumps(body or {}, indent=2)
        code = [
            f"// Mock API Interception for '{url_pattern}'",
            f"await page.route('{url_pattern}', async (route) => {{",
        ]
        if delay_ms > 0:
            code.append(f"  await new Promise(r => setTimeout(r, {delay_ms}));")
        code.extend([
            "  await route.fulfill({",
            f"    status: {status},",
            "    contentType: 'application/json',",
            f"    body: JSON.stringify({body_json}),",
            "  });",
            "});"
        ])
        return "\n".join(code)

    @classmethod
    def generate_playwright_python(cls, url_pattern: str, status: int = 200, body: Optional[Dict[str, Any]] = None, delay_ms: int = 0) -> str:
        """Generates Playwright Python route interception code."""
        body_json = json.dumps(body or {})
        code = [
            f"# Mock API Interception for '{url_pattern}'",
            "import time, json",
            f"def handle_route(route):",
        ]
        if delay_ms > 0:
            code.append(f"    time.sleep({delay_ms / 1000.0})")
        code.extend([
            f"    route.fulfill(",
            f"        status={status},",
            f"        content_type='application/json',",
            f"        body=json.dumps({body_json})",
            f"    )",
            f"page.route('{url_pattern}', handle_route)"
        ])
        return "\n".join(code)

    @classmethod
    def generate_cypress_js(cls, url_pattern: str, method: str = "POST", status: int = 200, body: Optional[Dict[str, Any]] = None, delay_ms: int = 0) -> str:
        """Generates Cypress cy.intercept code."""
        body_json = json.dumps(body or {})
        delay_opt = f", delay: {delay_ms}" if delay_ms > 0 else ""
        return f"cy.intercept('{method}', '{url_pattern}', {{ statusCode: {status}, body: {body_json}{delay_opt} }}).as('mock_{url_pattern.split('/')[-1]}');"

    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, Any]:
        """Returns preset details or raises ValueError."""
        if preset_name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(cls.PRESETS.keys())}")
        return cls.PRESETS[preset_name]


def main():
    parser = argparse.ArgumentParser(description="API Network Mocking & Chaos Shield Generator")
    parser.add_argument("--url", default="**/api/**", help="URL pattern to intercept")
    parser.add_argument("--preset", choices=list(NetworkMockShield.PRESETS.keys()), default=None, help="Use pre-configured mock scenario")
    parser.add_argument("--status", type=int, default=200, help="HTTP response status code")
    parser.add_argument("--body", default=None, help="JSON response body string or file")
    parser.add_argument("--delay", type=int, default=0, help="Artificial latency in milliseconds")
    parser.add_argument("--lang", choices=["ts", "python", "cypress"], default="ts", help="Target script language")
    parser.add_argument("--list-presets", action="store_true", help="List all available presets")

    args = parser.parse_args()

    if args.list_presets:
        print("======================================================================")
        print("  AVAILABLE NETWORK MOCK & CHAOS FAULT PRESETS")
        print("======================================================================")
        for k, v in NetworkMockShield.PRESETS.items():
            print(f"• {k.ljust(22)}: Status {v['status']} - {v['description']}")
        print("======================================================================")
        return

    status = args.status
    body = {}

    if args.preset:
        preset = NetworkMockShield.get_preset(args.preset)
        status = preset["status"]
        body = preset["body"]
    elif args.body:
        if os.path.exists(args.body):
            with open(args.body, "r", encoding="utf-8") as f:
                body = json.load(f)
        else:
            body = json.loads(args.body)

    if args.lang == "ts":
        code = NetworkMockShield.generate_playwright_ts(args.url, status=status, body=body, delay_ms=args.delay)
    elif args.lang == "python":
        code = NetworkMockShield.generate_playwright_python(args.url, status=status, body=body, delay_ms=args.delay)
    else:
        code = NetworkMockShield.generate_cypress_js(args.url, status=status, body=body, delay_ms=args.delay)

    print("======================================================================")
    print(f"  NETWORK MOCK SHIELD GENERATED ({args.lang.upper()})")
    print("======================================================================")
    print(code)
    print("======================================================================")


if __name__ == "__main__":
    main()
