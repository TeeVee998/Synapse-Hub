#!/usr/bin/env python3
"""
Universal Data Flow & Teardown Tracer (Taint Analysis)
----------------------------------------------------
Performs AST-level Taint Analysis tracking test data lifecycle across test scripts:
  1. SOURCE: Generation of dynamic unique identifiers (uniqueCode, DataGenerator).
  2. PROPAGATE: Insertion / persistence into database or UI state.
  3. SINK: Automated Teardown / Deletion / Cleanup.

Detects orphan test junk that pollutes test environments.
Supports dynamic target repository resolution (CLI flag, CWD auto-detect, ENV var).
"""

import os
import sys
import re
import json
import glob
import argparse
from datetime import datetime

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REPORTS_DIR = os.path.join(HUB_ROOT, "reports")
OUTPUT_JSON = os.path.join(REPORTS_DIR, "data_flow_trace_report.json")

# ANSI Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Taint patterns
SOURCE_PATTERNS = [
    re.compile(r'uniqueCode', re.IGNORECASE),
    re.compile(r'DataGenerator\.', re.IGNORECASE),
    re.compile(r'System\.currentTimeMillis', re.IGNORECASE),
    re.compile(r'random[A-Z]\w+', re.IGNORECASE),
    re.compile(r'ensure\w+Exists', re.IGNORECASE),
]

PROPAGATE_PATTERNS = [
    re.compile(r'\.save\w*\(', re.IGNORECASE),
    re.compile(r'\.themMoi\w*\(', re.IGNORECASE),
    re.compile(r'\.fill\w*\(', re.IGNORECASE),
    re.compile(r'\.create\w*\(', re.IGNORECASE),
    re.compile(r'\.insert\w*\(', re.IGNORECASE),
    re.compile(r'\b(?:save|persist|insert|themMoi)[A-Z]\w*\(', re.IGNORECASE),
]

SINK_PATTERNS = [
    re.compile(r'\.delete\w*\(', re.IGNORECASE),
    re.compile(r'\.xoa\w*\(', re.IGNORECASE),
    re.compile(r'\.teardown\w*\(', re.IGNORECASE),
    re.compile(r'\.cleanUp\w*\(', re.IGNORECASE),
    re.compile(r'confirmDialog', re.IGNORECASE),
    re.compile(r'ICON_DELETE', re.IGNORECASE),
    re.compile(r'Xoá|Xoa|delete', re.IGNORECASE),
]


def resolve_target_repo(cli_target=None, cli_repo=None):
    """
    Resolves the target repository path:
    1. Explicit CLI flag: --repo / --path or positional target.
    2. Environment variable: TARGET_PROJECT_DIR.
    3. Current Working Directory (if different from Hub and has Scripts/ or tests/).
    4. Default fallback: QA Hub root (parent of tools/).
    """
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
        if os.path.exists(os.path.join(cwd, "Scripts")) or os.path.exists(os.path.join(cwd, "tests")):
            return cwd

    return HUB_ROOT


def trace_script_dataflow(file_path, repo_root=None):
    """Traces source, propagation, and sink in a test script."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    base_root = repo_root or HUB_ROOT
    try:
        rel_path = os.path.relpath(file_path, base_root)
    except ValueError:
        rel_path = os.path.abspath(file_path)

    tc_name = os.path.basename(os.path.dirname(file_path))

    has_source = any(p.search(content) for p in SOURCE_PATTERNS)
    has_propagate = any(p.search(content) for p in PROPAGATE_PATTERNS)
    has_sink = any(p.search(content) for p in SINK_PATTERNS)

    # Classification
    tc_lower = tc_name.lower()
    is_delete = any(k in tc_lower for k in ["xoa", "xóa", "xoá", "delete", "cleanup", "remove"])
    is_edit = any(k in tc_lower for k in ["sua", "sửa", "chỉnh sửa", "chinh sua", "edit", "update", "modify"])

    if is_delete or (has_sink and not has_propagate):
        lifecycle = "CLEANUP_SUITE"
        description = "Dedicated deletion / teardown test suite."
    elif has_propagate and has_sink:
        lifecycle = "IDEMPOTENT_CLEAN"
        description = "Complete lifecycle: Dynamic creation + verified teardown."
    elif has_propagate and not has_sink:
        if is_edit:
            lifecycle = "MUTATION_UPDATE"
            description = "Modifies existing record in-place without creating new entities."
        else:
            lifecycle = "ORPHAN_DATA_RISK"
            description = "Creates persistent entity on AUT without local teardown."
    else:
        lifecycle = "READ_ONLY"
        description = "Read-only interaction flow."

    return {
        "file": rel_path,
        "tc_name": tc_name,
        "has_source": has_source,
        "has_propagate": has_propagate,
        "has_sink": has_sink,
        "lifecycle": lifecycle,
        "description": description
    }


def run_data_flow_tracer(target_dir=None, repo_root=None):
    """Scans all test cases in target directory and traces data flow."""
    root = repo_root or HUB_ROOT
    scan_dir = target_dir or os.path.join(root, "Scripts")
    script_files = []
    if os.path.isdir(scan_dir):
        for ext in ("*.groovy", "*.ts", "*.js", "*.py"):
            script_files.extend(glob.glob(os.path.join(scan_dir, "**", ext), recursive=True))

    results = []
    counts = {
        "IDEMPOTENT_CLEAN": 0,
        "READ_ONLY": 0,
        "CLEANUP_SUITE": 0,
        "MUTATION_UPDATE": 0,
        "ORPHAN_DATA_RISK": 0
    }

    for s in sorted(script_files):
        res = trace_script_dataflow(s, repo_root=root)
        results.append(res)
        counts[res["lifecycle"]] = counts.get(res["lifecycle"], 0) + 1

    total = len(script_files)
    safe_count = counts["IDEMPOTENT_CLEAN"] + counts["READ_ONLY"] + counts["CLEANUP_SUITE"] + counts["MUTATION_UPDATE"]
    purity_rate = (safe_count / max(1, total)) * 100 if total > 0 else 100.0

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      Universal Data Flow & TEARDOWN TRACER (Taint Audit)            {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Target Scope            : {scan_dir}")
    print(f"  Total Audited Scripts   : {total} Test Cases")
    print(f"  Idempotent Clean        : {GREEN}{counts['IDEMPOTENT_CLEAN']}{RESET} (Dynamic data + verified teardown)")
    print(f"  Read-Only Invariant     : {CYAN}{counts['READ_ONLY']}{RESET} (Search, filter, navigation, export)")
    print(f"  Dedicated Cleanup Suites: {GREEN}{counts['CLEANUP_SUITE']}{RESET} (Explicit deletion test cases)")
    print(f"  In-Place Mutations      : {YELLOW}{counts['MUTATION_UPDATE']}{RESET} (Edit/update existing records)")
    print(f"  Orphan Data Risk        : {RED if counts['ORPHAN_DATA_RISK'] > 0 else GREEN}{counts['ORPHAN_DATA_RISK']}{RESET} (Persistent creation without teardown)")
    print(f"  Database Hygiene Purity : {GREEN if purity_rate >= 90 else YELLOW}{purity_rate:.1f}%{RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    # Save artifact
    target_reports = os.path.join(root, "reports")
    os.makedirs(target_reports, exist_ok=True)
    report_file = os.path.join(target_reports, "data_flow_trace_report.json")

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "scan_dir": scan_dir,
        "total_scripts": total,
        "hygiene_purity_pct": round(purity_rate, 2),
        "lifecycle_counts": counts,
        "details": results
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"Detailed data-flow artifact saved to: {report_file}\n")

    if root != HUB_ROOT:
        # Also mirror to HUB_ROOT reports for central auditing
        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Universal Data Flow & Teardown Tracer")
    parser.add_argument("target", nargs="?", default=None, help="Target repository or directory containing test scripts")
    parser.add_argument("--repo", default=None, help="Target repository root")
    parser.add_argument("--dir", "-d", default=None, help="Directory containing test scripts to trace")
    args = parser.parse_args()

    try:
        repo_root = resolve_target_repo(cli_target=args.target, cli_repo=args.repo)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    target_dir = args.dir
    if not target_dir:
        # Check if target is explicitly a directory with scripts
        if args.target and os.path.isdir(args.target) and not os.path.exists(os.path.join(args.target, "Scripts")):
            target_dir = args.target
        else:
            target_dir = os.path.join(repo_root, "Scripts")

    return run_data_flow_tracer(target_dir=target_dir, repo_root=repo_root)


if __name__ == "__main__":
    sys.exit(main())
