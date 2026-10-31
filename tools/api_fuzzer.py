#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Autonomous API Fuzzing & Chaos Breaker
-------------------------------------------------
Zero-dependency, active runtime API mutator and resilience tester.
Ingests OpenAPI 3.x / Swagger 2.0 specifications (or endpoint catalogs),
generates dynamic boundary, type-inverted, and adversarial fuzzing payloads,
and executes live HTTP/S requests against staging/test APIs.

Three-Alarm Oracle Detection:
  1. HTTP 500 / 502 / 503 Internal Server Error (Backend crash / unhandled fault)
  2. Database & Framework Stacktrace Leaks (SQL injection reflection, Django/Spring/Postgres traces)
  3. SLA Latency Breach (> 3000ms response time - potential ReDoS or lock contention)
"""

import os
import re
import sys
import json
import time
import ssl
import urllib.request
import urllib.error
import urllib.parse
import argparse
from typing import Dict, Any, List, Optional, Tuple

# Enforce UTF-8 stdout encoding for Windows/macOS/Linux compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REPORTS_DIR = os.path.join(HUB_ROOT, "reports")

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from fuzz_payloads import get_fuzz_payloads, get_field_fuzz_scenarios
except ImportError:
    get_fuzz_payloads = None
    get_field_fuzz_scenarios = None

# Stacktrace and DB leak pattern signatures
STACKTRACE_LEAK_PATTERNS = [
    re.compile(r'Traceback \(most recent call last\):', re.IGNORECASE),
    re.compile(r'Exception in thread "[^"]+"', re.IGNORECASE),
    re.compile(r'\b(org\.springframework|org\.hibernate|java\.lang\.NullPointerException)\b', re.IGNORECASE),
    re.compile(r'\b(psycopg2\.(OperationalError|ProgrammingError)|PSQLException)\b', re.IGNORECASE),
    re.compile(r'\b(mysql_error|mysqli_sql_exception|pymysql\.err)\b', re.IGNORECASE),
    re.compile(r'\b(sqlite3\.OperationalError|SQLiteException)\b', re.IGNORECASE),
    re.compile(r'\b(django\.db\.utils|sqlalchemy\.exc)\b', re.IGNORECASE),
    re.compile(r'SQLSTATE\[[0-9A-Z]{5}\]', re.IGNORECASE),
    re.compile(r'syntax error at or near\s+"', re.IGNORECASE),
    re.compile(r'ODBC SQL Server Driver', re.IGNORECASE),
]

# Severity taxonomy (concept borrowed from OWASP ZAP's alert risk levels,
# Apache-2.0 - re-expressed for the fuzz oracle). Each alarm class maps to a
# fixed risk level so CI can gate on CRITICAL findings alone.
ALARM_SEVERITY = {
    "HTTP_": "HIGH",            # HTTP_500/502/503_SERVER_CRASH
    "STACKTRACE_LEAK": "CRITICAL",
    "SLA_TIMEOUT": "LOW",
    "AUTH_BYPASS": "CRITICAL",
    "CONNECTION_ERROR": "MEDIUM",
}
SEVERITY_LEVELS = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


def classify_alarm_severity(alarm: str) -> str:
    """Maps an alarm string onto the ZAP-style severity taxonomy."""
    for prefix, severity in ALARM_SEVERITY.items():
        if alarm.startswith(prefix):
            return severity
    return "INFO"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class ApiFuzzer:
    """Autonomous runtime API fuzzer with three-alarm defect Oracle."""

    def __init__(
        self,
        base_url: str,
        spec_path_or_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_sec: float = 10.0,
        sla_ms: float = 3000.0,
        verify_ssl: bool = False
    ):
        self.base_url = base_url.rstrip("/")
        self.spec_path = spec_path_or_url
        self.custom_headers = headers or {"Content-Type": "application/json", "User-Agent": "AgentQA-Fuzzer/2.0"}
        self.timeout_sec = timeout_sec
        self.sla_ms = sla_ms
        self.verify_ssl = verify_ssl

        # Environment Allowlist Guard (F2 Safety Discipline)
        # Prevents accidental fuzzing or stress bombardment against production environments
        parsed = urllib.parse.urlparse(self.base_url)
        host = (parsed.hostname or "").lower()
        is_safe_env = any(
            token in host for token in [
                "localhost", "127.0.0.1", "::1", "staging", "dev", "test", "qa", "sandbox", "local", "internal"
            ]
        )
        if host and not is_safe_env and not os.environ.get("SYNAPSE_ALLOW_PROD_FUZZ"):
            raise PermissionError(
                f"[SAFETY FIREWALL - REJECTED] Target host '{host}' is not in the allowed non-production environment allowlist "
                "(localhost, staging, dev, test, qa, sandbox). Set SYNAPSE_ALLOW_PROD_FUZZ=1 only if authorized."
            )

        # Prepare SSL context (support self-signed staging certificates)
        self.ssl_context = ssl.create_default_context()
        if not verify_ssl:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def load_spec(self) -> Dict[str, Any]:
        """Loads OpenAPI or Swagger specification from file or URL."""
        if not self.spec_path:
            # Fallback default health and mock endpoints
            return {
                "paths": {
                    "/api/v1/users": {
                        "post": {
                            "summary": "Create user",
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "username": {"type": "string", "maxLength": 50},
                                                "age": {"type": "integer", "minimum": 1, "maximum": 120},
                                                "email": {"type": "string"}
                                            },
                                            "required": ["username"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

        if self.spec_path.startswith(("http://", "https://")):
            req = urllib.request.Request(self.spec_path, headers={"User-Agent": "AgentQA-Fuzzer/2.0"})
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=10.0) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        else:
            if not os.path.exists(self.spec_path):
                raise FileNotFoundError(f"OpenAPI spec not found: {self.spec_path}")
            with open(self.spec_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def extract_fuzz_targets(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts actionable API routes and property schemas from spec."""
        targets = []
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method, details in path_item.items():
                if method.lower() not in ("get", "post", "put", "patch", "delete"):
                    continue

                req_body = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                props = req_body.get("properties", {})
                required = req_body.get("required", [])

                targets.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", f"{method.upper()} {path}"),
                    "parameters": details.get("parameters", []),
                    "properties": props,
                    "required": required
                })
        return targets

    def generate_mutations(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates dynamic mutation vectors for query params and request body."""
        mutations = []
        props = target.get("properties", {})
        method = target["method"]
        path = target["path"]

        # Base valid skeleton
        valid_body: Dict[str, Any] = {}
        for p_name, p_schema in props.items():
            t = p_schema.get("type", "string")
            if t == "string":
                valid_body[p_name] = f"valid_{p_name}"
            elif t in ("integer", "number"):
                valid_body[p_name] = 10
            elif t == "boolean":
                valid_body[p_name] = True
            else:
                valid_body[p_name] = "test"

        # 1. Baseline Happy-Path
        mutations.append({
            "name": f"{method} {path} - Baseline Happy-Path",
            "type": "BASELINE",
            "path": path,
            "method": method,
            "body": valid_body,
            "headers": self.custom_headers
        })

        # 2. Field Fuzzing Payloads
        for p_name, p_schema in props.items():
            p_type = p_schema.get("type", "string")

            # A. Extreme Buffer Stress (10,000 chars)
            mut_body = dict(valid_body)
            mut_body[p_name] = "A" * 10000
            mutations.append({
                "name": f"{method} {path} - Buffer Stress on '{p_name}'",
                "type": "BUFFER_STRESS",
                "path": path,
                "method": method,
                "body": mut_body,
                "headers": self.custom_headers
            })

            # B. SQLi Polyglot Probe
            mut_body = dict(valid_body)
            mut_body[p_name] = "' OR '1'='1' -- /* injected */"
            mutations.append({
                "name": f"{method} {path} - SQLi Polyglot Probe on '{p_name}'",
                "type": "SQLI_INJECTION",
                "path": path,
                "method": method,
                "body": mut_body,
                "headers": self.custom_headers
            })

            # C. Unicode BiDi / RTL Trojan Source
            mut_body = dict(valid_body)
            mut_body[p_name] = "\u202E\u0041\u0042\u0043_AUTO_TX"
            mutations.append({
                "name": f"{method} {path} - Unicode BiDi RTL Override on '{p_name}'",
                "type": "BIDI_UNICODE",
                "path": path,
                "method": method,
                "body": mut_body,
                "headers": self.custom_headers
            })

            # D. Null Byte Injection
            mut_body = dict(valid_body)
            mut_body[p_name] = f"data\x00{p_name}.json"
            mutations.append({
                "name": f"{method} {path} - Null Byte Injection on '{p_name}'",
                "type": "NULL_BYTE",
                "path": path,
                "method": method,
                "body": mut_body,
                "headers": self.custom_headers
            })

            # E. Numeric Boundaries (if integer)
            if p_type in ("integer", "number"):
                mut_body = dict(valid_body)
                mut_body[p_name] = 2147483648  # 32-bit overflow
                mutations.append({
                    "name": f"{method} {path} - 32-bit Integer Overflow on '{p_name}'",
                    "type": "NUMERIC_OVERFLOW",
                    "path": path,
                    "method": method,
                    "body": mut_body,
                    "headers": self.custom_headers
                })

            # F. Type Inversion (String where integer expected or vice versa)
            mut_body = dict(valid_body)
            mut_body[p_name] = 99999 if p_type == "string" else "NOT_A_NUMBER"
            mutations.append({
                "name": f"{method} {path} - Type Mutation on '{p_name}'",
                "type": "TYPE_MUTATION",
                "path": path,
                "method": method,
                "body": mut_body,
                "headers": self.custom_headers
            })

        # 3. Auth Bypass Vector (Remove Authorization Header)
        mut_headers = {k: v for k, v in self.custom_headers.items() if k.lower() != "authorization"}
        mutations.append({
            "name": f"{method} {path} - Auth Token Omission Probe",
            "type": "AUTH_OMISSION",
            "path": path,
            "method": method,
            "body": valid_body,
            "headers": mut_headers
        })

        # 4. Catalog-Driven Vectors via tools/fuzz_payloads.py (XSS polyglots,
        #    emoji surrogates, numeric boundaries). Formerly a dead import -
        #    now wired into generation so the catalog actually fires.
        if get_field_fuzz_scenarios is not None:
            existing_names = {m["name"] for m in mutations}
            for p_name, p_schema in props.items():
                p_type = p_schema.get("type", "string")
                for scen in get_field_fuzz_scenarios(p_name, p_type):
                    mut_body = dict(valid_body)
                    mut_body[p_name] = scen["value"]
                    name = f"{method} {path} - {scen['scenario']}"
                    if name in existing_names:
                        continue
                    existing_names.add(name)
                    mutations.append({
                        "name": name,
                        "type": scen["category"],
                        "path": path,
                        "method": method,
                        "body": mut_body,
                        "headers": self.custom_headers
                    })

        return mutations

    def execute_request(self, mutation: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Dispatches HTTP mutation and evaluates the three-alarm Oracle."""
        url = f"{self.base_url}{mutation['path']}"
        method = mutation["method"]
        body_data = None
        if method in ("POST", "PUT", "PATCH") and mutation.get("body") is not None:
            body_data = json.dumps(mutation["body"]).encode("utf-8")

        if dry_run:
            # Deterministic offline mock for CI & local checks
            return {
                "name": mutation["name"],
                "type": mutation["type"],
                "url": url,
                "method": method,
                "status_code": 400 if mutation["type"] != "BASELINE" else 200,
                "duration_ms": 42.5,
                "verdict": "PASS",
                "severity": "INFO",
                "alarms": [],
                "response_preview": '{"status": "handled_by_dry_run"}'
            }

        req = urllib.request.Request(
            url=url,
            data=body_data,
            headers=mutation["headers"],
            method=method
        )

        start_time = time.time()
        status_code = 0
        response_body = ""
        duration_ms = 0.0

        try:
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout_sec) as resp:
                status_code = resp.getcode()
                response_body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as he:
            status_code = he.code
            try:
                response_body = he.read().decode("utf-8", errors="replace")
            except Exception:
                response_body = str(he)
        except urllib.error.URLError as ue:
            status_code = -1
            response_body = str(ue.reason)
        except Exception as e:
            status_code = -2
            response_body = str(e)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # ----------------------------------------------------
        # THREE-ALARM DEFECT ORACLE EVALUATION
        # ----------------------------------------------------
        alarms = []

        # Alarm 1: HTTP 500 / 502 / 503 Internal Server Error
        if status_code in (500, 502, 503):
            alarms.append(f"HTTP_{status_code}_SERVER_CRASH: Unhandled backend exception / server panic")

        # Alarm 2: Database / Framework Stacktrace Leak
        for pattern in STACKTRACE_LEAK_PATTERNS:
            if pattern.search(response_body):
                matched = pattern.pattern
                alarms.append(f"STACKTRACE_LEAK: Response leaks backend internals matching '{matched}'")
                break

        # Alarm 3: SLA Latency Breach (> 3000ms)
        if duration_ms > self.sla_ms:
            alarms.append(f"SLA_TIMEOUT: Response took {duration_ms}ms (threshold: {self.sla_ms}ms), possible ReDoS or DB lock")

        # Alarm 4: Auth Bypass (OMISSION succeeded with 200/201)
        if mutation["type"] == "AUTH_OMISSION" and status_code in (200, 201):
            alarms.append("AUTH_BYPASS_VULNERABILITY: Endpoint returned 200 OK without Authorization header")

        # Alarm 5: Target unreachable - an endpoint that could not be tested
        # must NEVER be reported as PASS (Truth Anchor discipline).
        if status_code < 0:
            alarms.append("CONNECTION_ERROR: Target unreachable or transport failure - endpoint could not be verified")

        verdict = "FAIL" if alarms else "PASS"
        severity = "INFO"
        if alarms:
            severity = max(
                (classify_alarm_severity(a) for a in alarms),
                key=lambda s: SEVERITY_LEVELS.index(s)
            )

        return {
            "name": mutation["name"],
            "type": mutation["type"],
            "url": url,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "verdict": verdict,
            "severity": severity,
            "alarms": alarms,
            "response_preview": response_body[:300]
        }

    def run_fuzz_suite(self, dry_run: bool = False) -> Dict[str, Any]:
        """Runs the complete fuzzing suite against all extracted targets."""
        spec = self.load_spec()
        targets = self.extract_fuzz_targets(spec)

        all_mutations = []
        for t in targets:
            all_mutations.extend(self.generate_mutations(t))

        results = []
        total_failures = 0

        print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
        print(f"{BOLD}{CYAN}      ENTERPRISE AUTONOMOUS API FUZZING & CHAOS BREAKER               {RESET}")
        print(f"{BOLD}{CYAN}======================================================================{RESET}")
        print(f"  Target Base URL   : {self.base_url}")
        print(f"  Spec Source       : {self.spec_path or 'Default Archetype'}")
        print(f"  Total Endpoints   : {len(targets)}")
        print(f"  Total Mutations   : {len(all_mutations)}")
        print(f"  SLA Threshold     : {self.sla_ms} ms")
        print(f"  Mode              : {'DRY-RUN (Air-Gapped / Deterministic)' if dry_run else 'LIVE STAGING ATTACK'}\n")

        for idx, m in enumerate(all_mutations, start=1):
            res = self.execute_request(m, dry_run=dry_run)
            results.append(res)

            status_str = f"{GREEN}PASS{RESET}" if res["verdict"] == "PASS" else f"{RED}ALARM{RESET}"
            sys.stdout.write(f"  [{idx:03d}/{len(all_mutations):03d}] {status_str} | HTTP {res['status_code']} ({res['duration_ms']}ms) | {m['name']}\n")
            if res["alarms"]:
                total_failures += 1
                for alarm in res["alarms"]:
                    print(f"       👉 {RED}{BOLD}[DEFECT]{RESET} {alarm}")

        scorecard = {
            "base_url": self.base_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "ACTIVE",
            "total_mutations": len(all_mutations),
            "passed": len(all_mutations) - total_failures,
            "failed": total_failures,
            "sla_ms": self.sla_ms,
            "dry_run": dry_run,
            "severity_summary": self._severity_summary(results),
            "results": results
        }

        # Print Summary Scorecard
        print(f"\n{BOLD}======================================================================{RESET}")
        print(f"{BOLD}                   API FUZZING ORACLE SCORECARD                       {RESET}")
        print(f"{BOLD}======================================================================{RESET}")
        print(f"  Mutations Executed: {scorecard['total_mutations']}")
        print(f"  Clean Handled     : {GREEN}{scorecard['passed']}{RESET}")
        print(f"  Defects Detected  : {RED if total_failures > 0 else GREEN}{scorecard['failed']}{RESET}")
        print(f"  Severity Mix      : {scorecard['severity_summary']}")
        if total_failures == 0:
            print(f"  Verdict           : {GREEN}[PASS] API resilient against input fuzzing & chaos.{RESET}")
        else:
            print(f"  Verdict           : {RED}[FAIL] {total_failures} defect alarms detected. Backend fixes required!{RESET}")
        print(f"======================================================================\n")

        # Save Report
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, "api_fuzz_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2)
        print(f"Full telemetry report saved to: {report_path}")

        return scorecard

    @staticmethod
    def _severity_summary(results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Counts findings per severity level (ZAP-style risk mix)."""
        summary = {level: 0 for level in SEVERITY_LEVELS}
        for res in results:
            sev = res.get("severity", "INFO")
            if sev in summary:
                summary[sev] += 1
        return summary

    def run_passive_scan(self) -> Dict[str, Any]:
        """Offline spec-level audit (no HTTP dispatched).

        Concept borrowed from OWASP ZAP's passive scanning (Apache-2.0):
        findings are pre-flight advisories derived purely from the OpenAPI/
        Swagger document - unreachable endpoints cannot fake a pass here
        because nothing is dispatched at all.
        """
        spec = self.load_spec()
        has_global_security = bool(spec.get("security"))
        findings: List[Dict[str, Any]] = []

        for path, methods in spec.get("paths", {}).items():
            for method, op in methods.items():
                if method.lower() not in ("get", "post", "put", "patch", "delete"):
                    continue
                op_security = op.get("security") if isinstance(op, dict) else None
                is_protected = has_global_security or bool(op_security)
                label = f"{method.upper()} {path}"

                if not is_protected and method.lower() in ("post", "put", "patch", "delete"):
                    severity = "HIGH" if re.search(r"admin|internal|user", path, re.IGNORECASE) else "MEDIUM"
                    findings.append({
                        "finding": f"AUTH_NOT_DECLARED: Mutating endpoint declares no security requirement",
                        "severity": severity,
                        "target": label,
                        "recommendation": "Declare securitySchemes/security for this operation or document why it is public.",
                    })

                if not is_protected and re.search(r"admin|internal", path, re.IGNORECASE):
                    findings.append({
                        "finding": "SENSITIVE_PATH_UNPROTECTED: Administrative/internal path is publicly declared",
                        "severity": "HIGH",
                        "target": label,
                        "recommendation": "Gate this path behind an authentication scheme and network policy.",
                    })

                body = op.get("requestBody", {}) if isinstance(op, dict) else {}
                content = body.get("content", {}).get("application/json", {}) if isinstance(body, dict) else {}
                schema = content.get("schema", {})
                props = schema.get("properties", {}) if isinstance(schema, dict) else {}
                unbounded = [
                    p_name for p_name, p_schema in props.items()
                    if isinstance(p_schema, dict)
                    and p_schema.get("type") == "string"
                    and not any(k in p_schema for k in ("maxLength", "pattern", "enum", "format"))
                ]
                if unbounded:
                    findings.append({
                        "finding": f"NO_INPUT_VALIDATION_DECLARED: unbounded string props {unbounded[:5]}",
                        "severity": "LOW",
                        "target": label,
                        "recommendation": "Add maxLength/pattern/enum constraints so the contract rejects oversized input.",
                    })

        if not spec.get("info") and spec.get("paths"):
            findings.append({
                "finding": "SPEC_METADATA_MISSING: OpenAPI info block absent",
                "severity": "INFO",
                "target": self.spec_path or "inline-spec",
                "recommendation": "Document title/version/contact so scan reports are traceable to an owner.",
            })

        severity_summary = {level: 0 for level in SEVERITY_LEVELS}
        for f in findings:
            severity_summary[f["severity"]] += 1

        blocking = severity_summary["HIGH"] + severity_summary["CRITICAL"]

        print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
        print(f"{BOLD}{CYAN}          API PASSIVE SCAN (Offline Spec Audit - Zero Traffic)        {RESET}")
        print(f"{BOLD}{CYAN}======================================================================{RESET}")
        print(f"  Spec Source        : {self.spec_path or 'Default Archetype'}")
        print(f"  Findings           : {YELLOW if findings else GREEN}{len(findings)}{RESET}")
        print(f"  Severity Mix       : {severity_summary}")
        if blocking:
            print(f"  Verdict            : {RED}[FAIL] {blocking} HIGH/CRITICAL pre-flight finding(s).{RESET}")
        else:
            print(f"  Verdict            : {GREEN}[PASS] No HIGH/CRITICAL spec-level finding.{RESET}")
        print(f"======================================================================\n")
        for f in findings:
            print(f"  - [{f['severity']}] {f['target']} - {f['finding']}")
            print(f"      👉 {f['recommendation']}")

        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, "api_fuzz_report.json")
        scorecard = {
            "base_url": self.base_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "PASSIVE",
            "spec_source": self.spec_path or "Default Archetype",
            "total_findings": len(findings),
            "severity_summary": severity_summary,
            "findings": findings,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2)
        print(f"\nFull telemetry report saved to: {report_path}")

        return scorecard


def main():
    parser = argparse.ArgumentParser(description="Enterprise Autonomous API Fuzzer & Chaos Breaker")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL of target API server")
    parser.add_argument("--spec", default=None, help="Path or URL to OpenAPI/Swagger JSON specification")
    parser.add_argument("--token", default=None, help="Bearer token for authenticated endpoints")
    parser.add_argument("--sla-ms", type=float, default=3000.0, help="SLA latency ceiling in ms (default: 3000ms)")
    parser.add_argument("--mode", choices=["active", "passive"], default="active",
                        help="active = live fuzzing (default); passive = offline spec audit, zero traffic")
    parser.add_argument("--dry-run", action="store_true", help="Simulate mutation generation without live requests")
    parser.add_argument("--json", action="store_true", help="Output summary in JSON format")

    args = parser.parse_args()

    headers = {"Content-Type": "application/json", "User-Agent": "AgentQA-Fuzzer/2.0"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    fuzzer = ApiFuzzer(
        base_url=args.base_url,
        spec_path_or_url=args.spec,
        headers=headers,
        sla_ms=args.sla_ms
    )

    if args.mode == "passive":
        scorecard = fuzzer.run_passive_scan()
        if args.json:
            print(json.dumps(scorecard, indent=2))
        blocking = scorecard["severity_summary"]["HIGH"] + scorecard["severity_summary"]["CRITICAL"]
        return 1 if blocking > 0 else 0

    scorecard = fuzzer.run_fuzz_suite(dry_run=args.dry_run)
    if args.json:
        print(json.dumps(scorecard, indent=2))

    critical = scorecard["severity_summary"].get("CRITICAL", 0)
    if critical > 0:
        return 1
    return 1 if scorecard["failed"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
