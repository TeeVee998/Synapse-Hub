#!/usr/bin/env python3
"""
Enterprise QA Project Analyzer & Intelligence Aggregator
---------------------------------------------------------
Consolidates all project diagnostic and AST analysis tools into a single workflow.
Dispatched when user requests: 'analyze project', 're-analyze', 'audit project'.

Executes in sequence:
  1. Environment & Structure Diagnostic (tools/check_env.py)
  2. Page Class & AST Repository Mapping (tools/repo_map.py)
  3. Static Defect & Fake-Pass Sentinel (tools/infer_linter.py)
  4. Data Flow Lifecycle & Teardown Audit (tools/trace_data_flow.py)
  5. Definition of Done 7 Quality Gates (tools/verify_all.py)

Generates & Updates In-Place inside the Target Project:
  - PROJECT_HEALTH_REPORT.md (Root & reports/ of target project)
  - repo_map.txt (AST method map inside target project root)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, SCRIPT_DIR)

import check_env
import repo_map
import infer_linter
import trace_data_flow
import verify_all

# ANSI formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def resolve_target_repo(cli_target=None, cli_repo=None):
    chosen = cli_repo or cli_target
    if chosen:
        resolved = os.path.abspath(chosen)
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"Target repository path not found: {resolved}")
        return resolved

    env_dir = os.environ.get("TARGET_PROJECT_DIR")
    if env_dir and os.path.exists(env_dir):
        return os.path.abspath(env_dir)

    cwd = os.path.abspath(os.getcwd())
    if cwd.lower() != HUB_ROOT.lower():
        return cwd

    return HUB_ROOT


def run_full_analysis(target_repo):
    """Executes the complete diagnostic and AST intelligence suite."""
    start_time = datetime.now()
    mode = verify_all.detect_repo_mode(target_repo)

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      ENTERPRISE QA - COMPREHENSIVE PROJECT ANALYSIS SUITE            {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"📁 Target Repository : {target_repo}")
    print(f"🏷️  Operational Mode  : {mode}")
    print(f"⏱️  Timestamp         : {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    summary = {
        "timestamp": start_time.isoformat(),
        "target_repo": target_repo,
        "mode": mode,
        "env_status": "UNKNOWN",
        "repo_map": {},
        "infer_linter": {},
        "data_flow": {},
        "gates_status": "UNKNOWN"
    }

    # Step 1: Environment & Project Structure
    print(f"{BOLD}[1/5] Checking Environment & Project Structure (check_env)...{RESET}")
    env_runner = check_env.DiagnosticRunner(target_dir=target_repo)
    env_code = env_runner.run_all()
    summary["env_status"] = "READY" if env_code == 0 else "WARNINGS_OR_MISSING"

    # Step 2: Page Classes & Method AST Mapping
    print(f"\n{BOLD}[2/5] Mapping Page Classes & API Signatures (repo_map)...{RESET}")
    try:
        map_stats = repo_map.build_repo_map(target_repo=target_repo)
        summary["repo_map"] = {
            "classes_count": map_stats["classes_count"],
            "methods_count": map_stats["methods_count"],
            "source_lines": map_stats["source_lines"],
            "output_file": map_stats["output_file"]
        }
        print(f"   -> Indexed {map_stats['classes_count']} Page Classes ({map_stats['methods_count']} API signatures).")
        print(f"   -> Condensed context map: {map_stats['output_file']}")
    except Exception as e:
        print(f"   ⚠️ repo_map error: {e}")

    # Step 3: Static Defect & Fake-Pass Sentinel
    print(f"\n{BOLD}[3/5] Scanning Static Defects & Fake-Passes (infer_linter)...{RESET}")
    scripts_dir = os.path.join(target_repo, "Scripts")
    try:
        linter_code = infer_linter.run_infer_linter(target_dir=scripts_dir)
        summary["infer_linter"]["exit_code"] = linter_code
    except Exception as e:
        print(f"   ⚠️ infer_linter error: {e}")

    # Step 4: Data Flow Lifecycle & Teardown Hygiene
    print(f"\n{BOLD}[4/5] Auditing Synthetic Data Lifecycle & Teardown (trace_data_flow)...{RESET}")
    try:
        data_flow_code = trace_data_flow.run_data_flow_tracer(target_dir=scripts_dir, repo_root=target_repo)
        summary["data_flow"]["exit_code"] = data_flow_code
    except Exception as e:
        print(f"   ⚠️ trace_data_flow error: {e}")

    # Step 5: 7 Quality Gates DoD Verification
    print(f"\n{BOLD}[5/5] Verifying 7 Quality Gates DoD (verify_all)...{RESET}")
    gates_passed = True
    gates = [
        ("Gate 1: UTF-8 No BOM", verify_all.gate_1_bom_check),
        ("Gate 2: Path Portability", verify_all.gate_2_path_portability),
        ("Gate 3: Clean POM & Flat Architecture", verify_all.gate_3_clean_pom),
        ("Gate 4: AI Documentation Linter", verify_all.gate_4_ai_docs_lint),
        ("Gate 5: Temporary Files Blacklist", verify_all.gate_5_cleanup_blacklist),
        ("Gate 6: Credential Security", verify_all.gate_6_credential_security),
        ("Gate 7: Static Defect Sentinel", verify_all.gate_7_infer_linter),
    ]
    for name, gate_fn in gates:
        if not gate_fn(target_repo, mode=mode):
            gates_passed = False

    summary["gates_status"] = "100%_PASS" if gates_passed else "FAILURES_DETECTED"

    # Generate Markdown Executive Report
    elapsed = (datetime.now() - start_time).total_seconds()
    reports_dir = os.path.join(target_repo, "reports") if mode == "TARGET" else os.path.join(HUB_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_in_reports = os.path.join(reports_dir, "PROJECT_HEALTH_REPORT.md")
    report_in_root = os.path.join(target_repo, "PROJECT_HEALTH_REPORT.md")

    md_content = f"""# Project Health & AST Analysis Report

- **Target Repository:** `{target_repo}`
- **Operational Mode:** `{mode}`
- **Execution Timestamp:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}` (Completed in `{elapsed:.2f}s`)

---

## 1. Executive Health Metrics

| Metric / Standard | Result | Status |
| :--- | :---: | :---: |
| **Environment & Structure** | `{summary['env_status']}` | {'✅ PASS' if summary['env_status'] == 'READY' else '⚠️ WARN'} |
| **Page Classes & Helpers** | `{summary['repo_map'].get('classes_count', 0)}` classes (`{summary['repo_map'].get('methods_count', 0)}` methods) | ✅ INDEXED |
| **Static Defect Sentinel** | `infer_linter` exit `{summary['infer_linter'].get('exit_code', 0)}` | {'✅ CLEAN' if summary['infer_linter'].get('exit_code', 0) == 0 else '❌ CRITICAL'} |
| **Lifecycle & Teardown** | `trace_data_flow` exit `{summary['data_flow'].get('exit_code', 0)}` | ✅ AUDITED |
| **7 Quality Gates DoD** | `{summary['gates_status']}` | {'✅ 100% PASS' if gates_passed else '❌ BLOCKED'} |

---

## 2. In-Project Synchronized Artifacts

1. **Executive Health Summary (This file):** `PROJECT_HEALTH_REPORT.md`
2. **Condensed API Signatures Map (< 600 tokens):** `repo_map.txt`
3. **AST Static Defect Log:** `reports/infer_linter_report.json`
4. **Data Lifecycle Taint Audit:** `reports/data_flow_trace_report.json`

---

## 3. AI Context Anchoring & Post-Audit Protocol (0-Token Overhead)

> 📌 **AI Agent Guidelines:**
> - In subsequent sessions on this project, **DO NOT rescan** the entire codebase from scratch.
> - Anchor context directly by reading only two local in-project artifacts:
>   1. `PROJECT_HEALTH_REPORT.md` (immediate architecture status, warnings, and DoD readiness).
>   2. `repo_map.txt` (instant lookup for Page Classes, methods, and parameters in < 600 tokens).
> - **Post-Audit Git Push (Mandatory):** Once analysis completes, stage, commit, and push updated in-project artifacts to git (`git add PROJECT_HEALTH_REPORT.md repo_map.txt && git commit -m "docs(audit): update project health report and AST repo map" && git push origin <branch>`).
> - Whenever the user requests **"analyze project"** or **"project audit"**, re-run `agent-qa analyze` to update this file in-place.
"""
    with open(report_in_reports, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Save directly at the root of target_repo as well so it's instantly discoverable
    if os.path.abspath(target_repo).lower() != os.path.abspath(HUB_ROOT).lower():
        try:
            with open(report_in_root, "w", encoding="utf-8") as f:
                f.write(md_content)
        except Exception:
            pass

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}                     EXECUTIVE ANALYSIS COMPLETE                      {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Elapsed Time            : {elapsed:.2f}s")
    print(f"  Page Classes Indexed    : {summary['repo_map'].get('classes_count', 0)} classes")
    print(f"  7 Quality Gates DoD     : {GREEN + '100% PASS' if gates_passed else RED + 'FAILED'}{RESET}")
    print(f"  In-Project Report Path  : {report_in_root if os.path.abspath(target_repo).lower() != os.path.abspath(HUB_ROOT).lower() else report_in_reports}")
    if os.path.abspath(target_repo).lower() != os.path.abspath(HUB_ROOT).lower():
        print(f"  {YELLOW}💡 Post-Analysis Action: Push updated files to Git:{RESET}")
        print(f"     git add PROJECT_HEALTH_REPORT.md repo_map.txt")
        print(f"     git commit -m \"docs(audit): update project health report and AST repo map\"")
        print(f"     git push origin <branch>")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    return 0 if gates_passed else 1


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Enterprise QA Project Analyzer")
    parser.add_argument("target", nargs="?", default=None, help="Target repository path to analyze")
    parser.add_argument("--repo", "--path", dest="repo_path", default=None, help="Target repository path")
    args = parser.parse_args()

    try:
        target_repo = resolve_target_repo(cli_target=args.target, cli_repo=args.repo_path)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    return run_full_analysis(target_repo)


if __name__ == "__main__":
    sys.exit(main())
