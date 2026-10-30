#!/usr/bin/env python3
"""
Enterprise QA Autonomous Project Setup & Bootstrap Engine
----------------------------------------------------------
Transforms any target test project into an AI-Ready Enterprise Suite in 1-click.
Dispatched automatically by AI Agents (Zero-Command Protocol) or via 'agent-qa setup'.

Automated actions:
  1. Detects project tech stack (Katalon, Playwright, Cypress, Pytest).
  2. Generates tailored 'PROJECT_AI_GUIDE.md' if missing.
  3. Deploys Universal AI Bridges (.cursor/rules, CLAUDE.md, .github/copilot-instructions.md, .windsurfrules).
  4. Injects Antigravity Global Plugin (~/.gemini/config/plugins/synapse-hub).
  5. Installs automated Git Pre-Push Hook (.git/hooks/pre-push) for zero-leakage protection.
  6. Triggers 5-in-1 Health Audit (tools/analyze_project.py):
     - Maps AST method signatures (repo_map.txt).
     - Scans fake passes (infer_linter).
     - Audits database teardown hygiene (trace_data_flow).
     - Generates in-project health report (PROJECT_HEALTH_REPORT.md).
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
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
TEMPLATES_DIR = os.path.join(HUB_ROOT, "templates")
sys.path.insert(0, SCRIPT_DIR)

import analyze_project
import verify_all
import project_state

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
        if resolved.lower() == HUB_ROOT.lower():
            print(f"{RED}{BOLD}X [CWD CONFUSION GUARD] Target repository cannot be Synapse-Hub itself!{RESET}")
            print("  Synapse-Hub is the centralized skill hub, not an automation target project.")
            print("   Please specify a target project: python tools/setup_project.py --target /path/to/target-project")
            sys.exit(1)
        return resolved

    env_dir = os.environ.get("TARGET_PROJECT_DIR")
    if env_dir and os.path.exists(env_dir):
        resolved_env = os.path.abspath(env_dir)
        if resolved_env.lower() == HUB_ROOT.lower():
            print(f"{RED}{BOLD}X [CWD CONFUSION GUARD] TARGET_PROJECT_DIR points to Synapse-Hub itself!{RESET}")
            sys.exit(1)
        return resolved_env

    cwd = os.path.abspath(os.getcwd())
    if cwd.lower() != HUB_ROOT.lower():
        return cwd

    print(f"{RED}{BOLD}X [CWD CONFUSION GUARD] Current working directory is Synapse-Hub!{RESET}")
    print("  You must run setup inside your target project folder or supply --target:")
    print("   python tools/setup_project.py --target <path_to_target_project>")
    sys.exit(1)


def detect_tech_stack(target_dir):
    """Detects target project automation framework and script language."""
    target_path = Path(target_dir)

    # 1. Katalon Studio check
    prj_files = list(target_path.glob("*.prj"))
    if prj_files or (target_path / "Keywords").is_dir() or (target_path / "Scripts").is_dir():
        prj_name = prj_files[0].stem if prj_files else target_path.name
        return {
            "name": prj_name,
            "framework": "Katalon Studio (Enterprise Web)",
            "language": "Groovy",
            "page_dir": "Keywords/pages",
            "test_dir": "Scripts",
            "run_cmd": "./tools/run_headless_kre.sh (or katalonc CLI)"
        }

    # 2. Playwright check
    if (target_path / "playwright.config.ts").exists() or (target_path / "playwright.config.js").exists():
        is_ts = (target_path / "playwright.config.ts").exists() or (target_path / "tsconfig.json").exists()
        return {
            "name": target_path.name,
            "framework": "Playwright Test",
            "language": "TypeScript" if is_ts else "JavaScript",
            "page_dir": "src/pages" if (target_path / "src" / "pages").exists() else "pages",
            "test_dir": "tests",
            "run_cmd": "npx playwright test --project=chromium"
        }

    # 3. Cypress check
    if (target_path / "cypress.config.ts").exists() or (target_path / "cypress.config.js").exists():
        return {
            "name": target_path.name,
            "framework": "Cypress E2E",
            "language": "TypeScript" if (target_path / "cypress.config.ts").exists() else "JavaScript",
            "page_dir": "cypress/pages",
            "test_dir": "cypress/e2e",
            "run_cmd": "npx cypress run --headless"
        }

    # 4. Pytest check
    if (target_path / "pytest.ini").exists() or list(target_path.glob("test_*.py")):
        return {
            "name": target_path.name,
            "framework": "Pytest",
            "language": "Python",
            "page_dir": "pages",
            "test_dir": "tests",
            "run_cmd": "pytest tests/ -v"
        }

    # Default fallback
    return {
        "name": target_path.name,
        "framework": "Enterprise Test Automation",
        "language": "TypeScript / Groovy",
        "page_dir": "pages",
        "test_dir": "tests",
        "run_cmd": "npm test"
    }


def ensure_project_ai_guide(target_dir, stack_info):
    """Generates PROJECT_AI_GUIDE.md tailored to the target project if missing."""
    guide_path = os.path.join(target_dir, "PROJECT_AI_GUIDE.md")
    if os.path.exists(guide_path):
        print(f"  [PASS] PROJECT_AI_GUIDE.md already exists: {guide_path}")
        return False

    template_path = os.path.join(TEMPLATES_DIR, "PROJECT_AI_GUIDE_TEMPLATE.md")
    content = ""
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = f"# PROJECT AI GUIDE: {stack_info['name']}\n\n## 1. General System Under Test\n"

    # Populate template placeholders with detected project metadata
    content = content.replace("[TARGET_PROJECT_NAME]", stack_info["name"])
    content = content.replace("[e.g., Enterprise Billing Platform / Customer Portal]", stack_info["name"])
    content = content.replace("[e.g., Playwright Test, Katalon Studio 10.x, Cypress, Selenium]", stack_info["framework"])
    content = content.replace("[e.g., TypeScript, Groovy, Python, JavaScript]", stack_info["language"])
    content = content.replace("src/pages/... or Keywords/pages/...", stack_info["page_dir"])
    content = content.replace("tests/e2e/... or Scripts/...", stack_info["test_dir"])
    content = content.replace("[e.g., npx playwright test --project=chromium --reporter=html,junit:results.xml]", stack_info["run_cmd"])

    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  {GREEN}[OK] Generated PROJECT_AI_GUIDE.md tailored to {stack_info['framework']}:{RESET} {guide_path}")
    return True


def install_git_pre_push_hook(target_dir):
    """
    Installs or appends an automated pre-push hook into target project's .git repository.
    Safely backs up any existing pre-push hook (e.g. Husky, Lefthook) to prevent side-effects.
    """
    git_dir = os.path.join(target_dir, ".git")
    if not os.path.isdir(git_dir):
        print("  [SKIP] Not a Git repository root (.git folder not found). Skipped Git Hook installation.")
        return False

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_file = os.path.join(hooks_dir, "pre-push")

    # Resolve pinned package version
    manifest_file = os.path.join(HUB_ROOT, "skills_manifest.json")
    pkg_ver = "2.2.2"
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                pkg_ver = json.load(f).get("version", pkg_ver)
        except Exception:
            pass

    verify_all_script = os.path.join(SCRIPT_DIR, "verify_all.py").replace("\\", "/")
    analyze_script = os.path.join(SCRIPT_DIR, "analyze_project.py").replace("\\", "/")

    hook_snippet = f"""
# --- Synapse-Hub Pre-Push Quality Gate (v{pkg_ver}) ---
echo "\\n[AI-GUARD] Running Pre-Push Verification (Quality Gates DoD)..."
# Prioritize local tool execution to run offline without network latency or registry dependency
if [ -f "{verify_all_script}" ]; then
    python3 "{verify_all_script}" || python "{verify_all_script}"
elif command -v agent-qa >/dev/null 2>&1; then
    agent-qa verify
elif command -v npx >/dev/null 2>&1; then
    npx --no-install synapse-hub verify 2>/dev/null || npx synapse-hub@{pkg_ver} verify
fi
if [ $? -ne 0 ]; then
    echo "\\n[AI-GUARD - REJECTED] Git Push aborted: Quality Gates verification failed!"
    echo "Please fix defects or run 'python tools/verify_all.py' locally before pushing.\\n"
    exit 1
fi

echo "[AI-GUARD - PASSED] Quality Gates satisfied. Syncing project health report..."
if [ -f "{analyze_script}" ]; then
    python3 "{analyze_script}" || python "{analyze_script}"
elif command -v agent-qa >/dev/null 2>&1; then
    agent-qa analyze
elif command -v npx >/dev/null 2>&1; then
    npx --no-install synapse-hub analyze 2>/dev/null || npx synapse-hub@{pkg_ver} analyze
fi
echo "[AI-GUARD - READY] Pushing to remote...\\n"
# --- End Synapse-Hub Quality Gate ---
"""

    try:
        if os.path.exists(hook_file):
            with open(hook_file, "r", encoding="utf-8", errors="ignore") as f:
                existing_content = f.read()

            if "Synapse-Hub" in existing_content or "synapse-hub" in existing_content:
                print(f"  {CYAN}[SKIP] Pre-Push Git Hook already present:{RESET} {hook_file}")
                return True

            # Safely backup existing hook (e.g. Husky, Lefthook)
            backup_file = f"{hook_file}.backup"
            shutil.copy2(hook_file, backup_file)
            print(f"  {YELLOW}[BACKUP] Existing pre-push hook backed up to:{RESET} {backup_file}")

            # Append non-destructively
            final_content = existing_content.rstrip() + "\n" + hook_snippet
        else:
            final_content = "#!/bin/sh\n" + hook_snippet

        with open(hook_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(final_content)

        # Attempt to make executable on Unix-like environments
        try:
            os.chmod(hook_file, 0o755)
        except Exception:
            pass

        print(f"  {GREEN}[OK] Configured automated Pre-Push Git Hook:{RESET} {hook_file} (pinned to v{pkg_ver})")
        return True
    except Exception as e:
        print(f"  ⚠️ Could not install Git hook: {e}")
        return False


def inject_antigravity_global_plugin():
    """
    Automatically injects Synapse-Hub into Antigravity's Global Plugin Directory
    (~/.gemini/config/plugins/synapse-hub).
    Ensures that running `npx synapse-hub setup` activates the 27 skills and 6 subagents
    globally across ALL projects in Google Antigravity.
    """
    try:
        plugins_dir = os.path.expanduser("~/.gemini/config/plugins")
        target_plugin_dir = os.path.join(plugins_dir, "synapse-hub")
        os.makedirs(target_plugin_dir, exist_ok=True)

        # 1. plugin.json
        src_plugin_json = os.path.join(HUB_ROOT, "plugin.json")
        dst_plugin_json = os.path.join(target_plugin_dir, "plugin.json")
        if os.path.exists(src_plugin_json):
            if not os.path.exists(dst_plugin_json) or not os.path.samefile(src_plugin_json, dst_plugin_json):
                shutil.copy2(src_plugin_json, dst_plugin_json)

        # 2. README.md
        src_readme = os.path.join(HUB_ROOT, "README.md")
        dst_readme = os.path.join(target_plugin_dir, "README.md")
        if os.path.exists(src_readme):
            if not os.path.exists(dst_readme) or not os.path.samefile(src_readme, dst_readme):
                shutil.copy2(src_readme, dst_readme)

        # Helper to sync directory (junction or copy)
        def sync_dir(src, dst):
            if not os.path.exists(src):
                return
            if os.path.exists(dst) and os.path.samefile(src, dst):
                return
            if os.path.islink(dst):
                try:
                    os.unlink(dst)
                except Exception:
                    pass
            if sys.platform == "win32":
                try:
                    import _winapi
                    if not os.path.exists(dst):
                        _winapi.CreateJunction(src, dst)
                        return
                except Exception:
                    pass
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.tmp"))

        sync_dir(os.path.join(HUB_ROOT, ".agents", "skills"), os.path.join(target_plugin_dir, "skills"))
        sync_dir(os.path.join(HUB_ROOT, ".agents", "agents"), os.path.join(target_plugin_dir, "agents"))
        sync_dir(os.path.join(HUB_ROOT, "tools"), os.path.join(target_plugin_dir, "tools"))

        # 3. Rules (AGENTS.md)
        dst_rules = os.path.join(target_plugin_dir, "rules")
        os.makedirs(dst_rules, exist_ok=True)
        src_agents_md = os.path.join(HUB_ROOT, "AGENTS.md")
        dst_agents_md = os.path.join(dst_rules, "AGENTS.md")
        if os.path.exists(src_agents_md):
            if not os.path.exists(dst_agents_md) or not os.path.samefile(src_agents_md, dst_agents_md):
                shutil.copy2(src_agents_md, dst_agents_md)

        print(f"  {GREEN}[OK] Injected Antigravity Global Plugin:{RESET} {target_plugin_dir}")
        return True
    except Exception as e:
        print(f"  ⚠️ Antigravity Global Plugin notice: {e}")
        return False


def install_universal_ai_bridges(target_dir):
    """
    Deploys Universal AI Bridge configuration files into the target project workspace
    for seamless integration with Cursor, Claude Code, GitHub Copilot, and Windsurf.
    """
    bridges_dir = os.path.join(TEMPLATES_DIR, "ai_bridges")
    if not os.path.exists(bridges_dir):
        return False

    deployed = []

    # 1. Cursor (.cursor/rules/synapse-qa.mdc)
    cursor_dir = os.path.join(target_dir, ".cursor", "rules")
    os.makedirs(cursor_dir, exist_ok=True)
    src_cursor = os.path.join(bridges_dir, "cursor_synapse_qa.mdc")
    dst_cursor = os.path.join(cursor_dir, "synapse-qa.mdc")
    if os.path.exists(src_cursor):
        shutil.copy2(src_cursor, dst_cursor)
        deployed.append("Cursor (.cursor/rules/synapse-qa.mdc)")

    # 2. Claude Code (CLAUDE.md)
    dst_claude = os.path.join(target_dir, "CLAUDE.md")
    src_claude = os.path.join(bridges_dir, "CLAUDE.md")
    if os.path.exists(src_claude):
        if not os.path.exists(dst_claude):
            shutil.copy2(src_claude, dst_claude)
            deployed.append("Claude Code (CLAUDE.md)")
        else:
            with open(dst_claude, "r", encoding="utf-8", errors="ignore") as f:
                c_content = f.read()
            if "Synapse-Hub" not in c_content:
                with open(src_claude, "r", encoding="utf-8") as f:
                    append_data = f.read()
                with open(dst_claude, "a", encoding="utf-8") as f:
                    f.write("\n\n" + append_data)
                deployed.append("Claude Code (appended to CLAUDE.md)")

    # 3. GitHub Copilot (.github/copilot-instructions.md)
    github_dir = os.path.join(target_dir, ".github")
    os.makedirs(github_dir, exist_ok=True)
    dst_copilot = os.path.join(github_dir, "copilot-instructions.md")
    src_copilot = os.path.join(bridges_dir, "copilot-instructions.md")
    if os.path.exists(src_copilot):
        if not os.path.exists(dst_copilot):
            shutil.copy2(src_copilot, dst_copilot)
            deployed.append("GitHub Copilot (.github/copilot-instructions.md)")
        else:
            with open(dst_copilot, "r", encoding="utf-8", errors="ignore") as f:
                cp_content = f.read()
            if "Synapse-Hub" not in cp_content:
                with open(src_copilot, "r", encoding="utf-8") as f:
                    append_data = f.read()
                with open(dst_copilot, "a", encoding="utf-8") as f:
                    f.write("\n\n" + append_data)
                deployed.append("GitHub Copilot (appended to copilot-instructions.md)")

    # 4. Windsurf (.windsurfrules)
    dst_windsurf = os.path.join(target_dir, ".windsurfrules")
    src_windsurf = os.path.join(bridges_dir, "windsurfrules")
    if os.path.exists(src_windsurf):
        if not os.path.exists(dst_windsurf):
            shutil.copy2(src_windsurf, dst_windsurf)
            deployed.append("Windsurf (.windsurfrules)")
        else:
            with open(dst_windsurf, "r", encoding="utf-8", errors="ignore") as f:
                w_content = f.read()
            if "Synapse-Hub" not in w_content:
                with open(src_windsurf, "r", encoding="utf-8") as f:
                    append_data = f.read()
                with open(dst_windsurf, "a", encoding="utf-8") as f:
                    f.write("\n\n" + append_data)
                deployed.append("Windsurf (appended to .windsurfrules)")

    if deployed:
        print(f"  {GREEN}[OK] Deployed Universal AI Bridges:{RESET} {', '.join(deployed)}")
    return True


def uninstall_setup(target_repo: str) -> int:
    """Safely reverts and removes files installed by setup_project in the target repo."""
    print(f"\n{BOLD}{YELLOW}======================================================================{RESET}")
    print(f"{BOLD}{YELLOW}          SYNAPSE HUB — REVERT & UNINSTALL SETUP                      {RESET}")
    print(f"{BOLD}{YELLOW}======================================================================{RESET}")
    print(f"Target Repository: {target_repo}")

    reverted_items = 0

    # 1. Remove PROJECT_AI_GUIDE.md
    guide_file = os.path.join(target_repo, "PROJECT_AI_GUIDE.md")
    if os.path.exists(guide_file):
        os.remove(guide_file)
        print(f"  {GREEN}[REMOVED]{RESET} {guide_file}")
        reverted_items += 1

    # 2. Restore/Remove Git Pre-Push Hook
    hook_file = os.path.join(target_repo, ".git", "hooks", "pre-push")
    backup_file = os.path.join(target_repo, ".git", "hooks", "pre-push.bak")
    if os.path.exists(backup_file):
        if os.path.exists(hook_file):
            os.remove(hook_file)
        shutil.move(backup_file, hook_file)
        print(f"  {GREEN}[RESTORED]{RESET} Restored original pre-push hook from backup")
        reverted_items += 1
    elif os.path.exists(hook_file):
        with open(hook_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "Synapse-Hub" in content or "synapse-hub" in content:
            os.remove(hook_file)
            print(f"  {GREEN}[REMOVED]{RESET} Cleaned Synapse-Hub pre-push hook")
            reverted_items += 1

    # 3. Remove Cursor rule
    cursor_rule = os.path.join(target_repo, ".cursor", "rules", "synapse-qa.mdc")
    if os.path.exists(cursor_rule):
        os.remove(cursor_rule)
        print(f"  {GREEN}[REMOVED]{RESET} {cursor_rule}")
        reverted_items += 1

    # 4. Remove Copilot instruction
    copilot_file = os.path.join(target_repo, ".github", "copilot-instructions.md")
    if os.path.exists(copilot_file):
        os.remove(copilot_file)
        print(f"  {GREEN}[REMOVED]{RESET} {copilot_file}")
        reverted_items += 1

    # 5. Remove Windsurf rules
    windsurf_file = os.path.join(target_repo, ".windsurfrules")
    if os.path.exists(windsurf_file):
        os.remove(windsurf_file)
        print(f"  {GREEN}[REMOVED]{RESET} {windsurf_file}")
        reverted_items += 1

    print(f"\n{GREEN}✅ Uninstall complete! Cleaned {reverted_items} configuration files/hooks.{RESET}\n")
    return 0


def run_setup(target_repo, dry_run=False, profile="full"):
    """Main execution entrypoint for automated project setup."""
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      AUTONOMOUS ZERO-COMMAND PROJECT BOOTSTRAP (AI-READY SETUP)     {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"📁 Target Project  : {target_repo}")
    print(f"🎯 Selected Profile: {BOLD}{profile.upper()}{RESET}")
    if dry_run:
        print(f"Operational Mode   : {YELLOW}DRY-RUN (Simulating without modifying files on disk){RESET}\n")
    else:
        print(f"Operational Mode   : APPLY CHANGES\n")

    # 1. Detect Stack
    stack_info = detect_tech_stack(target_repo)
    print(f"🔍 Detected Stack  : {BOLD}{stack_info['framework']}{RESET} ({stack_info['language']})")
    print(f"📂 Structure Scope : Pages: `{stack_info['page_dir']}` | Tests: `{stack_info['test_dir']}`\n")

    if dry_run:
        print(f"{YELLOW}[DRY-RUN PREVIEW]{RESET}")
        print(f"  • Profile: {profile.upper()}")
        print(f"  • Would generate: {os.path.join(target_repo, 'PROJECT_AI_GUIDE.md')}")
        print(f"  • Would deploy AI bridges: .cursor/rules/synapse-qa.mdc, .github/copilot-instructions.md, .windsurfrules")
        print(f"  • Would install pre-push hook: {os.path.join(target_repo, '.git', 'hooks', 'pre-push')}")
        print(f"  • Would initialize: Central Agent Memory (~/.agent_memory/global_cache.db)")
        print(f"\n{GREEN}✅ Dry-run completed successfully. Zero changes written to disk.{RESET}\n")
        return 0

    # 2. Ensure PROJECT_AI_GUIDE.md & PROJECT_STATE.md
    print(f"{BOLD}[1/5] Checking Project AI Guide & State Anchor...{RESET}")
    guide_created = ensure_project_ai_guide(target_repo, stack_info)
    project_state.init_state(target_repo)

    # 3. Deploy Universal AI Bridges (Cursor, Claude Code, GitHub Copilot, Windsurf)
    print(f"\n{BOLD}[2/5] Deploying Universal AI Bridges (Cursor, Claude, Copilot, Windsurf)...{RESET}")
    bridges_deployed = install_universal_ai_bridges(target_repo)

    # 4. Inject Antigravity Global Plugin
    print(f"\n{BOLD}[3/5] Injecting Antigravity Global Plugin (~/.gemini/config/plugins)...{RESET}")
    plugin_injected = inject_antigravity_global_plugin()

    # 4.1 Initialize Central Agent Memory (SQLite Cache)
    try:
        import cache_resolver
        cache_resolver.init_db(seed=True)
        print(f"  {GREEN}[OK] Initialized Central Agent Memory (SQLite):{RESET} ~/.agent_memory/global_cache.db")
    except Exception as e:
        print(f"  ⚠️ Could not initialize memory cache: {e}")

    # 5. Install Pre-Push Git Hook
    print(f"\n{BOLD}[4/5] Installing Zero-Leakage Git Pre-Push Hook...{RESET}")
    hook_installed = install_git_pre_push_hook(target_repo)

    # 6. Run 5-in-1 Comprehensive Health & AST Analysis
    print(f"\n{BOLD}[5/5] Executing Initial Health Audit & AST Mapping...{RESET}")
    analysis_code = analyze_project.run_full_analysis(target_repo)

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}            🎉 PROJECT IS NOW 100% AI-READY (LEVEL 5 SETUP)           {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Target Framework    : {stack_info['framework']}")
    print(f"  AI Project Guide    : {os.path.join(target_repo, 'PROJECT_AI_GUIDE.md')}")
    print(f"  Universal Bridges   : Cursor (.cursor/rules), Claude Code, Copilot, Windsurf")
    print(f"  Antigravity Plugin  : {'ACTIVE (~/.gemini/config/plugins/synapse-hub)' if plugin_injected else 'STANDALONE'}")
    print(f"  AST Method Map      : {os.path.join(target_repo, 'repo_map.txt')}")
    print(f"  Health Report       : {os.path.join(target_repo, 'PROJECT_HEALTH_REPORT.md')}")
    print(f"  Pre-Push Sentinel   : {'ACTIVE (.git/hooks/pre-push)' if hook_installed else 'MANUAL (No .git folder)'}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    return analysis_code


def main():
    parser = argparse.ArgumentParser(description="Autonomous Enterprise QA Project Setup")
    parser.add_argument("target", nargs="?", default=None, help="Target repository path to setup")
    parser.add_argument("--repo", "--path", dest="repo_path", default=None, help="Target repository path")
    parser.add_argument("--profile", default="full", choices=["core", "web-e2e", "api-perf", "full"], help="Skills profile to install (core, web-e2e, api-perf, full)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate setup actions without modifying disk")
    parser.add_argument("--uninstall", action="store_true", help="Revert and remove files installed by setup_project")
    args = parser.parse_args()

    try:
        target_repo = resolve_target_repo(cli_target=args.target, cli_repo=args.repo_path)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    if args.uninstall:
        return uninstall_setup(target_repo)

    return run_setup(target_repo, dry_run=args.dry_run, profile=args.profile)


if __name__ == "__main__":
    sys.exit(main())
