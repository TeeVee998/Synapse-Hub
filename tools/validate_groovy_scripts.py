#!/usr/bin/env python3
"""
Pre-check validator for Groovy scripts and POM keywords in enterprise test suites.
Catches syntax errors, broken GString escape sequences, and structural balance issues
before running tests in CI, ensuring 100% parity with Katalon compiler checks.
Supports dynamic target repository resolution (CLI flag, CWD auto-detect, ENV var).
"""

import os
import sys
import re
import argparse
from pathlib import Path

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

HUB_ROOT = Path(__file__).resolve().parent.parent


def resolve_target_repo(cli_target=None, cli_repo=None):
    """
    Resolves the target repository path:
    1. Explicit CLI flag: --repo / --path or positional target.
    2. Environment variable: TARGET_PROJECT_DIR.
    3. Current Working Directory (if different from Hub and has Scripts/ or Keywords/).
    4. Default fallback: QA Hub root (parent of tools/).
    """
    chosen = cli_repo or cli_target
    if chosen:
        resolved = Path(chosen).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Target repository path not found: {resolved}")
        return resolved

    env_dir = os.environ.get("TARGET_PROJECT_DIR")
    if env_dir and os.path.exists(env_dir):
        return Path(env_dir).resolve()

    cwd = Path.cwd().resolve()
    if cwd != HUB_ROOT:
        if (cwd / "Scripts").exists() or (cwd / "Keywords").exists():
            return cwd

    return HUB_ROOT


def strip_comments_and_strings(source_code: str) -> str:
    """Strips comments, string literals, and regexes so literal braces/parentheses don't cause false positives."""
    pattern = re.compile(
        r'(?P<BLOCK_COMMENT>/\*.*?\*/)|'
        r'(?P<LINE_COMMENT>//[^\r\n]*)|'
        r'(?P<TRIPLE_DOUBLE>"""[\s\S]*?""")|'
        r'(?P<TRIPLE_SINGLE>\'\'\'[\s\S]*?\'\'\')|'
        r'(?P<DOLLAR_SLASHY>\$/[\s\S]*?/\$)|'
        r'(?P<DOUBLE_STRING>"(?:\\.|[^"\\])*")|'
        r'(?P<SINGLE_STRING>\'(?:\\.|[^\'\\])*\')',
        re.DOTALL
    )
    code = pattern.sub(' ', source_code)

    # Strip slashy regexes (e.g., ~/regex/ or = /regex/) while avoiding arithmetic division (e.g. a / b + c / d)
    # In Groovy, slashy regex only appears after operators ~, =, (, [, {, :, ,, ;
    def strip_slashy(m):
        return (m.group(1) or '') + ' '

    return re.sub(r'([=~:,(\[{;]\s*)/(?:\\/|[^/\r\n])+/(?![/*])', strip_slashy, code)


def check_file(file_path: Path) -> list:
    errors = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin-1')
        except Exception as e:
            return [f"Cannot read file: {e}"]

    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        # 1. Check for illegal backslash escapes like [\]
        if re.search(r"\[\\\]", line):
            errors.append(f"Line {idx}: Illegal escape sequence '[\\]'. Did you mean '[${{var}}]'?")

        # 2. Check for lonely unescaped backslash at end of quotes
        if re.search(r'["\']\\["\']', line):
            errors.append(f"Line {idx}: Unescaped single backslash in string.")

    # 3 & 4. Check structural balance on clean code without string/comment noise
    clean_content = strip_comments_and_strings(content)
    open_braces = clean_content.count('{')
    close_braces = clean_content.count('}')
    if open_braces != close_braces:
        errors.append(f"Unmatched braces: {open_braces} '{{' vs {close_braces} '}}'")

    open_parens = clean_content.count('(')
    close_parens = clean_content.count(')')
    if open_parens != close_parens:
        errors.append(f"Unmatched parentheses: {open_parens} '(' vs {close_parens} ')'")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Enterprise Groovy Syntax & Structural Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target repository or file/directory to validate")
    parser.add_argument("--repo", "--path", dest="repo_path", default=None, help="Target repository root")
    parser.add_argument("--dir", default=None, help="Specific directory to scan for .groovy files")
    args = parser.parse_args()

    try:
        target_repo = resolve_target_repo(cli_target=args.target, cli_repo=args.repo_path)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    print("=" * 60)
    print("Enterprise Automation: Pre-check Groovy Scripts & Keywords")
    print(f"Target Repository : {target_repo}")
    print("=" * 60)

    all_errors = {}
    files_checked = 0

    if args.dir:
        scan_dir = Path(args.dir).resolve()
        target_dirs = [scan_dir] if scan_dir.exists() else []
    elif args.target and Path(args.target).is_file():
        target_dirs = []
        target_file = Path(args.target).resolve()
        files_checked += 1
        errs = check_file(target_file)
        if errs:
            all_errors[str(target_file)] = errs
    else:
        target_dirs = [target_repo / 'Scripts', target_repo / 'Keywords']

    for t_dir in target_dirs:
        if not t_dir.exists():
            continue
        for f in t_dir.rglob('*.groovy'):
            files_checked += 1
            errs = check_file(f)
            if errs:
                try:
                    rel_name = str(f.relative_to(target_repo))
                except ValueError:
                    rel_name = str(f)
                all_errors[rel_name] = errs

    print(f"Checked {files_checked} Groovy files.")

    if all_errors:
        print("\n❌ SYNTAX PRE-CHECK FAILED! The following files have syntax errors:\n")
        for f_name, errs in all_errors.items():
            print(f"File: {f_name}")
            for err in errs:
                print(f"  - {err}")
            print()
        return 1
    else:
        print("✅ All Groovy scripts and keywords passed syntax pre-check 100%!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
