#!/usr/bin/env python3
"""
Enterprise AI Documentation & Artifact Linter (Anti-Drift Guard v2.0)
---------------------------------------------------------------
Automatically cross-references AI skills, agent instructions, and markdown
documents against the actual repository files, classes, methods, and test cases.

Checks:
  1. Page Class references: Matches against Keywords/pages/*.groovy.
  2. Test Suite references: Matches against Test Suites/*.ts.
  3. Tool script references: Matches against tools/*.
  4. Test Case references: Matches against Test Cases/*.tc (and validates TC-1..259 range).
  5. Method call references: Matches EnterpriseHelper.xxx() and BasePage.xxx() against real AST/regex methods.

Prevents AI agents from hallucinating nonexistent PageClasses, suites, tools, methods, or test cases.
Supports both Target Test Project mode and Hub Repository mode.
"""

import os
import sys
import glob
import re

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

GENERIC_PAGES = {
    "WebPage", "CurrentPage", "LandingPage", "GitHubPage", "SamplePage",
    "BasePage", "Page", "SinglePage", "MultiPage"
}

def extract_groovy_methods(file_path):
    """Extracts standard public/static methods from a Groovy class file."""
    methods = set()
    if not os.path.exists(file_path):
        return methods
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()
        method_pattern = re.compile(
            r'^\s*(?:@\w+\s+)*(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?'
            r'(?:void|def|String|int|boolean|List[^\s]*|TestObject|WebDriver|[A-Za-z0-9_<>\[\]]+)\s+([a-z][a-zA-Z0-9_]*)\s*\('
        )
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            m = method_pattern.search(line)
            if m:
                mname = m.group(1)
                if mname not in {"if", "for", "while", "switch", "catch"}:
                    methods.add(mname)
    except Exception:
        pass
    return methods

def get_actual_entities(repo_root):
    pages_dir = os.path.join(repo_root, "Keywords", "pages")
    helpers_dir = os.path.join(repo_root, "Keywords", "helpers")
    suites_dir = os.path.join(repo_root, "Test Suites")
    cases_dir = os.path.join(repo_root, "Test Cases")
    tools_dir = os.path.join(repo_root, "tools")

    actual_pages = set()
    class_methods = {}

    if os.path.isdir(pages_dir):
        for f in os.listdir(pages_dir):
            if f.endswith(".groovy"):
                pname = f[:-7]
                actual_pages.add(pname)
                class_methods[pname] = extract_groovy_methods(os.path.join(pages_dir, f))

    if os.path.isdir(helpers_dir):
        for f in os.listdir(helpers_dir):
            if f.endswith(".groovy"):
                hname = f[:-7]
                class_methods[hname] = extract_groovy_methods(os.path.join(helpers_dir, f))

    actual_suites = set()
    if os.path.isdir(suites_dir):
        for f in os.listdir(suites_dir):
            if f.endswith(".ts"):
                actual_suites.add(f[:-3])

    actual_cases = set()
    actual_tc_ids = set()
    if os.path.isdir(cases_dir):
        for f in os.listdir(cases_dir):
            if f.endswith(".tc"):
                base_name = f[:-3]
                actual_cases.add(base_name)
                m = re.match(r'(TC-\d+)', base_name)
                if m:
                    actual_tc_ids.add(m.group(1))

    actual_tools = set()
    if os.path.isdir(tools_dir):
        actual_tools.update(os.listdir(tools_dir))
    # Always include Hub tools directory in decoupled architecture
    hub_tools = os.path.abspath(os.path.dirname(__file__))
    if os.path.isdir(hub_tools):
        actual_tools.update(os.listdir(hub_tools))

    return actual_pages, actual_suites, actual_cases, actual_tc_ids, actual_tools, class_methods

def find_doc_files(repo_root):
    md_patterns = [
        os.path.join(repo_root, ".agents", "**", "*.md"),
        os.path.join(repo_root, "*.md"),
    ]
    doc_files = []
    for pattern in md_patterns:
        for f in glob.glob(pattern, recursive=True):
            rel = os.path.relpath(f, repo_root)
            if "node_modules" in rel or ".git" in rel or "allure-results" in rel:
                continue
            doc_files.append(rel)
    return sorted(doc_files)

def lint_docs(repo_root):
    actual_pages, actual_suites, actual_cases, actual_tc_ids, actual_tools, class_methods = get_actual_entities(repo_root)
    doc_files = find_doc_files(repo_root)

    page_pattern = re.compile(r'\b([A-Z][A-Za-z0-9]+Page)\b')
    suite_pattern = re.compile(r'(?:Test Suites/|-Suite\s+["\'](?:Test Suites/)?|--testSuitePath=["\'](?:Test Suites/)?)([A-Za-z0-9_]+)')
    tool_pattern = re.compile(r'\btools/([a-zA-Z0-9_\-\.]+\.(?:py|sh|ps1|bat|js))\b')
    tc_id_pattern = re.compile(r'\b(TC-\d+)\b')
    tc_path_pattern = re.compile(r'Test Cases/([A-Za-z0-9_ \-\.\(\)]+?)(?:\.tc)?["\s\)]')
    method_pattern = re.compile(r'\b(EnterpriseHelper|BasePage|[A-Z][a-zA-Z0-9]+Page)\.([a-z][a-zA-Z0-9_]+)\s*\(')

    errors = []
    warnings = []

    # Ignored tool references (examples, output targets, artifacts)
    ignored_tool_refs = {"api_matrix.json", "output.json", "report.json", "output.txt", "summary.json"}

    for doc in doc_files:
        full_path = os.path.join(repo_root, doc)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
        except Exception as e:
            errors.append(f"Cannot read {doc}: {e}")
            continue

        is_historical = "FINAL_REPORT.md" in doc or "POM_REFACTORING_PLAN.md" in doc

        for line_no, line in enumerate(lines, 1):
            # 1. Page Class Lint (Only strictly enforced if repository defines Page Classes in Keywords/pages)
            if actual_pages:
                for m in page_pattern.finditer(line):
                    pname = m.group(1)
                    if pname not in actual_pages and pname not in GENERIC_PAGES:
                        if is_historical:
                            continue
                        errors.append(f"[{doc}:{line_no}] Non-existent Page Class referenced: '{pname}' (Must be one of {sorted(actual_pages)})")

            # 2. Test Suite Lint (Only strictly enforced if repository defines Test Suites)
            if actual_suites:
                for m in suite_pattern.finditer(line):
                    sname = m.group(1)
                    if "xxx" in sname.lower() or "example" in sname.lower():
                        continue
                    if is_historical:
                        continue
                    if sname not in actual_suites:
                        errors.append(f"[{doc}:{line_no}] Non-existent Test Suite referenced: '{sname}'")

            # 3. Tool Script Lint (Enforced in both Hub and Target modes)
            for m in tool_pattern.finditer(line):
                tname = m.group(1)
                if tname in ignored_tool_refs:
                    continue
                if tname not in actual_tools:
                    errors.append(f"[{doc}:{line_no}] Non-existent tool script referenced: 'tools/{tname}'")

            # 4. Test Case Validation (Only strictly enforced if repository defines Test Cases)
            if actual_cases and not is_historical:
                # 4a. Validate TC-xxx numeric range
                for m in tc_id_pattern.finditer(line):
                    tcid = m.group(1)
                    num = int(tcid[3:])
                    if num < 1 or num > 259:
                        errors.append(f"[{doc}:{line_no}] Out-of-range Test Case ID referenced: '{tcid}' (Valid range: TC-1 to TC-259)")

                # 4b. Validate full Test Cases/... paths
                for m in tc_path_pattern.finditer(line):
                    tcname = m.group(1).strip()
                    if "xxx" in tcname.lower() or "*" in tcname or "example" in tcname.lower():
                        continue
                    if tcname.endswith(".tc"):
                        tcname = tcname[:-3]
                    if tcname not in actual_cases:
                        # Check prefix match
                        matching = [c for c in actual_cases if c.startswith(tcname)]
                        if not matching:
                            errors.append(f"[{doc}:{line_no}] Non-existent Test Case path referenced: 'Test Cases/{tcname}'")

            # 5. Method Call Lint (Cross-checks Class.method() against Groovy AST/regex)
            for m in method_pattern.finditer(line):
                cname = m.group(1)
                mname = m.group(2)
                if "xxx" in mname.lower() or "example" in mname.lower():
                    continue
                if cname in class_methods:
                    valid_methods = class_methods[cname]
                    # Also include inherited BasePage methods if it's a Page class
                    if cname != "BasePage" and "BasePage" in class_methods:
                        valid_methods = valid_methods.union(class_methods["BasePage"])

                    if mname not in valid_methods:
                        errors.append(f"[{doc}:{line_no}] Non-existent method referenced: '{cname}.{mname}()' (Class '{cname}' does not define this method)")

    return errors, warnings

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enterprise AI Documentation & Artifact Linter")
    parser.add_argument("target", nargs="?", default=None, help="Path to repository root to lint")
    parser.add_argument("--repo", default=None, help="Path to repository root to lint")
    args = parser.parse_args()

    target_path = args.repo or args.target
    if target_path:
        repo_root = os.path.abspath(target_path)
    else:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    print(f"[AI-DOCS-LINT] Running Documentation & Artifact Linter on: {os.path.basename(repo_root)}")
    errors, warnings = lint_docs(repo_root)

    if warnings:
        print(f"\n[WARN] {len(warnings)} Warnings:")
        for w in warnings:
            print(f"   - {w}")

    if errors:
        print(f"\n[FAIL] {len(errors)} Lint Errors Found (Documentation Drift / Hallucination):")
        for e in errors:
            print(f"   - {e}")
        print("\n[BLOCKED] Verification failed: Please align documentation with real disk entities.")
        return 1
    else:
        print("[PASS] All documented tools, PageClasses, Suites, and Method calls verified on disk.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
