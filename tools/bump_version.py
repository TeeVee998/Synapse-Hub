#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/bump_version.py — Atomic Universal Version Bumper for Synapse Hub

Synchronizes version numbers across all polyglot targets in a single command:
  1. package.json (NPM)
  2. pyproject.toml (Python/Poetry/PEP 621)
  3. skills_manifest.json (Skill Catalog Index)
  4. tools/cli.py (Agent-QA CLI)
  5. tools/mcp_server.py (MCP Protocol Server)
  6. tools/browser_helpers.js (In-Browser CDP Helper)
  7. tools/mcp_excel_server.ps1 (PowerShell MCP Service)
  8. docs/ARCHITECTURE.md (Architecture Specifications)
  9. README.md (Bilingual Documentation & Badges)

Usage:
  python3 tools/bump_version.py patch                  # 2.0.1 -> 2.0.2
  python3 tools/bump_version.py minor                  # 2.0.1 -> 2.1.0
  python3 tools/bump_version.py major                  # 2.0.1 -> 3.0.0
  python3 tools/bump_version.py 2.0.5                  # Explicit version
  python3 tools/bump_version.py patch --commit         # Bump + git commit
  python3 tools/bump_version.py patch --commit --push  # Bump + commit + git push + tag
  python3 tools/bump_version.py patch --dry-run        # Preview only
"""

import sys
import os
import re
import json
import argparse
import subprocess

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_semver(v_str: str):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", v_str.strip())
    if not m:
        raise ValueError(f"Invalid semver: '{v_str}'. Must follow major.minor.patch[-suffix]")
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)

def calculate_next_version(current: str, action: str) -> str:
    major, minor, patch, suffix = parse_semver(current)
    action = action.lower()
    if action == "patch":
        return f"{major}.{minor}.{patch + 1}"
    elif action == "minor":
        return f"{major}.{minor + 1}.0"
    elif action == "major":
        return f"{major + 1}.0.0"
    else:
        # Validate that action itself is a valid semver
        parse_semver(action)
        return action

def get_current_version() -> str:
    pkg_file = os.path.join(REPO_ROOT, "package.json")
    with open(pkg_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("version", "2.0.0")

def update_json_root_version(rel_path: str, new_ver: str, dry_run: bool = False) -> bool:
    full_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(full_path):
        print(f"  [WARN] File not found: {rel_path}")
        return False

    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    old_ver = data.get("version")
    if old_ver == new_ver:
        print(f"  [SKIP] {rel_path} already at v{new_ver}")
        return False

    data["version"] = new_ver
    if not dry_run:
        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  [UPDATED] {rel_path} (root version {old_ver} -> {new_ver})")
    else:
        print(f"  [DRY-RUN] Would update {rel_path} (root version {old_ver} -> {new_ver})")
    return True

def update_file(rel_path: str, pattern: str, replacement: str, dry_run: bool = False) -> bool:
    full_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(full_path):
        print(f"  [WARN] File not found: {rel_path}")
        return False

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content, count = re.subn(pattern, replacement, content)
    if count == 0:
        print(f"  [SKIP] No pattern match in {rel_path}")
        return False

    if not dry_run:
        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        print(f"  [UPDATED] {rel_path} ({count} occurrence{'s' if count > 1 else ''})")
    else:
        print(f"  [DRY-RUN] Would update {rel_path} ({count} occurrence{'s' if count > 1 else ''})")
    return True

def run_tests() -> bool:
    print("\n🔍 Running verification suite...")
    cmd = [sys.executable, "-m", "unittest", "discover", "tests", "-p", "test_*.py"]
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    if res.returncode != 0:
        print("❌ Unit tests failed! Aborting release.")
        return False
    print("✅ All unit tests PASSED.")

    verify_script = os.path.join(REPO_ROOT, "tools", "verify_all.py")
    res_verify = subprocess.run([sys.executable, verify_script], cwd=REPO_ROOT)
    if res_verify.returncode != 0:
        print("❌ Quality Gates failed! Aborting release.")
        return False
    print("✅ 9 Quality Gates DoD PASSED.")
    return True

def git_commit_and_tag(version: str, push: bool = False):
    print(f"\n📦 Creating Git commit and tag v{version}...")
    subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"chore(release): bump version to v{version}"], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "tag", f"v{version}"], cwd=REPO_ROOT, check=True)
    print(f"✅ Git commit and tag v{version} created.")

    if push:
        print(f"🚀 Pushing commit and tags to remote origin...")
        subprocess.run(["git", "push", "origin", "HEAD", "--tags"], cwd=REPO_ROOT, check=True)
        print(f"✅ Remote origin synchronized.")

def main():
    parser = argparse.ArgumentParser(description="Atomic Universal Version Bumper for Synapse Hub")
    parser.add_argument("action", nargs="?", default="patch", help="patch | minor | major | <explicit_version> (default: patch)")
    parser.add_argument("--dry-run", action="store_true", help="Preview version changes without writing files")
    parser.add_argument("--no-test", action="store_true", help="Skip running test suite after bumping")
    parser.add_argument("--commit", action="store_true", help="Auto-commit changes with conventional message")
    parser.add_argument("--tag", action="store_true", help="Create Git tag v<version>")
    parser.add_argument("--push", action="store_true", help="Push commit and tags to Git remote")

    args = parser.parse_args()

    current_ver = get_current_version()
    new_ver = calculate_next_version(current_ver, args.action)

    print("======================================================================")
    print("       SYNAPSE HUB — ATOMIC UNIVERSAL VERSION BUMPER                  ")
    print("======================================================================")
    print(f"  Current Version : {current_ver}")
    print(f"  Target Version  : {new_ver} ({args.action})")
    print(f"  Mode            : {'DRY RUN (Preview)' if args.dry_run else 'APPLY CHANGES'}")
    print("======================================================================")

    # 1. package.json
    update_json_root_version("package.json", new_ver, args.dry_run)

    # 1b. plugin.json
    update_json_root_version("plugin.json", new_ver, args.dry_run)

    # 2. pyproject.toml
    update_file("pyproject.toml", r'(version\s*=\s*")[^"]+(")', rf"\g<1>{new_ver}\g<2>", args.dry_run)

    # 3. skills_manifest.json
    update_json_root_version("skills_manifest.json", new_ver, args.dry_run)

    # 4. tools/cli.py
    update_file("tools/cli.py", r'(version\s*=\s*")[^"]+(")', rf"\g<1>{new_ver}\g<2>", args.dry_run)

    # 5. tools/mcp_server.py
    update_file("tools/mcp_server.py", r'(SERVER_VERSION\s*=\s*")[^"]+(")', rf"\g<1>{new_ver}\g<2>", args.dry_run)

    # 6. tools/browser_helpers.js
    update_file("tools/browser_helpers.js", r"(__version === ')[^']+(')", rf"\g<1>{new_ver}\g<2>", args.dry_run)
    update_file("tools/browser_helpers.js", r"(__version:\s*')[^']+(')", rf"\g<1>{new_ver}\g<2>", args.dry_run)

    # 7. tools/mcp_excel_server.ps1
    update_file("tools/mcp_excel_server.ps1", r'(version\s*=\s*")[^"]+(")', rf"\g<1>{new_ver}\g<2>", args.dry_run)

    # 8. docs/ARCHITECTURE.md
    update_file("docs/ARCHITECTURE.md", r'(>\s*\*\*Version:\*\*\s*`)[^`]+(`)', rf"\g<1>{new_ver}\g<2>", args.dry_run)

    # 9. README.md (Documentation headings and mermaid badges)
    update_file("README.md", r'(Phiên bản Hub:\*\*\s*`v)[^`]+(`)', rf"\g<1>{new_ver}\g<2>", args.dry_run)
    update_file("README.md", r'(Hub Version:\*\*\s*`v)[^`]+(`)', rf"\g<1>{new_ver}\g<2>", args.dry_run)
    update_file("README.md", r'(Intelligence Core v)[^")\]]+', rf"\g<1>{new_ver}", args.dry_run)

    if args.dry_run:
        print("\n[INFO] Dry-run completed. No files modified on disk.")
        return

    # Tests verification
    if not args.no_test:
        if not run_tests():
            sys.exit(1)

    # Git operations
    if args.commit or args.push:
        git_commit_and_tag(new_ver, push=args.push)

    print("\n======================================================================")
    print(f"🎉 VERSION BUMP COMPLETE: v{current_ver} ➔ v{new_ver}")
    print("======================================================================")
    print("Next steps:")
    print(f"  • Publish to NPM : npm publish")
    print(f"  • Or Git Push    : git push origin HEAD --tags")
    print("======================================================================")

if __name__ == "__main__":
    main()
