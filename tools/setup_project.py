#!/usr/bin/env python3
"""
Enterprise QA Autonomous Project Setup & Bootstrap Engine
----------------------------------------------------------
Transforms any target test project into an AI-Ready Enterprise Suite in 1-click.
Dispatched automatically by AI Agents (Zero-Command Protocol) or via 'agent-qa setup'.

Automated actions:
  1. Detects project tech stack (Katalon, Playwright, Cypress, Pytest).
  2. Generates tailored 'PROJECT_AI_GUIDE.md' if missing.
  3. Installs automated Git Pre-Push Hook (.git/hooks/pre-push) for zero-leakage protection.
  4. Triggers 5-in-1 Health Audit (tools/analyze_project.py):
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
    """Installs an automated pre-push hook into target project's .git repository."""
    git_dir = os.path.join(target_dir, ".git")
    if not os.path.isdir(git_dir):
        print("  [SKIP] Not a Git repository root (.git folder not found). Skipped Git Hook installation.")
        return False

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_file = os.path.join(hooks_dir, "pre-push")

    verify_all_script = os.path.join(SCRIPT_DIR, "verify_all.py").replace("\\", "/")
    analyze_script = os.path.join(SCRIPT_DIR, "analyze_project.py").replace("\\", "/")

    hook_content = f"""#!/bin/sh
# Automated Zero-Leakage Pre-Push Hook (Installed by Synapse-Hub)
# Enforces 8 Quality Gates DoD and syncs project intelligence before pushing.

echo "\\n[AI-GUARD] Running Pre-Push Verification (8 Quality Gates DoD)..."
if command -v npx >/dev/null 2>&1; then
    npx synapse-hub verify
elif [ -f "{verify_all_script}" ]; then
    python3 "{verify_all_script}" || python "{verify_all_script}"
fi
if [ $? -ne 0 ]; then
    echo "\\n[AI-GUARD - REJECTED] Git Push aborted: Quality Gates verification failed!"
    echo "Please fix defects or run 'npx synapse-hub verify' locally before pushing.\\n"
    exit 1
fi

echo "[AI-GUARD - PASSED] 8 Quality Gates satisfied. Syncing project health report..."
if command -v npx >/dev/null 2>&1; then
    npx synapse-hub analyze
elif [ -f "{analyze_script}" ]; then
    python3 "{analyze_script}" || python "{analyze_script}"
fi
echo "[AI-GUARD - READY] Pushing to remote...\\n"
exit 0
"""
    try:
        with open(hook_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_content)

        # Attempt to make executable on Unix-like environments
        try:
            os.chmod(hook_file, 0o755)
        except Exception:
            pass

        print(f"  {GREEN}[OK] Installed automated Pre-Push Git Hook:{RESET} {hook_file}")
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


def run_setup(target_repo):
    """Main execution entrypoint for automated project setup."""
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      AUTONOMOUS ZERO-COMMAND PROJECT BOOTSTRAP (AI-READY SETUP)     {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"📁 Target Project  : {target_repo}")

    # 1. Detect Stack
    stack_info = detect_tech_stack(target_repo)
    print(f"🔍 Detected Stack  : {BOLD}{stack_info['framework']}{RESET} ({stack_info['language']})")
    print(f"📂 Structure Scope : Pages: `{stack_info['page_dir']}` | Tests: `{stack_info['test_dir']}`\n")

    # 2. Ensure PROJECT_AI_GUIDE.md & PROJECT_STATE.md
    print(f"{BOLD}[1/4] Checking Project AI Guide & State Anchor...{RESET}")
    guide_created = ensure_project_ai_guide(target_repo, stack_info)
    project_state.init_state(target_repo)

    # 3. Inject Antigravity Global Plugin
    print(f"\n{BOLD}[2/4] Injecting Antigravity Global Plugin (~/.gemini/config/plugins)...{RESET}")
    plugin_injected = inject_antigravity_global_plugin()

    # 3.1 Initialize Central Agent Memory (SQLite Cache)
    try:
        import cache_resolver
        cache_resolver.init_db(seed=True)
        print(f"  {GREEN}[OK] Initialized Central Agent Memory (SQLite):{RESET} ~/.agent_memory/global_cache.db")
    except Exception as e:
        print(f"  ⚠️ Could not initialize memory cache: {e}")

    # 4. Install Pre-Push Git Hook
    print(f"\n{BOLD}[3/4] Installing Zero-Leakage Git Pre-Push Hook...{RESET}")
    hook_installed = install_git_pre_push_hook(target_repo)

    # 5. Run 5-in-1 Comprehensive Health & AST Analysis
    print(f"\n{BOLD}[4/4] Executing Initial Health Audit & AST Mapping...{RESET}")
    analysis_code = analyze_project.run_full_analysis(target_repo)

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}            🎉 PROJECT IS NOW 100% AI-READY (LEVEL 5 SETUP)           {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Target Framework    : {stack_info['framework']}")
    print(f"  AI Project Guide    : {os.path.join(target_repo, 'PROJECT_AI_GUIDE.md')}")
    print(f"  AST Method Map      : {os.path.join(target_repo, 'repo_map.txt')}")
    print(f"  Health Report       : {os.path.join(target_repo, 'PROJECT_HEALTH_REPORT.md')}")
    print(f"  Pre-Push Sentinel   : {'ACTIVE (.git/hooks/pre-push)' if hook_installed else 'MANUAL (No .git folder)'}")
    print(f"  Antigravity Plugin  : {'ACTIVE (~/.gemini/config/plugins/synapse-hub)' if plugin_injected else 'STANDALONE'}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    return analysis_code


def main():
    parser = argparse.ArgumentParser(description="Autonomous Enterprise QA Project Setup")
    parser.add_argument("target", nargs="?", default=None, help="Target repository path to setup")
    parser.add_argument("--repo", "--path", dest="repo_path", default=None, help="Target repository path")
    args = parser.parse_args()

    try:
        target_repo = resolve_target_repo(cli_target=args.target, cli_repo=args.repo_path)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    return run_setup(target_repo)


if __name__ == "__main__":
    sys.exit(main())
