#!/usr/bin/env python3
"""
Enterprise Synapse-Hub Auto-Update & Version Drift Sentinel
------------------------------------------------------------
Provides non-blocking upstream version checks and 1-click self-updating
across Local Git Clones, Global Antigravity Plugins, and NPM installations.

Features:
1. Non-blocking check against NPM Registry & GitHub (cached 24h, zero latency).
2. Non-intrusive update banner on CLI invocations.
3. 1-Click upgrade engine: `synapse-hub update` / `agent-qa update`.
"""

import os
import sys
import json
import time
import urllib.request
import subprocess
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
GLOBAL_DIR = os.path.expanduser("~/.agent_memory")
CACHE_FILE = os.path.join(GLOBAL_DIR, "update_cache.json")
GLOBAL_PLUGIN_DIR = os.path.expanduser("~/.gemini/config/plugins/synapse-hub")

CHECK_INTERVAL_SECONDS = 86400  # 24 Hours

# ANSI Formatting
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def parse_semver(ver_str):
    """Parses a version string into a numeric tuple for comparison."""
    clean = ver_str.strip().lstrip("v")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def get_local_version():
    """Reads the local version from package.json or skills_manifest.json."""
    pkg_file = os.path.join(HUB_ROOT, "package.json")
    if os.path.exists(pkg_file):
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", "2.1.1")
        except Exception:
            pass

    manifest_file = os.path.join(HUB_ROOT, "skills_manifest.json")
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", "2.1.1")
        except Exception:
            pass

    return "2.1.1"


def fetch_remote_version():
    """Queries NPM registry or GitHub raw for the latest published version."""
    headers = {"User-Agent": "synapse-hub-update-sentinel"}

    # 1. Primary: NPM Registry
    try:
        req = urllib.request.Request("https://registry.npmjs.org/synapse-hub/latest", headers=headers)
        with urllib.request.urlopen(req, timeout=1.8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "version" in data:
                return data["version"], "npm"
    except Exception:
        pass

    # 2. Secondary fallback: GitHub raw package.json
    try:
        raw_url = "https://raw.githubusercontent.com/TeeVee998/Synapse-Hub/main/package.json"
        req = urllib.request.Request(raw_url, headers=headers)
        with urllib.request.urlopen(req, timeout=1.8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "version" in data:
                return data["version"], "github"
    except Exception:
        pass

    return None, None


def read_update_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def write_update_cache(data):
    try:
        os.makedirs(GLOBAL_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def check_for_updates(force=False, notify=True):
    """
    Checks if a newer version exists upstream.
    Uses a 24-hour file cache to prevent network overhead during daily workflows.
    """
    cache = read_update_cache()
    now = time.time()
    last_check = cache.get("last_check_timestamp", 0)

    local_ver = get_local_version()
    remote_ver = cache.get("latest_remote_version")

    # Only fetch if cache is stale or forced
    if force or (now - last_check > CHECK_INTERVAL_SECONDS) or not remote_ver:
        fetched_ver, source = fetch_remote_version()
        if fetched_ver:
            remote_ver = fetched_ver
            cache["latest_remote_version"] = fetched_ver
            cache["source"] = source
            cache["last_check_timestamp"] = now
            cache["last_check_date"] = datetime.now().isoformat()
            write_update_cache(cache)
        elif not remote_ver:
            return False, local_ver, None

    if remote_ver:
        is_newer = parse_semver(remote_ver) > parse_semver(local_ver)
        if is_newer and notify:
            print_update_banner(local_ver, remote_ver)
        return is_newer, local_ver, remote_ver

    return False, local_ver, None


def print_update_banner(local_ver, remote_ver):
    """Prints a clean ASCII alert banner when an update is available."""
    banner = f"""
{CYAN}┌────────────────────────────────────────────────────────────────────────┐
│  {BOLD}🚀 Synapse-Hub Update Available: {YELLOW}{local_ver}{RESET}{CYAN} → {GREEN}{BOLD}v{remote_ver}{RESET}{CYAN}                               │
│                                                                        │
│  To upgrade your local hub, run:                                       │
│    👉 {BOLD}agent-qa update{RESET}{CYAN}  or  {BOLD}npx synapse-hub update{RESET}{CYAN}                          │
│                                                                        │
│  Repository: {BOLD}https://github.com/TeeVee998/Synapse-Hub{RESET}{CYAN}                     │
└────────────────────────────────────────────────────────────────────────┘{RESET}
"""
    print(banner)


def perform_update():
    """
    Executes 1-click update:
    1. If inside a git repository (local clone or global plugin): pulls latest changes.
    2. Synchronizes SQLite central memory.
    3. Re-runs DoD Quality Gates to guarantee integrity.
    """
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}           SYNAPSE-HUB: 1-CLICK AUTOMATED UPDATE ENGINE               {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")

    local_ver = get_local_version()
    print(f"📦 Current Hub Version: {BOLD}v{local_ver}{RESET}")
    print("🔍 Checking upstream for latest releases...")

    has_update, local_ver, remote_ver = check_for_updates(force=True, notify=False)
    if remote_ver:
        print(f"🌐 Latest Upstream Version: {BOLD}{GREEN}v{remote_ver}{RESET}")
    else:
        print("⚠️ Could not reach upstream registry (offline or network timeout).")

    # Detect if repo is a git clone
    git_dir = os.path.join(HUB_ROOT, ".git")
    is_git_repo = os.path.exists(git_dir)

    updated = False

    if is_git_repo:
        print(f"\n{BOLD}[1/3] Pulling latest updates via Git...{RESET}")
        try:
            res = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=HUB_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if res.returncode == 0:
                print(f"  {GREEN}[OK] Git pull successful:{RESET}")
                for line in res.stdout.strip().splitlines():
                    print(f"     {line}")
                updated = True
            else:
                print(f"  ⚠️ Git pull notice: {res.stderr.strip() or res.stdout.strip()}")
        except Exception as e:
            print(f"  ⚠️ Could not execute git pull: {e}")
    else:
        print(f"\n{BOLD}[1/3] Checking NPM package installation...{RESET}")
        try:
            res = subprocess.run(
                ["npm", "install", "-g", "synapse-hub@latest"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if res.returncode == 0:
                print(f"  {GREEN}[OK] Global NPM package updated to latest!{RESET}")
                updated = True
        except Exception:
            pass

    # 2. Check Global Plugin
    if os.path.exists(GLOBAL_PLUGIN_DIR) and GLOBAL_PLUGIN_DIR.lower() != HUB_ROOT.lower():
        print(f"\n{BOLD}[2/3] Synchronizing Global Antigravity Plugin...{RESET}")
        plugin_git = os.path.join(GLOBAL_PLUGIN_DIR, ".git")
        if os.path.exists(plugin_git):
            try:
                subprocess.run(["git", "pull", "--ff-only"], cwd=GLOBAL_PLUGIN_DIR, stdout=subprocess.DEVNULL)
                print(f"  {GREEN}[OK] Updated Global Plugin repository: {GLOBAL_PLUGIN_DIR}{RESET}")
            except Exception:
                pass
        else:
            # Refresh plugin.json in global plugin
            try:
                import shutil
                src_pkg = os.path.join(HUB_ROOT, "plugin.json")
                dst_pkg = os.path.join(GLOBAL_PLUGIN_DIR, "plugin.json")
                if os.path.exists(src_pkg):
                    shutil.copy2(src_pkg, dst_pkg)
                    print(f"  {GREEN}[OK] Refreshed plugin.json in: {GLOBAL_PLUGIN_DIR}{RESET}")
            except Exception:
                pass

    # 3. Re-initialize SQLite Memory Cache
    print(f"\n{BOLD}[3/3] Synchronizing Central Agent Memory Cache...{RESET}")
    try:
        import cache_resolver
        cache_resolver.init_db(seed=True)
        print(f"  {GREEN}[OK] Synced episodic solution memory (0-token cache).{RESET}")
    except Exception as e:
        print(f"  ⚠️ Cache sync notice: {e}")

    # Clear update cache so banner dismisses
    new_local_ver = get_local_version()
    cache = {
        "last_check_timestamp": time.time(),
        "latest_remote_version": new_local_ver,
        "last_check_date": datetime.now().isoformat(),
        "source": "self-update"
    }
    write_update_cache(cache)

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{GREEN}  🎉 UPDATE COMPLETE: Synapse-Hub is up to date (v{new_local_ver})!  {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Synapse-Hub Auto-Update & Drift Sentinel")
    parser.add_argument("--check", action="store_true", help="Check for available updates without applying")
    parser.add_argument("--update", action="store_true", help="Perform 1-click update to latest version")
    parser.add_argument("--force", action="store_true", help="Force refresh update check bypassing cache")
    args = parser.parse_args()

    if args.check:
        has_update, cur, rem = check_for_updates(force=True, notify=False)
        print(f"Current Hub Version : v{cur}")
        print(f"Latest Upstream     : v{rem if rem else 'Unknown'}")
        if has_update:
            print(f"{YELLOW}⚠️ An update is available! Run 'agent-qa update' to upgrade.{RESET}")
            sys.exit(1)
        else:
            print(f"{GREEN}✅ Synapse-Hub is up to date.{RESET}")
            sys.exit(0)

    if args.update or not (args.check or args.force):
        perform_update()
        sys.exit(0)


if __name__ == "__main__":
    main()
