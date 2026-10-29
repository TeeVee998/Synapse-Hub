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
    def generate_playwright_har_harness(cls, har_path: str, mode: str = "replay", url_glob: str = "**/*", lang: str = "ts") -> str:
        """
        Generates Playwright Native Zero-Latency HAR Record & Replay harness.
        - record: Dumps real network traffic to HAR file.
        - replay: Intercepts all matching requests and returns responses from HAR with 0ms delay.
        """
        if mode == "record":
            if lang == "python":
                return "\n".join([
                    f"# --- ZERO-LATENCY HAR RECORDING HARNESS (Playwright Python) ---",
                    f"# Dumps live network traffic to '{har_path}'",
                    f"context = browser.new_context(",
                    f"    record_har_path='{har_path}',",
                    f"    record_har_mode='minimal',",
                    f"    record_har_url_filter='{url_glob}'",
                    f")",
                    f"page = context.new_page()",
                    f"# Note: Run 'python tools/network_mock_shield.py --har-sanitize {har_path}' before committing to git!"
                ])
            else:
                return "\n".join([
                    f"// --- ZERO-LATENCY HAR RECORDING HARNESS (Playwright TS) ---",
                    f"// Dumps live network traffic to '{har_path}'",
                    f"const context = await browser.newContext({{",
                    f"  recordHar: {{",
                    f"    path: '{har_path}',",
                    f"    mode: 'minimal',",
                    f"    urlFilter: '{url_glob}'",
                    f"  }}",
                    f"}});",
                    f"const page = await context.newPage();",
                    f"// Note: Run 'python tools/network_mock_shield.py --har-sanitize {har_path}' before committing to git!"
                ])
        else:
            # Replay Mode
            if lang == "python":
                return "\n".join([
                    f"# --- ZERO-LATENCY HAR REPLAY HARNESS (Playwright Python) ---",
                    f"# Replays 100% network responses from local HAR with 0ms delay (Immune to backend downtime)",
                    f"page.route_from_har(",
                    f"    har_id='{har_path}',",
                    f"    url='{url_glob}',",
                    f"    not_found='fallback',",
                    f"    update=False",
                    f")"
                ])
            else:
                return "\n".join([
                    f"// --- ZERO-LATENCY HAR REPLAY HARNESS (Playwright TS) ---",
                    f"// Replays 100% network responses from local HAR with 0ms delay (Immune to backend downtime)",
                    f"await page.routeFromHAR('{har_path}', {{",
                    f"  url: '{url_glob}',",
                    f"  notFound: 'fallback',",
                    f"  update: false",
                    f"}});"
                ])

    @classmethod
    def sanitize_har_file(cls, input_har_path: str, output_har_path: Optional[str] = None) -> int:
        """
        Parses a recorded HAR file and redacts sensitive PII & credentials:
        Bearer tokens, Authorization headers, Cookie headers, passwords, API keys.
        Returns the count of redacted entries.
        """
        import re
        if not os.path.exists(input_har_path):
            raise FileNotFoundError(f"HAR file not found: {input_har_path}")

        with open(input_har_path, "r", encoding="utf-8", errors="replace") as fp:
            data = json.load(fp)

        entries = data.get("log", {}).get("entries", [])
        redacted_count = 0

        pii_patterns = [
            (re.compile(r'"(password|pass|secret|token|api_?key|access_?token)"\s*:\s*"[^"]+"', re.IGNORECASE), r'"\1": "REDACTED_SECRET"'),
            (re.compile(r'"(credit_?card|card_?number|pan)"\s*:\s*"[^"]+"', re.IGNORECASE), r'"\1": "411111******1111"'),
            (re.compile(r'"(cvv|cvc)"\s*:\s*"[^"]+"', re.IGNORECASE), r'"\1": "999"'),
            (re.compile(r'"(email)"\s*:\s*"[^"]+"', re.IGNORECASE), r'"\1": "auto_user@enterprise.local"')
        ]

        for entry in entries:
            req = entry.get("request", {})
            # 1. Scrub Request Headers
            for header in req.get("headers", []):
                h_name = header.get("name", "").lower()
                if h_name in ("authorization", "cookie", "x-api-key", "token", "proxy-authorization"):
                    header["value"] = "Bearer REDACTED_TOKEN" if "bearer" in header.get("value", "").lower() else "REDACTED"
                    redacted_count += 1

            # 2. Scrub Request Post Data
            post_data = req.get("postData", {})
            if "text" in post_data:
                txt = post_data["text"]
                for pat, rep in pii_patterns:
                    txt = pat.sub(rep, txt)
                post_data["text"] = txt

            # 3. Scrub Response Headers (Set-Cookie)
            resp = entry.get("response", {})
            for header in resp.get("headers", []):
                h_name = header.get("name", "").lower()
                if h_name in ("set-cookie", "authorization"):
                    header["value"] = "REDACTED_COOKIE"
                    redacted_count += 1

        out_path = output_har_path or input_har_path
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

        return redacted_count

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

    # HAR Record & Replay options
    parser.add_argument("--har-mode", choices=["record", "replay"], default=None, help="Generate Playwright HAR record or replay harness")
    parser.add_argument("--har-path", default="fixtures/network_trace.har", help="Path to HAR archive file")
    parser.add_argument("--har-sanitize", default=None, help="Sanitize PII, tokens, and cookies from recorded HAR file")
    parser.add_argument("--har-out", default=None, help="Optional output path for sanitized HAR")

    args = parser.parse_args()

    # Handle HAR Sanitization
    if args.har_sanitize:
        redacted = NetworkMockShield.sanitize_har_file(args.har_sanitize, output_har_path=args.har_out)
        target = args.har_out or args.har_sanitize
        print(f"✅ [HAR SANITIZED] Scrubbed {redacted} sensitive headers/tokens in: {target}")
        return

    # Handle HAR Harness Generation
    if args.har_mode:
        code = NetworkMockShield.generate_playwright_har_harness(
            har_path=args.har_path,
            mode=args.har_mode,
            url_glob=args.url,
            lang=args.lang
        )
        print("======================================================================")
        print(f"  PLAYWRIGHT ZERO-LATENCY HAR {args.har_mode.upper()} HARNESS ({args.lang.upper()})")
        print("======================================================================")
        print(code)
        print("======================================================================")
        return

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
