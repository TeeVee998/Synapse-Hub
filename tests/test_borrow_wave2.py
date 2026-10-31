#!/usr/bin/env python3
"""
Golden Tests for the Permissive-Repo Borrow Wave 2
---------------------------------------------------
Covers the upgrades borrowed from permissively-licensed ecosystem projects:
  - Testcontainers (Apache-2.0): db_sandbox wait-ready strategies (T1-T3)
  - OWASP ZAP (Apache-2.0): api_fuzzer passive/active modes + severity (T4-T7)
  - Selenium (Apache-2.0): heuristic matcher geometric relative locators (T8)
  - Locust (MIT): generate_jmx_plan locustfile emission + staged profiles (T9-T10)
  - playwright-mcp (Apache-2.0): MCP tool surface + ARIA snapshot (T11-T12)
"""

import os
import sys
import json
import math
import socket
import sqlite3
import tempfile
import threading
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


class BorrowWave2GoldenTests(unittest.TestCase):
    """Golden cases T1-T12 for the Wave-2 borrowed upgrades."""

    # ------------------------------------------------------------------
    # T1-T3: db_sandbox wait-ready (Testcontainers wait strategies)
    # ------------------------------------------------------------------

    def test_t1_wait_ready_sqlite_auto_detect(self):
        """T1: wait-ready auto-detects a SQLite file and passes instantly."""
        import db_sandbox
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "svc.db")
            sqlite3.connect(db_path).execute("PRAGMA schema_version").fetchone()
            res = db_sandbox.wait_for_ready(db_path, strategy="auto", timeout_sec=5.0)
            self.assertTrue(res["ready"])
            self.assertEqual(res["strategy"], "sqlite")
            self.assertIsNone(res["error"])

    def test_t2_wait_ready_port_probe(self):
        """T2: wait-ready port strategy passes for a listening socket and times out for a closed one."""
        import db_sandbox
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(5)
        port = srv.getsockname()[1]
        try:
            res = db_sandbox.wait_for_ready(f"127.0.0.1:{port}", strategy="port", timeout_sec=5.0)
            self.assertTrue(res["ready"], res)
        finally:
            srv.close()
        # Closed port must exhaust the deadline (1s) and report not-ready.
        res_closed = db_sandbox.wait_for_ready("127.0.0.1:59877", strategy="port", timeout_sec=1.0)
        self.assertFalse(res_closed["ready"])
        self.assertGreaterEqual(res_closed["attempts"], 1)

    def test_t3_wait_ready_http_probe(self):
        """T3: wait-ready http strategy passes when an HTTP service answers non-5xx."""
        import db_sandbox

        class OKHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *args):
                pass

        srv = HTTPServer(("127.0.0.1", 0), OKHandler)
        port = srv.server_address[1]
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            res = db_sandbox.wait_for_ready(f"http://127.0.0.1:{port}/health", strategy="http", timeout_sec=5.0)
            self.assertTrue(res["ready"], res)
        finally:
            srv.shutdown()
            srv.server_close()
        # A 5xx-rendering service is NOT ready. 59878 is closed -> URLError -> not ready.
        res_down = db_sandbox.wait_for_ready("http://127.0.0.1:59878/health", strategy="http", timeout_sec=1.0)
        self.assertFalse(res_down["ready"])

    # ------------------------------------------------------------------
    # T4-T7: api_fuzzer passive/active + severity (OWASP ZAP concepts)
    # ------------------------------------------------------------------

    SPEC = {
        "info": {"title": "T", "version": "1.0"},
        "paths": {
            "/api/admin/users": {
                "post": {
                    "requestBody": {"content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                        "required": ["name"],
                    }}}},
                }
            },
            "/api/health": {"get": {}},
        },
    }

    def test_t4_passive_scan_finds_unprotected_sensitive_path(self):
        """T4: passive scan flags mutating endpoints without declared security."""
        import api_fuzzer
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(self.SPEC, f)
            spec_path = f.name
        try:
            fuzzer = api_fuzzer.ApiFuzzer(base_url="http://localhost:8080", spec_path_or_url=spec_path)
            scorecard = fuzzer.run_passive_scan()
            self.assertEqual(scorecard["mode"], "PASSIVE")
            findings_text = json.dumps(scorecard["findings"])
            self.assertIn("AUTH_NOT_DECLARED", findings_text)
            self.assertIn("SENSITIVE_PATH_UNPROTECTED", findings_text)
            self.assertIn("NO_INPUT_VALIDATION_DECLARED", findings_text)
            self.assertGreaterEqual(scorecard["severity_summary"]["HIGH"], 2)
        finally:
            os.remove(spec_path)

    def test_t5_severity_taxonomy_mapping(self):
        """T5: alarm strings map onto the fixed ZAP-style severity taxonomy."""
        import api_fuzzer
        self.assertEqual(api_fuzzer.classify_alarm_severity("STACKTRACE_LEAK: leaks internals"), "CRITICAL")
        self.assertEqual(api_fuzzer.classify_alarm_severity("AUTH_BYPASS_VULNERABILITY: 200 without auth"), "CRITICAL")
        self.assertEqual(api_fuzzer.classify_alarm_severity("HTTP_500_SERVER_CRASH: panic"), "HIGH")
        self.assertEqual(api_fuzzer.classify_alarm_severity("SLA_TIMEOUT: 5000ms"), "LOW")
        self.assertEqual(api_fuzzer.classify_alarm_severity("CONNECTION_ERROR: refused"), "MEDIUM")

    def test_t6_payload_catalog_is_wired_into_mutations(self):
        """T6: the former dead fuzz_payloads import now generates catalog vectors."""
        import api_fuzzer
        fuzzer = api_fuzzer.ApiFuzzer(base_url="http://localhost:8080")
        mutations = fuzzer.generate_mutations({
            "path": "/api/items",
            "method": "POST",
            "properties": {"title": {"type": "string"}, "qty": {"type": "integer"}},
        })
        names = json.dumps(mutations)
        self.assertIn("XSS Universal Polyglot", names)
        self.assertIn("Emoji Surrogate", names)
        self.assertIn("64-bit BigInt", names)
        self.assertGreater(len(mutations), 20, "catalog wiring should expand the mutation set")

    def test_t7_unreachable_target_never_passes(self):
        """T7: connection failure must FAIL, never PASS (Truth Anchor)."""
        import api_fuzzer
        fuzzer = api_fuzzer.ApiFuzzer(base_url="http://127.0.0.1:59879")
        res = fuzzer.execute_request({"name": "probe", "type": "BASELINE", "path": "/x", "method": "GET", "headers": {}})
        self.assertLess(res["status_code"], 0)
        self.assertTrue(any(a.startswith("CONNECTION_ERROR") for a in res["alarms"]))
        self.assertEqual(res["verdict"], "FAIL")

    # ------------------------------------------------------------------
    # T8: heuristic matcher geometric relative locators (Selenium concept)
    # ------------------------------------------------------------------

    SNAPSHOT = [
        {"id": "email", "tag": "input", "x": 100, "y": 100, "width": 300, "height": 40},
        {"id": "password", "tag": "input", "x": 100, "y": 160, "width": 300, "height": 40},
        {"id": "login-btn", "tag": "button", "text": "Sign In", "x": 100, "y": 220, "width": 140, "height": 44},
        {"id": "footer-btn", "tag": "button", "text": "Footer", "x": 100, "y": 900, "width": 140, "height": 40},
    ]

    def test_t8_geometric_relative_matching(self):
        """T8: relative={relation, anchor} picks the geometrically correct element."""
        from heuristic_locator_matcher import HeuristicLocatorMatcher
        below = HeuristicLocatorMatcher.match(
            "submit", dom_snapshot=self.SNAPSHOT, relative={"relation": "below", "anchor": "#password"})
        self.assertEqual(below["strategy"], "GEOMETRIC_RELATIVE_MATCH")
        self.assertEqual(below["healed_locator"], "#login-btn")

        above = HeuristicLocatorMatcher.match(
            "email", dom_snapshot=self.SNAPSHOT, relative={"relation": "above", "anchor": "#password"})
        self.assertEqual(above["healed_locator"], "#email")

        near = HeuristicLocatorMatcher.match(
            "input", dom_snapshot=self.SNAPSHOT, relative={"relation": "near", "anchor": "#login-btn"})
        self.assertEqual(near["healed_locator"], "#password")

        # No bounding boxes -> graceful fallback to the order-based heuristic.
        bbox_free = [{"id": "password", "tag": "input"}, {"id": "go", "tag": "button"}]
        fallback = HeuristicLocatorMatcher.match(
            "submit", dom_snapshot=bbox_free, relative={"relation": "below", "anchor": "#password"})
        self.assertEqual(fallback["strategy"], "SPATIAL_ANCHOR_PROXIMITY")
        self.assertEqual(fallback["healed_locator"], "#go")

    # ------------------------------------------------------------------
    # T9-T10: generate_jmx_plan locustfile + staged profiles (Locust)
    # ------------------------------------------------------------------

    SAMPLERS = [
        {"name": "Browse Catalog", "path": "/api/items", "method": "GET", "body": "", "expected_status": 200},
        {"name": "Create Order", "path": "/api/orders", "method": "POST",
         "body": '{"item": "PERF_AUTO_${__time(HMS,)}", "qty": "${RANDOM_ITEM_ID}"}', "expected_status": 201},
        {"name": "Check Status", "path": "/api/status", "method": "GET", "body": "", "expected_status": 200},
    ]

    def _jmx(self, workload, vus=100, ramp=30, duration=300):
        import generate_jmx_plan as g
        return g.build_jmx_xml(
            plan_name="T", base_host="h", protocol="https", port="443",
            vus=vus, ramp_up=ramp, duration=duration, loop_count=-1, sla_p95=500,
            samplers=[dict(s, path=s["path"], body=s["body"]) for s in self.SAMPLERS],
            enable_cookies=True, enable_cache=True, csv_file=None, csv_variables="",
            group_transactions=False, weighted_mix=None, deep_correlation=True,
            workload_profile=workload, jsr223_hmac=False, influxdb_url=None,
            perfmon_server=None, think_time_min=0, think_time_max=0,
        )

    def test_t9_staged_step_profile_generates_stage_thread_groups(self):
        """T9: step profile emits 4 staged ThreadGroups with ladder threads; linear keeps P-props."""
        step_xml = self._jmx("step")
        self.assertEqual(step_xml.count(") - Stage "), 4)
        self.assertIn("Stage 1", step_xml)
        stage_threads = [int(t) for t in
                         __import__("re").findall(r'ThreadGroup.num_threads">(\d+)</stringProp>', step_xml)]
        self.assertEqual(stage_threads, [25, 50, 75, 100])
        self.assertEqual(step_xml.count("jmeter_results.jtl"), 1, "single plan-level JTL collector")

        linear_xml = self._jmx("linear", vus=50)
        self.assertIn("${__P(vus,50)}", linear_xml, "linear profile keeps property-overridable form")
        self.assertNotIn("Stage 2", linear_xml)

        spike_xml = self._jmx("spike", vus=50)
        self.assertEqual(spike_xml.count(") - Stage "), 3)

    def test_t10_locustfile_emission_is_valid_python(self):
        """T10: --emit-locust produces a compilable locustfile with weighted tasks."""
        import generate_jmx_plan as g
        source = g.generate_locustfile(
            plan_name="Enterprise Checkout API",
            base_host="api.staging.local", protocol="https", port="443",
            samplers=self.SAMPLERS, weighted_mix="70,30",
            think_time_min_ms=500, think_time_max_ms=1500,
        )
        compile(source, "<locustfile>", "exec")  # raises SyntaxError if invalid
        self.assertIn("class EnterpriseCheckoutApi(HttpUser):", source)
        self.assertIn("@task(", source)
        self.assertIn("wait_time = between(0.50, 1.50)", source)
        self.assertIn("{ts}", source)  # runtime datetime token survived escaping
        self.assertIn("{{", source)    # JSON braces escaped for .format()

    # ------------------------------------------------------------------
    # T11-T12: MCP tool surface + ARIA snapshot (playwright-mcp concepts)
    # ------------------------------------------------------------------

    def test_t11_mcp_server_exposes_new_tools_and_fixed_cache_query(self):
        """T11: tools/list includes the new tools; query_memory_cache no longer errors."""
        import mcp_server
        listing = mcp_server.process_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [t["name"] for t in listing["result"]["tools"]]
        self.assertIn("compile_gherkin_suite", names)
        self.assertIn("fuzz_api", names)
        self.assertGreaterEqual(len(names), 18)

        cache_call = mcp_server.process_message({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "query_memory_cache",
                       "arguments": {"error_signature": "NoSuchElementException: no such element"}}})
        self.assertFalse(cache_call["result"].get("isError", False),
                         "query_memory_cache must not raise after the query_solution fix")

        gherkin_call = mcp_server.process_message({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "compile_gherkin_suite",
                       "arguments": {"target": os.path.join(
                           REPO_ROOT, ".agents/skills/gherkin-to-suite/examples/checkout.feature")}}})
        data = json.loads(gherkin_call["result"]["content"][0]["text"])
        self.assertEqual(data["totals"]["expanded_cases"], 5)
        self.assertEqual(data["health_score_pct"], 100.0)

    def test_t12_browser_helpers_has_aria_snapshot(self):
        """T12: browser_helpers.js ships ariaSnapshot in Playwright-MCP format."""
        with open(os.path.join(TOOLS_DIR, "browser_helpers.js"), "r", encoding="utf-8") as f:
            source = f.read()
        self.assertIn("ariaSnapshot:", source)
        self.assertIn("__version: '2.3.1'", source)
        self.assertIn("[ref=e", source)      # ARIA snapshot refs
        self.assertIn("[disabled]", source)  # state suffixes
        self.assertIn("[level=", source)     # heading levels


if __name__ == "__main__":
    unittest.main()
