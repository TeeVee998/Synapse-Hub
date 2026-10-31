#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Thế Vị (@TeeVee998). All rights reserved.
# SPDX-License-Identifier: MIT
# Project: Synapse-Hub (https://github.com/TeeVee998/Synapse-Hub)

"""
Enterprise Agent-QA CLI Entrypoint
----------------------------------
Provides a centralized command-line interface for the agent-skills ecosystem.
Dispatches commands to underlying specialized tools in tools/.
"""

import os
import sys
import argparse

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, SCRIPT_DIR)


def cmd_version(args):
    manifest_path = os.path.join(REPO_ROOT, "skills_manifest.json")
    version = "2.3.0"
    if os.path.exists(manifest_path):
        try:
            import json
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("version", version)
        except Exception:
            pass
    print(f"Agent-QA Hub CLI v{version}")
    manifest_skills = 28
    if os.path.exists(manifest_path):
        try:
            import json
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_skills = json.load(f).get("totalSkills", 28)
        except Exception:
            pass
    print(f"Catalog: {manifest_skills} Standardized Skills | 6 Subagent Swarm Profiles")
    print("Created by: Thế Vị (@TeeVee998) <https://github.com/TeeVee998/Synapse-Hub>")
    print("License   : MIT (Attribution Required)")


def cmd_verify_author(args):
    from author_integrity import verify_author_attribution, get_canonical_watermark, enforce_author_attribution
    valid, violations = verify_author_attribution()
    if valid:
        print(f"✅ Author attribution & provenance verified: {get_canonical_watermark()}")
        sys.exit(0)
    else:
        enforce_author_attribution(strict=True)


def cmd_verify(args):
    from verify_all import main as verify_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(verify_main())


def cmd_lint(args):
    from infer_linter import main as lint_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(lint_main())


def cmd_heal(args):
    from cache_resolver import main as heal_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(heal_main())


def cmd_distill(args):
    from distill_log import main as distill_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(distill_main())


def cmd_impact(args):
    from test_impact import main as impact_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(impact_main())


def cmd_clean(args):
    """Cleans temporary build files, __pycache__, and compiled bytecode across the repository."""
    import shutil
    removed_count = 0
    print("🧹 Cleaning temporary build artifacts and bytecode caches...")
    for root, dirs, files in os.walk(REPO_ROOT):
        for d in list(dirs):
            if d == "__pycache__":
                full_dir = os.path.join(root, d)
                try:
                    shutil.rmtree(full_dir)
                    removed_count += 1
                    dirs.remove(d)
                except Exception as e:
                    print(f"⚠️  Could not remove {full_dir}: {e}")
        for f in files:
            if f.endswith((".pyc", ".pyo", ".tmp")):
                try:
                    os.remove(os.path.join(root, f))
                    removed_count += 1
                except Exception:
                    pass
    print(f"✅ Cleanup finished: {removed_count} build artifacts and caches removed.")


def cmd_flaky(args):
    from flaky_detector import main as flaky_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(flaky_main())


def cmd_canary(args):
    from agent_canary import main as canary_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(canary_main())


def cmd_analyze(args):
    from analyze_project import main as analyze_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(analyze_main())


def cmd_setup(args):
    from setup_project import main as setup_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(setup_main())


def cmd_auto_heal(args):
    from auto_heal import main as auto_heal_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(auto_heal_main())


def cmd_safety_check(args):
    from safety_firewall import main as safety_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(safety_main())


def cmd_contract_drift(args):
    from api_drift_sentinel import main as drift_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(drift_main())


def cmd_mcp_serve(args):
    from mcp_server import run_stdio_server
    run_stdio_server()


def cmd_mutate(args):
    from micro_mutator import main as mut_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(mut_main())


def cmd_heal_pr(args):
    from heal_pr_automator import main as pr_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(pr_main())


def cmd_shard(args):
    from matrix_sharder import main as shard_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(shard_main())


def cmd_transpile(args):
    from omni_transpiler import transpile_file
    res = transpile_file(args.source, args.to, args.out)
    print(f"✅ Transpiled '{args.source}' -> {args.to} ({len(res)} files):")
    for p, code in res.items():
        print(f"  • {p} ({len(code.splitlines())} lines)")
        if not args.out:
            print("---")
            print(code)
            print("---")


def cmd_omni_scan(args):
    from omni_transpiler import scan_repository
    inv = scan_repository(args.path)
    import json
    if getattr(args, "json", False):
        print(json.dumps(inv, indent=2))
    else:
        print("======================================================================")
        print("  OMNI-AUTOMATION POLYGLOT REPOSITORY INVENTORY (0-TOKEN AST SCAN)")
        print("======================================================================")
        print(f"📁 Target Directory   : {inv['repository']}")
        print(f"📄 Scanned Files      : {inv['total_files_scanned']}")
        print(f"🌐 Languages Detected : {inv['languages']}")
        print(f"⚡ Frameworks         : {inv['frameworks']}")
        print(f"🏛️ Page Classes Found : {len(inv['pages'])}")
        print(f"🎯 Total Locators     : {inv['total_locators']}")
        print(f"⚙️ Action Methods     : {inv['total_methods']}")
        print(f"🧪 Test Cases Found   : {len(inv['test_cases'])}")
        print("======================================================================")


def cmd_report_bug(args):
    from bug_reporter import main as bug_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(bug_main())


def cmd_mock_shield(args):
    from network_mock_shield import main as mock_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(mock_main())


def cmd_visual_mask(args):
    from smart_visual_masker import main as mask_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(mask_main())


def cmd_ci_hook(args):
    from ci_healing_hook import main as hook_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(hook_main())


def cmd_migrate(args):
    """Migrates an entire legacy test suite (Katalon, Cypress, Selenium) to modern target (Playwright TS)."""
    from omni_transpiler import transpile_file
    src = getattr(args, "src", None)
    dest = getattr(args, "dest", None) or "playwright_suite"
    target = getattr(args, "target", "playwright-ts")
    if not src:
        print("❌ Error: --src parameter is required for migrate.")
        sys.exit(1)

    if os.path.isdir(src):
        migrated_count = 0
        test_exts = {".groovy", ".java", ".js", ".ts", ".py"}
        for root, _, files in os.walk(src):
            for f in files:
                if os.path.splitext(f)[1].lower() in test_exts:
                    file_path = os.path.join(root, f)
                    try:
                        transpile_file(file_path, target, output_dir=dest, hermetic=True)
                        migrated_count += 1
                    except Exception:
                        pass
        print(f"✅ [MIGRATION COMPLETE] {migrated_count} test files converted to {target} in '{dest}'.")
    else:
        transpile_file(src, target, output_dir=dest, hermetic=True)
        print(f"✅ [MIGRATION COMPLETE] '{src}' -> {target} in '{dest}'.")


def cmd_decouple_config(args):
    from config_decoupler import main as decouple_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(decouple_main())


def cmd_fuzz_api(args):
    from api_fuzzer import main as fuzz_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(fuzz_main())


def cmd_som(args):
    from visual_som_helper import main as som_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(som_main())


def cmd_gherkin(args):
    from gherkin_suite import main as gherkin_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(gherkin_main())


def cmd_export_postman(args):
    from export_postman_collection import main as postman_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(postman_main())


def cmd_generate_jmx(args):
    from generate_jmx_plan import main as jmx_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(jmx_main())


def cmd_skillspector(args):
    from skillspector import main as skillspector_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(skillspector_main())


def cmd_analyze_jtl(args):
    from jtl_analyzer import main as jtl_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(jtl_main())


def cmd_export_excel(args):
    from md_to_xlsx import main as excel_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(excel_main())


def cmd_correlate_telemetry(args):
    from telemetry_correlator import main as telem_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(telem_main())


def cmd_analyze_newman(args):
    from newman_analyzer import main as newman_main
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    sys.exit(newman_main())


def cmd_update(args):
    import update_sentinel
    if getattr(args, "check", False):
        has_update, cur, rem = update_sentinel.check_for_updates(force=True, notify=False)
        print(f"Current Hub Version : v{cur}")
        print(f"Latest Upstream     : v{rem if rem else 'Unknown'}")
        if has_update:
            print(f"⚠️ An update is available: v{cur} -> v{rem}. Run 'agent-qa update' to upgrade.")
            sys.exit(1)
        else:
            print("✅ Synapse-Hub is up to date.")
            sys.exit(0)
    update_sentinel.perform_update()


def cmd_tokens(args):
    import count_tokens
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    count_tokens.main()


def cmd_dashboard(args):
    import dashboard_generator
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    dashboard_generator.main()


def cmd_watch(args):
    import watch_mode
    sys.argv = [sys.argv[0]] + (sys.argv[2:] if len(sys.argv) > 2 else [])
    watch_mode.main()


def _hub_version():
    manifest_path = os.path.join(REPO_ROOT, "skills_manifest.json")
    version = "2.3.0"
    if os.path.exists(manifest_path):
        try:
            import json
            with open(manifest_path, "r", encoding="utf-8") as f:
                version = json.load(f).get("version", version)
        except Exception:
            pass
    return version


def main():
    parser = argparse.ArgumentParser(
        prog="agent-qa",
        description="Enterprise AI Agent Quality Engineering & Test Automation Hub CLI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Agent-QA Hub CLI v{_hub_version()}"
    )
    parser.add_argument(
        "--offline", "--offline-deterministic",
        action="store_true",
        dest="offline",
        help="Force 100%% offline air-gapped deterministic mode (zero external network / LLM API calls)"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # version
    p_ver = subparsers.add_parser("version", help="Show Hub version and catalog metadata")
    p_ver.set_defaults(func=cmd_version)

    # setup
    p_setup = subparsers.add_parser("setup", help="Autonomous 1-click bootstrap of target project (AI guide, Git hook, AST map)")
    p_setup.set_defaults(func=cmd_setup)

    # auto-heal
    p_auto_heal = subparsers.add_parser("auto-heal", help="Autonomous closed-loop test failure diagnosis and healing plan")
    p_auto_heal.set_defaults(func=cmd_auto_heal)

    # heal-pr
    p_heal_pr = subparsers.add_parser("heal-pr", help="Calculate self-healing confidence and generate Git PR draft")
    p_heal_pr.set_defaults(func=cmd_heal_pr)

    # mutate
    p_mut = subparsers.add_parser("mutate", help="Inject syntactic micro-mutants to verify test assertion strength")
    p_mut.set_defaults(func=cmd_mutate)

    # shard
    p_shard = subparsers.add_parser("shard", help="Balance parallel CI/CD test execution using duration-balanced bin-packing")
    p_shard.set_defaults(func=cmd_shard)

    # safety-check
    p_safety = subparsers.add_parser("safety-check", help="Action Safety Firewall & Blast Radius Containment")
    p_safety.set_defaults(func=cmd_safety_check)

    # contract-drift
    p_drift = subparsers.add_parser("contract-drift", help="Detect breaking API changes across OpenAPI / Swagger specs")
    p_drift.set_defaults(func=cmd_contract_drift)

    # mcp-serve
    p_mcp = subparsers.add_parser("mcp-serve", help="Start the JSON-RPC 2.0 stdio Model Context Protocol (MCP) server")
    p_mcp.set_defaults(func=cmd_mcp_serve)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Execute Comprehensive Project Health & AST Analysis")
    p_analyze.set_defaults(func=cmd_analyze)

    # verify
    p_verify = subparsers.add_parser("verify", help="Execute 9 Quality Gates DoD Verification")
    p_verify.set_defaults(func=cmd_verify)

    # lint
    p_lint = subparsers.add_parser("lint", help="Run AST Fake-Pass & Zero-Assertion Sentinel")
    p_lint.set_defaults(func=cmd_lint)

    # heal
    p_heal = subparsers.add_parser("heal", help="Query, learn, or record-failed into semantic memory cache")
    p_heal.set_defaults(func=cmd_heal)

    # distill
    p_distill = subparsers.add_parser("distill", help="Distill and filter verbose CLI logs by 95 percent")
    p_distill.set_defaults(func=cmd_distill)

    # impact
    p_impact = subparsers.add_parser("impact", help="Analyze code change impact using AST Knowledge Graph")
    p_impact.set_defaults(func=cmd_impact)

    # gherkin
    p_gherkin = subparsers.add_parser("gherkin", help="Compile Gherkin .feature files into test matrix, Universal IR and coverage-gap report (0-token)")
    p_gherkin.set_defaults(func=cmd_gherkin)

    # canary
    p_canary = subparsers.add_parser("canary", help="Run autonomous canary resilience benchmark")
    p_canary.set_defaults(func=cmd_canary)

    # clean
    p_clean = subparsers.add_parser("clean", help="Clean build artifacts, __pycache__, and bytecode")
    p_clean.set_defaults(func=cmd_clean)

    # flaky
    p_flaky = subparsers.add_parser("flaky", help="Detect flaky tests and manage quarantine lifecycle")
    p_flaky.set_defaults(func=cmd_flaky)

    # transpile
    p_trans = subparsers.add_parser("transpile", help="Transpile test files across languages and frameworks (0-token)")
    p_trans.add_argument("source", help="Source file path")
    p_trans.add_argument("--to", required=True, choices=["playwright-ts", "playwright-python", "selenium-java", "katalon-groovy", "cypress-js"], help="Target framework")
    p_trans.add_argument("--out", default=None, help="Output directory")
    p_trans.set_defaults(func=cmd_transpile)

    # omni-scan
    p_omni = subparsers.add_parser("omni-scan", help="Scan repository and build polyglot test inventory (0-token)")
    p_omni.add_argument("path", default=".", nargs="?", help="Directory to scan")
    p_omni.add_argument("--json", action="store_true", help="Output raw JSON")
    p_omni.set_defaults(func=cmd_omni_scan)

    # report-bug
    p_bug = subparsers.add_parser("report-bug", help="Auto-generate enterprise Jira/Markdown Bug Ticket with RCA")
    p_bug.set_defaults(func=cmd_report_bug)

    # mock-shield
    p_mock = subparsers.add_parser("mock-shield", help="Generate API Route Interception & Chaos Fault Injection Shield")
    p_mock.set_defaults(func=cmd_mock_shield)

    # visual-mask
    p_mask = subparsers.add_parser("visual-mask", help="Smart Visual Masking & Anti-Flake Animation Blocker")
    p_mask.set_defaults(func=cmd_visual_mask)

    # ci-hook
    p_ci = subparsers.add_parser("ci-hook", help="CI/CD Silent Self-Healing Pipeline Hook & Automated PR Generator")
    p_ci.set_defaults(func=cmd_ci_hook)

    # migrate
    p_migrate = subparsers.add_parser("migrate", help="Autonomous suite migration from legacy (Katalon/Cypress) to modern Playwright")
    p_migrate.add_argument("--src", required=True, help="Source legacy test suite file or directory")
    p_migrate.add_argument("--dest", default="playwright_suite", help="Destination directory for migrated code")
    p_migrate.add_argument("--target", default="playwright-ts", choices=["playwright-ts", "playwright-python", "selenium-java", "cypress-js"], help="Target framework")
    p_migrate.set_defaults(func=cmd_migrate)

    # decouple-config
    p_decouple = subparsers.add_parser("decouple-config", help="Decouple hardcoded URLs, credentials, and secrets into env profiles")
    p_decouple.add_argument("target", nargs="?", default=os.getcwd(), help="Target directory to scan")
    p_decouple.add_argument("--fix", action="store_true", help="Apply environment variable replacements in-place")
    p_decouple.add_argument("--out-dir", default=None, help="Output directory for config profiles")
    p_decouple.set_defaults(func=cmd_decouple_config)

    # fuzz-api
    p_fuzz = subparsers.add_parser("fuzz-api", help="Autonomous API Fuzzing & Chaos Breaker (bắn mutation payloads, bắt 500, DB leak, SLA breach)")
    p_fuzz.set_defaults(func=cmd_fuzz_api)

    # som (Visual Grounding for Canvas / GIS)
    p_som = subparsers.add_parser("som", help="Multimodal Vision Grounding & Set-of-Marks (SoM) for Canvas/GIS without DOM")
    p_som.set_defaults(func=cmd_som)

    # export-postman
    p_postman = subparsers.add_parser("export-postman", help="Export OpenAPI / Swagger / HAR to Postman Collection v2.1.0 with auto-asserts")
    p_postman.set_defaults(func=cmd_export_postman)

    # generate-jmx
    p_jmx = subparsers.add_parser("generate-jmx", help="Generate Apache JMeter 5.x Test Plan XML (.jmx) with JMeter 360 Enterprise Capabilities")
    p_jmx.set_defaults(func=cmd_generate_jmx)

    # analyze-jtl
    p_jtl = subparsers.add_parser("analyze-jtl", help="Analyze JMeter .jtl results, evaluate P90/P95/P99 SLA, and enforce CI/CD Quality Gate")
    p_jtl.set_defaults(func=cmd_analyze_jtl)

    # export-excel
    p_excel = subparsers.add_parser("export-excel", help="Convert Markdown Test Cases into Styled Enterprise Excel (.xlsx)")
    p_excel.add_argument("input", nargs="?", help="Path to input Markdown file (.md)")
    p_excel.add_argument("-o", "--output", help="Path to output Excel file (.xlsx)")
    p_excel.add_argument("--sheet-name", default="Test Cases", help="Worksheet title (default: Test Cases)")
    p_excel.set_defaults(func=cmd_export_excel)

    # correlate-telemetry
    p_telemetry = subparsers.add_parser("correlate-telemetry", help="Correlate Client-Side JMeter latency with Server-Side APM CPU/RAM/DB telemetry")
    p_telemetry.set_defaults(func=cmd_correlate_telemetry)

    # analyze-newman
    p_newman = subparsers.add_parser("analyze-newman", help="Analyze Postman / Newman test results, triage failed assertions, and enforce CI/CD Quality Gate")
    p_newman.set_defaults(func=cmd_analyze_newman)

    # update
    p_update = subparsers.add_parser("update", help="1-Click update Synapse-Hub to latest version from GitHub/NPM")
    p_update.add_argument("--check", action="store_true", help="Check for available updates without applying")
    p_update.set_defaults(func=cmd_update)

    # skillspector (AI Agent Skill & MCP Security Scanner)
    p_skillspector = subparsers.add_parser("skillspector", help="AI Agent Skill & MCP Security Sentinel (71 vectors, NVIDIA SkillSpector spec)")
    p_skillspector.add_argument("path", nargs="?", default=".", help="Skill directory or file to scan (default: current directory)")
    p_skillspector.add_argument("--format", choices=["terminal", "json", "markdown", "sarif"], default="terminal", help="Output format")
    p_skillspector.add_argument("--output", "-o", help="Write report to output file")
    p_skillspector.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on HIGH/CRITICAL finding")
    p_skillspector.set_defaults(func=cmd_skillspector)

    # verify-author (Author Provenance & Anti-Tamper Integrity Guard)
    p_author = subparsers.add_parser("verify-author", help="Verify author attribution, provenance, and anti-tamper integrity")
    p_author.set_defaults(func=cmd_verify_author)

    # tokens (Cross-Platform Token & Cost Auditor)
    p_tokens = subparsers.add_parser("tokens", help="Audit token usage and estimated API cost across Antigravity, Cursor, and Claude Code")
    p_tokens.add_argument("--platform", "-p", choices=["auto", "antigravity", "cursor", "claude", "all"], default="auto", help="AI platform to audit (default: auto)")
    p_tokens.add_argument("--session", type=str, help="Specific session ID or index to audit")
    p_tokens.add_argument("--current", action="store_true", help="Audit current active conversation")
    p_tokens.add_argument("--last", action="store_true", help="Audit previous completed session (default)")
    p_tokens.add_argument("--last-task", action="store_true", help="Audit specifically the last turn of target session")
    p_tokens.add_argument("--turns", action="store_true", help="Show full turn-by-turn breakdown table")
    p_tokens.add_argument("--rolling", "--budget", action="store_true", dest="rolling", help="Show 5-hour and 7-day rolling window quota & remaining tokens")
    p_tokens.add_argument("--savings", action="store_true", help="Show Hub vs. Non-Hub token and cost savings comparison")
    p_tokens.add_argument("--header", action="store_true", help="Print Pre-Flight confirmation block lines")
    p_tokens.add_argument("--list", action="store_true", help="List recent conversations")
    p_tokens.add_argument("--pricing", choices=["gemini-flash", "gemini-pro", "claude-sonnet", "claude-opus", "gpt-4o", "gpt-4o-mini"], default=None, help="Model pricing basis (default: auto-detected)")
    p_tokens.add_argument("--json", action="store_true", help="Output machine-readable JSON format")
    p_tokens.add_argument("--file", type=str, help="Direct path to a transcript.jsonl file")
    p_tokens.set_defaults(func=cmd_tokens)

    # dashboard (Standalone One-Page HTML Executive Dashboard)
    p_dashboard = subparsers.add_parser("dashboard", help="Generate standalone one-page executive HTML dashboard (zero CDN deps)")
    p_dashboard.add_argument("target", nargs="?", default=None, help="Target repository directory (default: current or Hub)")
    p_dashboard.add_argument("--output", "-o", help="Output HTML file path (default: <target>/reports/PROJECT_DASHBOARD.html)")
    p_dashboard.add_argument("--open", action="store_true", help="Automatically open generated dashboard in default browser")
    p_dashboard.add_argument("--json", action="store_true", help="Print summary JSON to stdout")
    p_dashboard.set_defaults(func=cmd_dashboard)

    # watch (Real-Time Incremental Watch Mode Sentinel)
    p_watch = subparsers.add_parser("watch", help="Real-Time incremental watch mode & test engineering HUD (< 100ms feedback)")
    p_watch.add_argument("target", nargs="?", default=".", help="Directory to monitor (default: current directory)")
    p_watch.add_argument("--debounce", type=float, default=0.8, help="Debounce interval in seconds (default: 0.8)")
    p_watch.add_argument("--once", action="store_true", help="Run incremental scan once on all files and exit")
    p_watch.set_defaults(func=cmd_watch)

    args, unknown = parser.parse_known_args()
    if getattr(args, "offline", False):
        os.environ["AGENT_QA_OFFLINE"] = "1"
        print("🔒 [OFFLINE MODE] Air-Gapped Deterministic Mode Active. 100% Local AST & Heuristics (Zero External API calls).")

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    # Enforce cryptographic author attribution and anti-tamper provenance
    from author_integrity import assert_integrity_or_raise
    assert_integrity_or_raise()

    # Non-intrusive cached update notification (24h cache)
    if args.subcommand not in ("update", "mcp-serve", "version"):
        try:
            import update_sentinel
            update_sentinel.check_for_updates(force=False, notify=True)
        except Exception:
            pass

    # Dispatch subcommand
    args.func(args)


if __name__ == "__main__":
    main()
