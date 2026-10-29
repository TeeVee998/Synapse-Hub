#!/usr/bin/env python3
"""
Enterprise Automated Testing Suite for AI Agent Tools & Hub Integrity
----------------------------------------------------------------------
Verifies the syntactic correctness, importability, and deterministic
behavior of all centralized tools in `tools/` using standard library `unittest`.
Contains real behavioral assertions and fixture-based functional tests.
"""

import os
import sys
import json
import tempfile
import io
import subprocess
import unittest
from pathlib import Path

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

import infer_linter
import lint_ai_docs
import distill_log
import cache_resolver
import verify_all
import wcag_audit
import cli
import flaky_detector
import repo_map
import validate_groovy_scripts
import check_env
import test_impact
import trace_data_flow
import analyze_project

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class TestToolsIntegrityAndBehavior(unittest.TestCase):
    """Automated unit and functional tests for tools in tools/."""

    def test_skills_manifest_integrity(self):
        """Validates that skills_manifest.json matches disk files."""
        manifest_path = os.path.join(REPO_ROOT, "skills_manifest.json")
        self.assertTrue(os.path.exists(manifest_path), "skills_manifest.json must exist")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("version"), "2.0.1", "Manifest version must be 2.0.1")
        manifest_skills = [s["id"] for s in data.get("skills", [])]
        self.assertEqual(len(manifest_skills), 27, "Manifest must declare exactly 27 skills")

        skills_dir = os.path.join(REPO_ROOT, ".agents", "skills")
        for skill_id in manifest_skills:
            skill_md = os.path.join(skills_dir, skill_id, "SKILL.md")
            self.assertTrue(os.path.exists(skill_md), f"Skill file must exist: {skill_md}")

    def test_browser_helpers_exists_and_complete(self):
        """Validates that browser_helpers.js exists and exports core capabilities."""
        helper_path = os.path.join(TOOLS_DIR, "browser_helpers.js")
        self.assertTrue(os.path.exists(helper_path), "tools/browser_helpers.js must exist")

        with open(helper_path, "r", encoding="utf-8") as f:
            code = f.read()

        expected_methods = ["batch:", "audit:", "heal:", "clickSafe:", "exportSession:", "isStable:"]
        for method in expected_methods:
            self.assertIn(method, code, f"browser_helpers.js missing method: {method}")

    def test_npm_package_and_launcher_integrity(self):
        """Validates that package.json and bin/agent-qa.js exist, export valid bin entries, and pass version check."""
        pkg_path = os.path.join(REPO_ROOT, "package.json")
        bin_path = os.path.join(REPO_ROOT, "bin", "agent-qa.js")
        self.assertTrue(os.path.exists(pkg_path), "package.json must exist")
        self.assertTrue(os.path.exists(bin_path), "bin/agent-qa.js must exist")

        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg_data = json.load(f)

        self.assertEqual(pkg_data.get("name"), "synapse-hub")
        self.assertEqual(pkg_data.get("version"), "2.0.1")
        self.assertIn("synapse-hub", pkg_data.get("bin", {}))
        self.assertIn("synapse", pkg_data.get("bin", {}))
        self.assertIn("agent-qa", pkg_data.get("bin", {}))

        # Test node bin launcher execution
        res = subprocess.run(["node", bin_path, "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=REPO_ROOT)
        self.assertEqual(res.returncode, 0, f"Node bin launcher failed: {res.stderr}")
        self.assertIn("Agent-QA Hub CLI v2.0.1", res.stdout)

    def test_cache_resolver_cosine_similarity(self):
        """Validates compute_cosine_similarity calculation in cache_resolver."""
        t1 = "ElementClickInterceptedException timeout error"
        t2 = "ElementClickInterceptedException timeout error"
        t3 = "Completely different issue unrelated"

        self.assertAlmostEqual(cache_resolver.compute_cosine_similarity(t1, t2), 1.0, places=4)
        self.assertAlmostEqual(cache_resolver.compute_cosine_similarity(t1, t3), 0.0, places=4)

    def test_cache_resolver_no_false_positive_between_distinct_exceptions(self):
        """Validates that distinct UI exceptions with shared boilerplate do not trigger false positive matches."""
        no_such = "org.openqa.selenium.NoSuchElementException: Cannot locate element at com.kms.katalon.core.webui.keyword.builtin.ClickKeyword"
        stale = "org.openqa.selenium.StaleElementReferenceException: stale element reference at com.kms.katalon.core.webui.keyword.builtin.ClickKeyword"

        sim = cache_resolver.compute_cosine_similarity(no_such, stale)
        self.assertLess(sim, 0.20, f"NoSuchElement and StaleElement must not collide on boilerplate tokens, got {sim}")

    def test_cache_resolver_negative_memory_failed_fixes(self):
        """Validates that cache_resolver records and retrieves failed bug fix attempts."""
        cache_resolver.init_db(seed=True)
        sig = "UnitTest_Custom_Exception"
        cache_resolver.record_failed_fix(
            error_signature=sig,
            attempted_patch="mock_broken_patch();",
            failure_reason="Failed validation during test execution",
            agent_role="unit-tester"
        )
        failed_list = cache_resolver.get_failed_fixes(sig)
        self.assertTrue(len(failed_list) >= 1, "Must retrieve recorded failed fix")
        self.assertEqual(failed_list[0]["attempted_patch"], "mock_broken_patch();")
        self.assertEqual(failed_list[0]["failure_reason"], "Failed validation during test execution")

    # --- FUNCTIONAL TESTS FOR INFER_LINTER ---

    def test_infer_linter_functional_detects_swallowed_exception(self):
        """Validates that infer_linter detects empty catch blocks as CRITICAL defects."""
        with tempfile.NamedTemporaryFile("w", suffix=".groovy", delete=False, encoding="utf-8") as tf:
            tf.write("""
                try {
                    LoginPage.login("admin", "123")
                } catch (Exception e) {
                    // swallowed exception!
                }
                assert true
            """)
            temp_path = tf.name

        try:
            result = infer_linter.analyze_script(temp_path)
            self.assertFalse(result["is_clean"])
            defect_types = [d["type"] for d in result["defects"]]
            self.assertIn("SWALLOWED_EXCEPTION", defect_types)
            criticals = [d for d in result["defects"] if d["severity"] == "CRITICAL"]
            self.assertTrue(len(criticals) >= 1)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_infer_linter_functional_detects_flaky_sleep(self):
        """Validates that infer_linter detects excessive Thread.sleep as WARNING."""
        with tempfile.NamedTemporaryFile("w", suffix=".groovy", delete=False, encoding="utf-8") as tf:
            tf.write("""
                LoginPage.open()
                Thread.sleep(5000)
                assert LoginPage.isLoaded()
            """)
            temp_path = tf.name

        try:
            result = infer_linter.analyze_script(temp_path)
            defect_types = [d["type"] for d in result["defects"]]
            self.assertIn("EXCESSIVE_HARD_DELAY", defect_types)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_infer_linter_functional_detects_fake_pass(self):
        """Validates that infer_linter detects actions without assertions as FAKE_PASS."""
        with tempfile.NamedTemporaryFile("w", suffix=".groovy", delete=False, encoding="utf-8") as tf:
            tf.write("""
                LoginPage.open()
                LoginPage.enterCredentials("user", "pass")
                LoginPage.clickSubmit()
                // Performs multiple interactions but contains zero verification/assertions!
            """)
            temp_path = tf.name

        try:
            result = infer_linter.analyze_script(temp_path)
            defect_types = [d["type"] for d in result["defects"]]
            self.assertIn("FAKE_PASS_NO_ASSERTION", defect_types)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_infer_linter_functional_clean_script(self):
        """Validates that a compliant test script passes cleanly."""
        with tempfile.NamedTemporaryFile("w", suffix=".groovy", delete=False, encoding="utf-8") as tf:
            tf.write("""
                LoginPage.open()
                LoginPage.login("user", "pass")
                verifyElementPresent(DashboardPage.HEADER, 10)
                assertTrue(DashboardPage.isLoaded())
            """)
            temp_path = tf.name

        try:
            result = infer_linter.analyze_script(temp_path)
            self.assertTrue(result["is_clean"], f"Compliant script should be clean, got: {result['defects']}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_infer_linter_zero_scripts_guard(self):
        """Validates that infer_linter handles an empty directory without ZeroDivisionError."""
        with tempfile.TemporaryDirectory() as empty_dir:
            ret = infer_linter.run_infer_linter(target_dir=empty_dir)
            self.assertEqual(ret, 0, "run_infer_linter on empty dir must return exit code 0")

    # --- FUNCTIONAL TESTS FOR LINT_AI_DOCS ---

    def test_lint_ai_docs_functional_on_repo(self):
        """Validates that lint_ai_docs runs without runtime crash on repo."""
        errors, warnings = lint_ai_docs.lint_docs(REPO_ROOT)
        self.assertEqual(len(errors), 0, f"Expected 0 doc lint errors on repo, got: {errors}")

    def test_lint_ai_docs_detects_hallucinated_tool(self):
        """Validates that lint_ai_docs catches references to nonexistent tools."""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, dir=REPO_ROOT, encoding="utf-8") as tf:
            tf.write("Run the tool: tools/fake_nonexistent_hallucinated_tool.py for testing.\n")
            temp_path = tf.name

        try:
            errors, _ = lint_ai_docs.lint_docs(REPO_ROOT)
            matched = any("fake_nonexistent_hallucinated_tool.py" in e for e in errors)
            self.assertTrue(matched, "lint_ai_docs must catch hallucinated tool script")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # --- FUNCTIONAL TESTS FOR DISTILL_LOG ---

    def test_distill_log_functional(self):
        """Validates that distill_log filters noise and preserves failure blocks."""
        raw_log = [
            "[INFO] Starting build task...",
            "> Task :compileJava UP-TO-DATE",
            "> Task :processResources UP-TO-DATE",
            "SLF4J: Failed to load class",
            "[DEBUG] Loading configuration profiles",
            "Starting ChromeDriver 114.0",
            "Only local connections are allowed",
            "DevTools listening on ws://127.0.0.1:9222",
            "TC-101 LoginFlow PASSED",
            "TC-102 CheckoutFlow FAILED",
            "java.lang.NullPointerException: Cannot invoke method click() on null object",
            "    at Script1680000000000.run(Script1680000000000.groovy:42)",
            "    at com.kms.katalon.core.main.ScriptEngine.run(ScriptEngine.java:194)",
            "[INFO] Test execution finished."
        ]
        noisy_text = "\n".join(raw_log * 10)  # 140 lines of noise
        distilled = distill_log.distill(noisy_text)

        self.assertIn("FAILURES DETECTED", distilled)
        self.assertIn("TC-102", distilled)
        self.assertIn("NullPointerException", distilled)
        self.assertTrue(len(distilled.splitlines()) < len(noisy_text.splitlines()) * 0.5,
                        "Distilled log should compress noise by over 50%")

    # --- FUNCTIONAL TESTS FOR VERIFY_ALL GATES ---

    def test_verify_all_bom_gate_functional(self):
        """Validates Gate 1 detects UTF-8 BOM in files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bom_file = os.path.join(temp_dir, "test.md")
            with open(bom_file, "wb") as f:
                f.write(b"\xef\xbb\xbf# BOM Header\n")

            has_passed = verify_all.gate_1_bom_check(temp_dir)
            self.assertFalse(has_passed, "gate_1_bom_check must return False when BOM exists")

    def test_verify_all_gate_5_no_windows_dot_bug(self):
        """Validates Gate 5 passes and does not match '.' on Windows."""
        has_passed = verify_all.gate_5_cleanup_blacklist(REPO_ROOT)
        self.assertTrue(has_passed, "Gate 5 must pass on clean repository without matching '.'")

    def test_verify_all_gate_6_detects_credentials_functional(self):
        """Validates Gate 6 catches plaintext hardcoded passwords."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_file = os.path.join(temp_dir, "config.py")
            with open(bad_file, "w", encoding="utf-8") as f:
                f.write("password = 'Enterprise@2026'\n")  # gate6-allowlist: synthetic test fixture

            has_passed = verify_all.gate_6_credential_security(temp_dir, mode="HUB")
            self.assertFalse(has_passed, "gate_6_credential_security must fail when hardcoded password exists")

    def test_verify_all_complete_run_hub_mode(self):
        """Validates that all 7 gates pass on the QA Hub."""
        repo_root = REPO_ROOT
        gates = [
            verify_all.gate_1_bom_check,
            verify_all.gate_2_path_portability,
            verify_all.gate_3_clean_pom,
            verify_all.gate_4_ai_docs_lint,
            verify_all.gate_5_cleanup_blacklist,
            verify_all.gate_6_credential_security,
            verify_all.gate_7_infer_linter,
        ]
        for gate in gates:
            res = gate(repo_root, mode="HUB")
            self.assertTrue(res, f"Gate {gate.__name__} failed in HUB mode")

    def test_verify_all_resolve_target_repo(self):
        """Validates resolve_target_repo across explicit args, env vars, and default Hub."""
        # 1. Default to Hub when no args
        hub_resolved = verify_all.resolve_target_repo()
        self.assertEqual(hub_resolved, REPO_ROOT)

        # 2. Explicit target via cli_repo or cli_target
        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_resolved = verify_all.resolve_target_repo(cli_target=temp_dir)
            self.assertEqual(explicit_resolved, temp_dir)

            flag_resolved = verify_all.resolve_target_repo(cli_repo=temp_dir)
            self.assertEqual(flag_resolved, temp_dir)

        # 3. Non-existent path raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            verify_all.resolve_target_repo(cli_target="Z:\\NonExistent\\Path\\12345")

        # 4. Environment variable TARGET_PROJECT_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["TARGET_PROJECT_DIR"] = temp_dir
            try:
                env_resolved = verify_all.resolve_target_repo()
                self.assertEqual(env_resolved, temp_dir)
            finally:
                os.environ.pop("TARGET_PROJECT_DIR", None)

    def test_verify_all_detect_repo_mode(self):
        """Validates detect_repo_mode correctly classifies HUB vs TARGET."""
        # QA Hub must be classified as HUB
        self.assertEqual(verify_all.detect_repo_mode(REPO_ROOT), "HUB")

        # Target directory with Groovy scripts must be TARGET
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = os.path.join(temp_dir, "Scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            with open(os.path.join(scripts_dir, "TC_Test.groovy"), "w", encoding="utf-8") as f:
                f.write("LoginPage.open()\n")
            self.assertEqual(verify_all.detect_repo_mode(temp_dir), "TARGET")

        # Target directory with playwright config must be TARGET
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "playwright.config.ts"), "w", encoding="utf-8") as f:
                f.write("export default {};\n")
            self.assertEqual(verify_all.detect_repo_mode(temp_dir), "TARGET")

    def test_verify_all_complete_run_target_mode(self):
        """Validates that all gates pass on a compliant Target Project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = os.path.join(temp_dir, "Scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            # Create compliant Clean POM test script with 4 executable lines
            with open(os.path.join(scripts_dir, "TC_Smoke.groovy"), "w", encoding="utf-8") as f:
                f.write("LoginPage.navigate()\nLoginPage.submitCredentials('user')\nLoginPage.waitForToast()\nLoginPage.assertValid()\n")

            gates = [
                verify_all.gate_1_bom_check,
                verify_all.gate_2_path_portability,
                verify_all.gate_3_clean_pom,
                verify_all.gate_4_ai_docs_lint,
                verify_all.gate_5_cleanup_blacklist,
                verify_all.gate_6_credential_security,
                verify_all.gate_7_infer_linter,
            ]
            for gate in gates:
                res = gate(temp_dir, mode="TARGET")
                self.assertTrue(res, f"Gate {gate.__name__} failed in TARGET mode")

    def test_repo_map_dynamic_target(self):
        """Validates repo_map resolves target repository and indexes Page Classes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            kdir = os.path.join(temp_dir, "Keywords", "pages")
            os.makedirs(kdir)
            with open(os.path.join(kdir, "ProfilePage.groovy"), "w", encoding="utf-8") as f:
                f.write("class ProfilePage extends BasePage {\n    def updateBio(String bio) {}\n}\n")

            out_txt = os.path.join(temp_dir, "map.txt")
            out_json = os.path.join(temp_dir, "map.json")
            stats = repo_map.build_repo_map(target_repo=temp_dir, output_txt=out_txt, output_json=out_json)

            self.assertEqual(stats["classes_count"], 1)
            self.assertEqual(stats["target_repo"], temp_dir)
            self.assertTrue(os.path.exists(out_txt))
            self.assertTrue(os.path.exists(out_json))

    def test_validate_groovy_scripts_dynamic_target(self):
        """Validates validate_groovy_scripts runs on target repo without syntax errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdir = os.path.join(temp_dir, "Scripts")
            os.makedirs(sdir)
            with open(os.path.join(sdir, "TC_Valid.groovy"), "w", encoding="utf-8") as f:
                f.write("class TC_Valid { def run() { println('OK') } }\n")

            target_repo = validate_groovy_scripts.resolve_target_repo(cli_target=temp_dir)
            self.assertEqual(target_repo, Path(temp_dir).resolve())

    def test_check_env_qa_hub_and_target_resolution(self):
        """Validates check_env recognizes QA Hub structure and resolves targets."""
        # 1. QA Hub structure passes on REPO_ROOT
        hub_runner = check_env.DiagnosticRunner(target_dir=REPO_ROOT)
        hub_runner.check_project_structure()
        self.assertEqual(len(hub_runner.errors), 0, "QA Hub structure must pass on REPO_ROOT")

        # 2. Target project resolution via cli_target
        with tempfile.TemporaryDirectory() as temp_dir:
            resolved = check_env.resolve_target_repo(cli_target=temp_dir)
            self.assertEqual(resolved, Path(temp_dir).resolve())

    def test_test_impact_dynamic_target(self):
        """Validates test_impact resolve_target_repo and total count scan."""
        with tempfile.TemporaryDirectory() as temp_dir:
            resolved = test_impact.resolve_target_repo(cli_target=temp_dir)
            self.assertEqual(resolved, temp_dir)

            sdir = os.path.join(temp_dir, "Scripts")
            os.makedirs(sdir)
            with open(os.path.join(sdir, "TC_Smoke.groovy"), "w", encoding="utf-8") as f:
                f.write("// smoke\n")

            total = test_impact.get_total_test_cases(workspace_dir=temp_dir)
            self.assertEqual(total, 1)

    def test_analyze_project_suite_execution(self):
        """Validates that analyze_project runs the 5-in-1 audit on the Hub and writes markdown report."""
        code = analyze_project.run_full_analysis(REPO_ROOT)
        self.assertEqual(code, 0, "analyze_project must return 0 on clean Hub")
        report_path = os.path.join(REPO_ROOT, "reports", "PROJECT_HEALTH_REPORT.md")
        self.assertTrue(os.path.exists(report_path), "PROJECT_HEALTH_REPORT.md must be generated")

    # --- FUNCTIONAL TESTS FOR WCAG AUDIT ---

    def test_wcag_audit_functional(self):
        """Validates that wcag_audit detects accessibility violations in HTML."""
        bad_html = """
        <html>
            <body>
                <img src="logo.png">
                <button></button>
                <input type="text" name="username">
            </body>
        </html>
        """
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
            tf.write(bad_html)
            temp_path = tf.name

        try:
            auditor = wcag_audit.run_audit(temp_path)
            self.assertTrue(len(auditor.violations) >= 2, "Must detect missing alt and empty button")
            criteria = [v["criterion"] for v in auditor.violations]
            self.assertTrue(any("1.1.1" in c for c in criteria))
            self.assertTrue(any("4.1.2" in c for c in criteria))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # --- FUNCTIONAL TESTS FOR CLI DISPATCH ---

    def test_cli_version_output(self):
        """Validates that cli.cmd_version outputs the expected catalog details."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            cli.cmd_version(None)
            output = sys.stdout.getvalue()
            self.assertIn("Agent-QA Hub CLI v2.0.1", output)
            self.assertIn("27 Standardized Skills", output)
        finally:
            sys.stdout = old_stdout

    def test_flaky_detector_calculate_flakiness(self):
        """Validates that flaky_detector correctly scores flakiness tiers and quarantine flags."""
        # 1. Deterministic PASS
        res_stable = flaky_detector.calculate_flakiness([True, True, True, True, True])
        self.assertEqual(res_stable["status"], "STABLE")
        self.assertFalse(res_stable["quarantine"])
        self.assertEqual(res_stable["pass_rate"], 100.0)
        self.assertEqual(res_stable["flips"], 0)

        # 2. Intermittent Severe Flake (3 pass, 2 fail, 4 flips)
        res_severe = flaky_detector.calculate_flakiness([True, False, True, False, True])
        self.assertEqual(res_severe["status"], "SEVERE_FLAKE")
        self.assertTrue(res_severe["quarantine"])
        self.assertEqual(res_severe["flips"], 4)
        self.assertEqual(res_severe["pass_rate"], 60.0)

        # 3. Deterministic FAIL
        res_fail = flaky_detector.calculate_flakiness([False, False, False, False, False])
        self.assertEqual(res_fail["status"], "DETERMINISTIC_FAIL")
        self.assertFalse(res_fail["quarantine"])

    # --- REGRESSION TESTS FOR 7 REPORTED DEFECTS ---

    def test_browser_helpers_fetch_window_context(self):
        """Regression test 1: window.fetch hook must bind context to window to avoid Illegal invocation."""
        helper_path = os.path.join(TOOLS_DIR, "browser_helpers.js")
        with open(helper_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("origFetch.apply(window, arguments)", content)
        self.assertNotIn("origFetch.apply(this, arguments)", content)

    def test_infer_linter_no_false_positive_on_check_words(self):
        """Regression test 2: ASSERTION_PATTERN must have \\b and not match checkbox or checkout."""
        from infer_linter import ASSERTION_PATTERN
        self.assertFalse(bool(ASSERTION_PATTERN.search("WebUI.click(findTestObject('input_checkbox'))")))
        self.assertFalse(bool(ASSERTION_PATTERN.search("checkout()")))
        self.assertFalse(bool(ASSERTION_PATTERN.search("checkAvailability()")))
        self.assertFalse(bool(ASSERTION_PATTERN.search("checkbox.click()")))
        
        # Must match valid assertions
        self.assertTrue(bool(ASSERTION_PATTERN.search("assertTrue(isValid)")))
        self.assertTrue(bool(ASSERTION_PATTERN.search("assert expected == actual")))
        self.assertTrue(bool(ASSERTION_PATTERN.search("verifyElementPresent(findTestObject('btn'))")))
        self.assertTrue(bool(ASSERTION_PATTERN.search("waitForToast('Success')")))
        self.assertTrue(bool(ASSERTION_PATTERN.search("checkStatus(200)")))
        self.assertTrue(bool(ASSERTION_PATTERN.search("expect(page).toHaveTitle('Dashboard')")))

    def test_validate_groovy_scripts_strips_comments_and_regex(self):
        """Regression test 3: strip_comments_and_strings must eliminate braces in comments and regexes."""
        import validate_groovy_scripts
        from pathlib import Path
        snippet = """
        // Log success :)
        /* block comment with { unmatched brace */
        String regex = "\\\\d{1,3}";
        def match = ~/\\\\d{1,3}/;
        def run() {
            println("Test with (paren)");
        }
        """
        temp_file = Path(REPO_ROOT) / "temp_validate_test.groovy"
        try:
            temp_file.write_text(snippet, encoding="utf-8")
            errors = validate_groovy_scripts.check_file(temp_file)
            self.assertEqual(errors, [], f"Expected zero errors, got: {errors}")
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_cache_resolver_sync_db_initializes_both_schemas(self):
        """Regression test 4: sync_db must initialize schemas for both GLOBAL_DB and LOCAL_DB."""
        synced = cache_resolver.sync_db()
        self.assertIsInstance(synced, int)
        self.assertGreaterEqual(synced, 0)

    @unittest.skipUnless(HAS_PIL, "Pillow library is required for visual tests")
    def test_visual_diff_canvas_vectorized(self):
        """Regression test 5: compare_canvas_images runs fast using C-level histogram and accurate diff."""
        from PIL import Image
        import visual_diff_canvas
        im1 = Image.new("RGB", (200, 200), (255, 255, 255))
        im2 = Image.new("RGB", (200, 200), (255, 255, 255))
        for x in range(20):
            for y in range(20):
                im2.putpixel((x, y), (0, 0, 0))
        t1 = os.path.join(REPO_ROOT, "temp_canvas1.png")
        t2 = os.path.join(REPO_ROOT, "temp_canvas2.png")
        diff_out = os.path.join(REPO_ROOT, "temp_diff.png")
        try:
            im1.save(t1)
            im2.save(t2)
            is_match, ratio, count = visual_diff_canvas.compare_canvas_images(t1, t2, diff_out, threshold=0.005)
            self.assertFalse(is_match)
            self.assertEqual(count, 400)
            self.assertAlmostEqual(ratio, 400 / 40000, places=4)
            self.assertTrue(os.path.exists(diff_out))
        finally:
            for p in [t1, t2, diff_out]:
                if os.path.exists(p):
                    os.remove(p)

    def test_check_env_ssl_unverified(self):
        """Regression test 6: check_env.py must use unverified SSL context and have UTF-8 stdout configured."""
        env_tool = os.path.join(TOOLS_DIR, "check_env.py")
        with open(env_tool, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("ssl.CERT_NONE", code)
        self.assertIn("sys.stdout.reconfigure", code)

    def test_package_dist_includes_docs_scripts_templates(self):
        """Regression test 7: docs/, scripts/, and templates/ must exist and be included in agent-skills.zip."""
        import zipfile
        zip_path = os.path.join(REPO_ROOT, "agent-skills.zip")
        created_by_test = False
        if not os.path.exists(zip_path) or not zipfile.is_zipfile(zip_path):
            package_script = os.path.join(REPO_ROOT, "scripts", "package_dist.py")
            subprocess.run([sys.executable, package_script], check=True, cwd=REPO_ROOT, stdout=subprocess.DEVNULL)
            created_by_test = True
        try:
            self.assertTrue(os.path.exists(zip_path), "agent-skills.zip must exist")
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = set(zf.namelist())
                self.assertIn("docs/ARCHITECTURE.md", names)
                self.assertIn("docs/CLI_REFERENCE.md", names)
                self.assertIn("scripts/install.ps1", names)
                self.assertIn("scripts/setup.sh", names)
                self.assertIn("templates/PROJECT_AI_GUIDE_TEMPLATE.md", names)
                self.assertIn("package.json", names)
                self.assertIn("bin/agent-qa.js", names)
        finally:
            if created_by_test and os.path.exists(zip_path):
                os.remove(zip_path)

    def test_lookup_tc_multi_tier_resolution(self):
        """Validates that lookup_tc.py supports CLI --file and TC_DATA_FILE environment variable."""
        import lookup_tc
        sample_tc = [{"ID": "TC-999", "Name": "Test Login Boundary", "Expected": "Pass", "Steps": "1. Open"}]
        temp_tc_file = os.path.join(REPO_ROOT, "temp_tc_test.json")
        with open(temp_tc_file, "w", encoding="utf-8") as f:
            json.dump(sample_tc, f)

        try:
            # 1. Test CLI file resolution
            p1 = lookup_tc.resolve_json_path(cli_file=temp_tc_file)
            self.assertEqual(os.path.abspath(temp_tc_file), p1)

            # 2. Test ENV var resolution
            os.environ["TC_DATA_FILE"] = temp_tc_file
            p2 = lookup_tc.resolve_json_path()
            self.assertEqual(os.path.abspath(temp_tc_file), p2)
        finally:
            if "TC_DATA_FILE" in os.environ:
                del os.environ["TC_DATA_FILE"]
            if os.path.exists(temp_tc_file):
                os.remove(temp_tc_file)

    def test_lookup_xpath_multi_tier_resolution(self):
        """Validates that lookup_xpath.py supports CLI --file and XPATH_DATA_FILE environment variable."""
        import lookup_xpath
        sample_xp = {"LoginPage": [{"constant": "TXT_USER", "xpath": "//input[@id='user']", "tag": "input"}]}
        temp_xp_file = os.path.join(REPO_ROOT, "temp_xp_test.json")
        with open(temp_xp_file, "w", encoding="utf-8") as f:
            json.dump(sample_xp, f)

        try:
            # 1. Test CLI file resolution
            p1 = lookup_xpath.resolve_json_path(cli_file=temp_xp_file)
            self.assertEqual(os.path.abspath(temp_xp_file), p1)

            # 2. Test ENV var resolution
            os.environ["XPATH_DATA_FILE"] = temp_xp_file
            p2 = lookup_xpath.resolve_json_path()
            self.assertEqual(os.path.abspath(temp_xp_file), p2)
        finally:
            if "XPATH_DATA_FILE" in os.environ:
                del os.environ["XPATH_DATA_FILE"]
            if os.path.exists(temp_xp_file):
                os.remove(temp_xp_file)

    def test_setup_project_detect_stack_and_bootstrap(self):
        """Validates that setup_project detects project tech stack and generates tailored PROJECT_AI_GUIDE.md."""
        import setup_project
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Create a dummy Playwright project marker
            with open(os.path.join(temp_dir, "playwright.config.ts"), "w", encoding="utf-8") as f:
                f.write("// config\n")

            stack = setup_project.detect_tech_stack(temp_dir)
            self.assertEqual(stack["framework"], "Playwright Test")
            self.assertEqual(stack["language"], "TypeScript")

            # 2. Run ensure_project_ai_guide
            created = setup_project.ensure_project_ai_guide(temp_dir, stack)
            self.assertTrue(created)
            guide_path = os.path.join(temp_dir, "PROJECT_AI_GUIDE.md")
            self.assertTrue(os.path.exists(guide_path))
            with open(guide_path, "r", encoding="utf-8") as gf:
                content = gf.read()
            self.assertIn("Playwright Test", content)

    def test_setup_project_install_git_hook(self):
        """Validates that setup_project installs the pre-push hook into .git/hooks."""
        import setup_project
        with tempfile.TemporaryDirectory() as temp_dir:
            git_hooks = os.path.join(temp_dir, ".git", "hooks")
            os.makedirs(git_hooks)
            installed = setup_project.install_git_pre_push_hook(temp_dir)
            self.assertTrue(installed)
            hook_file = os.path.join(git_hooks, "pre-push")
            self.assertTrue(os.path.exists(hook_file))
            with open(hook_file, "r", encoding="utf-8") as hf:
                content = hf.read()
            self.assertIn("AI-GUARD", content)
            self.assertIn("verify_all.py", content)

    def test_project_state_rolling_window_cap(self):
        """Validates that project_state enforces strict rolling window and caps size under 50 lines."""
        import project_state
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = project_state.init_state(temp_dir, goal="Test Goal")
            self.assertTrue(os.path.exists(state_file))

            # Add 15 tasks to trigger rolling buffer pruning
            for i in range(15):
                project_state.update_state(temp_dir, completed_task=f"Task {i}")

            with open(state_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Must be strictly capped under 50 lines (~200 tokens)
            self.assertLess(len(lines), 50, f"State file must stay under 50 lines, got {len(lines)}")
            content = "".join(lines)
            self.assertIn("Task 14", content, "Latest task must be present")
            self.assertNotIn("Task 0", content, "Oldest task must be pruned by rolling window")

    def test_auto_heal_diagnose_plan(self):
        """Validates that auto_heal parses failure and returns a structured plan."""
        import auto_heal
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = auto_heal.diagnose_and_plan_heal(temp_dir)
            self.assertIn("status", plan)

    def test_safety_firewall_interception_and_bypass(self):
        """Validates that safety_firewall detects destructive actions and respects bypass."""
        import safety_firewall
        # 1. Dangerous action
        d1, r1 = safety_firewall.is_action_dangerous("click", text="Delete All Invoices")
        self.assertTrue(d1)
        self.assertIn("delete", r1.lower())

        # 2. Selector with dangerous pattern
        d2, _ = safety_firewall.is_action_dangerous("click", selector="button.btn-danger")
        self.assertTrue(d2)

        # 3. Safe action
        d3, _ = safety_firewall.is_action_dangerous("click", text="Save Changes", selector="button.p-button-primary")
        self.assertFalse(d3)

        # 4. Authorization check without force
        res_blocked = safety_firewall.inspect_and_authorize("click", text="Drop Database", force=False)
        self.assertFalse(res_blocked["authorized"])

        # 5. Authorization check with force
        res_forced = safety_firewall.inspect_and_authorize("click", text="Drop Database", force=True)
        self.assertTrue(res_forced["authorized"])
        self.assertTrue(res_forced["bypass_granted"])

    def test_api_drift_sentinel_breaking_changes(self):
        """Validates that api_drift_sentinel detects removed endpoints and newly required params."""
        import api_drift_sentinel
        old_spec = {
            "paths": {
                "/users": {
                    "get": {
                        "parameters": [{"name": "limit", "in": "query", "required": False, "type": "integer"}]
                    },
                    "delete": {}
                }
            }
        }
        # New spec removes DELETE /users and changes limit to required
        new_spec = {
            "paths": {
                "/users": {
                    "get": {
                        "parameters": [{"name": "limit", "in": "query", "required": True, "type": "integer"}]
                    }
                },
                "/orders": {
                    "get": {}
                }
            }
        }

        diff = api_drift_sentinel.compare_specs(old_spec, new_spec)
        self.assertFalse(diff["is_backward_compatible"])
        self.assertGreaterEqual(diff["breaking_changes_count"], 2)
        types = [b["type"] for b in diff["breaking_changes"]]
        self.assertIn("REMOVED_HTTP_METHOD", types)
        self.assertIn("PARAM_NOW_REQUIRED", types)
        self.assertEqual(diff["additions_count"], 1)

    def test_mcp_server_protocol_exchange(self):
        """Validates that mcp_server handles initialize, tools/list, and tools/call via JSON-RPC."""
        import mcp_server
        # 1. Initialize
        init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        init_resp = mcp_server.process_message(init_req)
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "enterprise-agent-qa")

        # 2. Tools list
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        list_resp = mcp_server.process_message(list_req)
        tools = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertIn("verify_all_gates", tools)
        self.assertIn("check_action_safety", tools)
        self.assertIn("check_contract_drift", tools)

        # 3. Tools call
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "check_action_safety",
                "arguments": {
                    "action_type": "click",
                    "element_text": "Submit Form"
                }
            }
        }
        call_resp = mcp_server.process_message(call_req)
        self.assertFalse(call_resp["result"]["isError"])
        content_text = call_resp["result"]["content"][0]["text"]
        data = json.loads(content_text)
        self.assertTrue(data["authorized"])
        self.assertFalse(data["dangerous"])

    def test_micro_mutator_generates_mutants(self):
        """Validates that micro_mutator creates atomic syntactic mutations on logic expressions."""
        import micro_mutator
        sample_code = """
        def verifyEligibility(int age, boolean active) {
            if (age >= 18 && active == true) {
                return true
            }
            return false
        }
        """
        mutants = micro_mutator.generate_mutants_for_code(sample_code, file_path="sample.groovy")
        self.assertGreaterEqual(len(mutants), 3)
        descriptions = [m["description"] for m in mutants]
        self.assertTrue(any("Relational Inversion" in d or "Boundary Shift" in d for d in descriptions))
        self.assertTrue(any("Equality Inversion" in d for d in descriptions))
        self.assertTrue(any("Boolean Inversion" in d for d in descriptions))

    def test_heal_pr_automator_confidence_and_draft(self):
        """Validates that heal_pr_automator calculates weighted confidence and drafts PR markdown."""
        import heal_pr_automator
        # 1. High confidence (>= 90%)
        conf_high = heal_pr_automator.calculate_healing_confidence(aom_score=0.95, spatial_score=0.90, visual_score=0.92)
        self.assertTrue(conf_high["qualified_for_pr"])
        self.assertEqual(conf_high["risk_tier"], "LOW_RISK")
        self.assertGreaterEqual(conf_high["confidence_percentage"], 90.0)

        pr = heal_pr_automator.generate_pr_draft(
            page_file="Keywords/pages/LoginPage.groovy",
            old_locator="//button[@id='submit']",
            new_locator="//button[@name='login_btn']",
            confidence_info=conf_high
        )
        self.assertTrue(pr["branch_name"].startswith("heal/loginpage_"))
        self.assertIn("Automated Self-Healing Verification PR", pr["pr_body"])
        self.assertIn("AOM", pr["pr_body"])

        # 2. Low confidence (< 90%)
        conf_low = heal_pr_automator.calculate_healing_confidence(aom_score=0.60, spatial_score=0.50, visual_score=0.40)
        self.assertFalse(conf_low["qualified_for_pr"])
        self.assertEqual(conf_low["risk_tier"], "HIGH_RISK")

    def test_matrix_sharder_bin_packing(self):
        """Validates that matrix_sharder distributes tests across N shards using LPT."""
        import matrix_sharder
        test_files = [f"Scripts/TC_{i}.groovy" for i in range(10)]
        with tempfile.TemporaryDirectory() as temp_dir:
            shards = matrix_sharder.shard_tests_lpt(test_files, temp_dir, num_shards=3)
            self.assertEqual(len(shards), 3)
            total_assigned = sum(len(s["tests"]) for s in shards)
            self.assertEqual(total_assigned, 10)
            for s in shards:
                self.assertGreater(len(s["tests"]), 0)

    def test_safety_firewall_code_snippet_and_dry_run(self):
        """Validates that safety_firewall parses code snippets and dry-run validates actions."""
        import safety_firewall
        code_dangerous = "page.click('button.btn-danger'); page.fill('#user', 'admin');"
        inspections = safety_firewall.inspect_code_snippet(code_dangerous, force=False)
        self.assertGreaterEqual(len(inspections), 2)
        has_blocked = any(not item["authorized"] for item in inspections)
        self.assertTrue(has_blocked)

        code_safe = "page.click('#submit-btn'); page.fill('#user', 'admin');"
        inspections_safe = safety_firewall.inspect_code_snippet(code_safe, force=False)
        all_safe = all(item["authorized"] for item in inspections_safe)
        self.assertTrue(all_safe)

    def test_micro_mutator_scoring_and_gatekeeper_rejection(self):
        """Validates that micro_mutator scores tests and rejects fake-pass tautologies (< 80%)."""
        import micro_mutator
        # 1. Fake pass with zero assertions -> Score = 0%
        fake_pass_code = """
        def testLogin() {
            int status = 200
            if (status == 200) {
                print("Logged in")
            }
        }
        """
        mutants_fake = micro_mutator.generate_mutants_for_code(fake_pass_code, "fake.groovy")
        eval_fake, score_fake = micro_mutator.evaluate_mutants_statically(fake_pass_code, mutants_fake)
        self.assertEqual(score_fake, 0.0)
        self.assertLess(score_fake, 80.0)

        # 2. Robust test with assertions -> Score >= 80%
        robust_code = """
        def testLogin() {
            int status = 200
            assert status == 200
        }
        """
        mutants_robust = micro_mutator.generate_mutants_for_code(robust_code, "robust.groovy")
        eval_robust, score_robust = micro_mutator.evaluate_mutants_statically(robust_code, mutants_robust)
        self.assertGreaterEqual(score_robust, 80.0)

    def test_qa_eval_benchmark_evaluator(self):
        """Validates that the QA benchmark evaluator loads challenges and executes resolution."""
        sys.path.insert(0, os.path.join(REPO_ROOT, "benchmarks", "qa_eval"))
        try:
            import eval_runner
            evaluator = eval_runner.BenchmarkEvaluator()
            challenges = evaluator.load_challenges(category_filter="locator_drift")
            self.assertGreaterEqual(len(challenges), 5)
            summary = evaluator.run_all(category_filter="locator_drift")
            self.assertEqual(summary["resolution_rate_pct"], 100.0)
            self.assertGreater(summary["avg_mutation_score"], 0)
        finally:
            if os.path.join(REPO_ROOT, "benchmarks", "qa_eval") in sys.path:
                sys.path.remove(os.path.join(REPO_ROOT, "benchmarks", "qa_eval"))

    def test_tms_sync_bridge_pull_and_report_bug(self):
        """Validates that tms_sync_bridge pulls acceptance criteria and creates defect tickets."""
        import tms_sync_bridge
        bridge = tms_sync_bridge.TMSBridge()

        # 1. Pull Story
        story = bridge.pull_story_acceptance_criteria("PROJ-1042")
        self.assertEqual(story["issue_key"], "PROJ-1042")
        self.assertGreaterEqual(len(story["acceptance_criteria"]), 3)
        self.assertTrue(any("Given" in ac for ac in story["acceptance_criteria"]))

        # 2. Report Bug Ticket
        bug = bridge.report_defect(
            project_key="BILLING",
            test_case_id="TC-INV-99",
            summary="Invoice total mismatch",
            error_message="AssertionError: Expected 1000 but got 950",
            screenshot_path="Screenshots/FAILED_TC-INV-99.png"
        )
        self.assertTrue(bug["ticket_key"].startswith("BILLING-BUG-"))
        self.assertEqual(bug["test_case_id"], "TC-INV-99")
        self.assertIn("AssertionError", bug["error_message"])
        self.assertEqual(bug["status"], "Created")

        # 3. Sync Execution Results
        sync = bridge.sync_execution_results("PLAN-10", [
            {"tc_id": "TC-1", "status": "PASS"},
            {"tc_id": "TC-2", "status": "FAIL"}
        ])
        self.assertEqual(sync["total_synced"], 2)
        self.assertEqual(sync["passed"], 1)
        self.assertEqual(sync["failed"], 1)
        self.assertEqual(sync["pass_rate_pct"], 50.0)

    def test_db_sandbox_snapshot_restore_and_savepoint(self):
        """Validates that db_sandbox provides instant snapshots, restores, and transaction rollback."""
        import db_sandbox
        import sqlite3
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            test_db = os.path.join(temp_dir, "test_app.db")
            sandbox = db_sandbox.DBSandbox(db_type="sqlite", db_path=test_db, snapshot_dir=temp_dir)

            # 1. Snapshot baseline
            snap_meta = sandbox.create_snapshot("baseline_01")
            self.assertEqual(snap_meta["status"], "READY")
            self.assertTrue(os.path.exists(snap_meta["snapshot_path"]))

            # 2. Mutate DB with test junk
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (code, status) VALUES ('AUTO_DIRTY_01', 'DIRTY')")
            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM users")
            count_dirty = cursor.fetchone()[0]
            conn.close()
            self.assertEqual(count_dirty, 1)

            # 3. Restore snapshot (Zero-Pollution)
            rest_meta = sandbox.restore_snapshot("baseline_01")
            self.assertEqual(rest_meta["status"], "RESTORED")
            self.assertTrue(rest_meta["zero_pollution_guaranteed"])

            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count_clean = cursor.fetchone()[0]
            conn.close()
            self.assertEqual(count_clean, 0)

            # 4. Savepoint Rollback
            res_sp = sandbox.execute_with_savepoint([
                "INSERT INTO users (code, status) VALUES ('TEMP_TX_01', 'ACTIVE');"
            ])
            self.assertEqual(res_sp["status"], "SUCCESS")
            self.assertEqual(res_sp["count_inside_transaction"], 1)
            self.assertEqual(res_sp["count_after_rollback"], 0)
            self.assertTrue(res_sp["zero_pollution_verified"])

            # 5. Audit & Purge
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (code, status) VALUES ('AUTO_LEAK_01', 'LEAKED')")
            conn.commit()
            conn.close()

            audit_res = sandbox.audit_and_purge_pollution()
            self.assertEqual(audit_res["total_purged_rows"], 1)
            self.assertTrue(audit_res["zero_pollution_achieved"])

    def test_traffic_session_converter_har_to_playwright(self):
        """Validates that traffic_session_converter filters noise, redacts PII, and generates Playwright tests."""
        import traffic_session_converter
        converter = traffic_session_converter.TrafficConverter(sanitize_pii=True)

        har_data = {
            "log": {
                "entries": [
                    {
                        "request": {"method": "GET", "url": "https://app.test.local/login", "headers": []},
                        "response": {"status": 200}
                    },
                    {
                        "request": {"method": "GET", "url": "https://app.test.local/logo.png", "headers": []},
                        "response": {"status": 200}
                    },
                    {
                        "request": {
                            "method": "POST",
                            "url": "https://app.test.local/api/pay",
                            "headers": [{"name": "Authorization", "value": "Bearer secret_123"}],
                            "postData": {"text": json.dumps({"card": "4111111111111111", "cvv": "123", "password": "pass"})}
                        },
                        "response": {"status": 201}
                    }
                ]
            }
        }

        requests = converter.parse_har(har_data)
        # Static asset logo.png must be filtered out
        self.assertEqual(len(requests), 2)
        urls = [r["url"] for r in requests]
        self.assertNotIn("https://app.test.local/logo.png", urls)

        # Post data must have PII sanitized
        post_req = next(r for r in requests if r["method"] == "POST")
        self.assertNotIn("secret_123", str(post_req["headers"]))
        self.assertIn("REDACTED", str(post_req["headers"]))
        self.assertIn("REDACTED_SECRET", post_req["request_body"])
        self.assertIn("999", post_req["request_body"])

        # Playwright code generation
        code = converter.generate_playwright_test(requests, test_name="PaymentReplay")
        self.assertIn("test.describe('PaymentReplay'", code)
        self.assertIn("await request.post('https://app.test.local/api/pay'", code)
        self.assertIn("expect(resp2.status()).toBe(201)", code)

    @unittest.skipUnless(HAS_PIL, "Pillow library is required for visual tests")
    def test_visual_som_helper_bounding_and_coordinate_grounding(self):
        """Validates that visual_som_helper overlays marks and resolves physical coordinates."""
        import visual_som_helper
        with tempfile.TemporaryDirectory() as temp_dir:
            img_path = os.path.join(temp_dir, "dashboard.png")
            helper = visual_som_helper.VisualSoMHelper()

            elements = [
                {"x": 100, "y": 200, "width": 80, "height": 40, "label": "Zoom In"},
                {"x": 300, "y": 200, "width": 120, "height": 50, "label": "Execute Trade"}
            ]

            marked_path, marks_map = helper.generate_som_overlay(img_path, elements)
            self.assertTrue(os.path.exists(marked_path))
            self.assertEqual(len(marks_map), 2)

            # Resolve Mark #2
            mark_2 = helper.resolve_mark_coordinates(marks_map, target_mark_id=2)
            self.assertIsNotNone(mark_2)
            self.assertEqual(mark_2["center_x"], 360)
            self.assertEqual(mark_2["center_y"], 225)
            self.assertIn("await page.mouse.click(360, 225);", mark_2["playwright_action"])

            # Resolve by fuzzy label
            resolved_label = helper.resolve_mark_coordinates(marks_map, target_label="Zoom")
            self.assertIsNotNone(resolved_label)
            self.assertEqual(resolved_label["mark_id"], 1)

            # Vision Prompt Format
            prompt = helper.format_vision_prompt(marks_map, goal="Click on Execute Trade")
            self.assertIn("GOAL: Click on Execute Trade", prompt)
            self.assertIn("CLICK_MARK:", prompt)

    @unittest.skipUnless(HAS_PIL, "Pillow library is required for visual tests")
    def test_visual_som_helper_visual_caching(self):
        """Validates that visual_som_helper caches visual hashes and coordinates in SQLite."""
        import visual_som_helper
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_cache.db")
            img_path = os.path.join(temp_dir, "order_chart.png")

            img = Image.new("RGB", (400, 300), color="#1E1E2E")
            draw = ImageDraw.Draw(img)
            draw.rectangle([100, 100, 200, 150], fill="#00FF66")
            draw.text((110, 115), "Submit", fill="#000000")
            img.save(img_path)

            helper = visual_som_helper.VisualSoMHelper(db_path=db_path)

            # 1. Save to cache
            h = helper.save_cached_coordinates("TradingView Submit", img_path, center_x=150, center_y=125)
            self.assertEqual(len(h), 64)

            # 2. Lookup exact match (> 98%)
            hit = helper.lookup_cached_coordinates("TradingView Submit", img_path, threshold=0.98)
            self.assertIsNotNone(hit)
            self.assertEqual(hit["center_x"], 150)
            self.assertEqual(hit["center_y"], 125)
            self.assertGreaterEqual(hit["visual_similarity"], 0.98)
            self.assertTrue(hit["cached"])
            self.assertIn("await page.mouse.click(150, 125);", hit["playwright_action"])

            # 3. Lookup miss on un-cached component
            miss = helper.lookup_cached_coordinates("Unknown Component", img_path)
            self.assertIsNone(miss)

    def test_heal_pr_automator_with_trace_and_visual_evidence(self):
        """Validates that heal_pr_automator embeds Playwright trace and visual diff proof."""
        import heal_pr_automator
        conf = heal_pr_automator.calculate_healing_confidence(0.95, 0.90, 0.92)
        pr = heal_pr_automator.generate_pr_draft(
            page_file="Keywords/pages/OrderPage.groovy",
            old_locator="//button[@id='submit']",
            new_locator="//button[@name='confirm']",
            confidence_info=conf,
            trace_zip="Reports/traces/trace-TC101.zip",
            before_img="Screenshots/FAILED_TC101.png",
            after_img="Screenshots/PASSED_TC101.png",
            diff_img="Screenshots/DIFF_TC101.png"
        )
        self.assertIn("Playwright Trace & Visual Inspection Evidence", pr["pr_body"])
        self.assertIn("Reports/traces/trace-TC101.zip", pr["pr_body"])
        self.assertIn("npx playwright show-trace", pr["pr_body"])
        self.assertIn("Screenshots/FAILED_TC101.png", pr["pr_body"])
        self.assertIn("Screenshots/PASSED_TC101.png", pr["pr_body"])
        self.assertIn("Screenshots/DIFF_TC101.png", pr["pr_body"])

    def test_fuzz_payloads_catalog_and_scenarios(self):
        """Validates that fuzz_payloads provides comprehensive boundary sanitization vectors."""
        import fuzz_payloads
        catalog = fuzz_payloads.get_fuzz_payloads()
        self.assertIn("sqli_polyglots", catalog)
        self.assertIn("unicode_bidi_rtl", catalog)
        self.assertIn("emoji_surrogates", catalog)
        self.assertIn("extreme_length", catalog)
        self.assertIn("numeric_boundaries", catalog)

        # Scenarios for string field
        scenarios = fuzz_payloads.get_field_fuzz_scenarios("contractCode", "string")
        sc_names = [s["scenario"] for s in scenarios]
        self.assertTrue(any("SQLi" in name for name in sc_names))
        self.assertTrue(any("Unicode BiDi" in name for name in sc_names))
        self.assertTrue(any("Emoji" in name for name in sc_names))
        self.assertTrue(any("10^4" in name for name in sc_names))

    def test_generate_api_matrix_with_fuzzing(self):
        """Validates that generate_api_matrix outputs edge-case fuzzing scenarios."""
        import generate_api_matrix
        spec = {
            "paths": {
                "/api/v1/orders": {
                    "post": {
                        "summary": "Create Order",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["orderId"],
                                        "properties": {
                                            "orderId": {"type": "string", "minLength": 5, "maxLength": 30}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        matrix = generate_api_matrix.parse_spec(spec)
        descriptions = [tc["description"] for tc in matrix]
        self.assertTrue(any("SQLi Polyglot" in d for d in descriptions))
        self.assertTrue(any("Unicode BiDi RTL" in d for d in descriptions))
        self.assertTrue(any("Emoji Surrogate" in d for d in descriptions))
        self.assertTrue(any("10^4 Chars" in d for d in descriptions))


if __name__ == "__main__":
    unittest.main()
