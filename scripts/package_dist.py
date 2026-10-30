#!/usr/bin/env python3
"""
Enterprise Agent-Skills Hub Distribution Packager
================================================
Packages the complete, clean repository into a release-ready zip file (agent-skills.zip).
Ensures 100% inclusion of all mandatory folders:
  - .agents/    (skills, rules, workflows, agents)
  - docs/       (ARCHITECTURE.md, CLI_REFERENCE.md, CONTRIBUTING.md)
  - scripts/    (install.ps1, setup.sh, lint_skills.ps1)
  - templates/  (PROJECT_AI_GUIDE_TEMPLATE.md)
  - tools/      (all CLI tools and utilities)
  - root configs (README.md, AGENTS.md, pyproject.toml, requirements.txt, skills_manifest.json)

Excludes ephemeral clutter (.git, .venv, __pycache__, reports, temp files).
"""

import os
import sys
import zipfile
from pathlib import Path

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "agent_qa.egg-info",
    "archive",
    "reports",
    "graphify-out",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp",
    ".zip",
}

MANDATORY_CHECKS = [
    "docs/ARCHITECTURE.md",
    "docs/CLI_REFERENCE.md",
    "scripts/install.ps1",
    "scripts/setup.sh",
    "templates/PROJECT_AI_GUIDE_TEMPLATE.md",
    "templates/PROJECT_STATE_TEMPLATE.md",
    "templates/ai_bridges/cursor_synapse_qa.mdc",
    "templates/ai_bridges/CLAUDE.md",
    "templates/ai_bridges/copilot-instructions.md",
    "templates/ai_bridges/windsurfrules",
    "README.md",
    "AGENTS.md",
    "package.json",
    "bin/agent-qa.js",
    "tools/infer_linter.py",
    "tools/verify_all.py",
    "tools/analyze_project.py",
    "tools/setup_project.py",
    "tools/auto_heal.py",
    "tools/project_state.py",
    "tools/safety_firewall.py",
    "tools/api_drift_sentinel.py",
    "tools/mcp_server.py",
    "tools/micro_mutator.py",
    "tools/heal_pr_automator.py",
    "tools/matrix_sharder.py",
    "tools/browser_helpers.js",
    "tools/config_decoupler.py",
    "tools/omni_emitter.py",
    "tools/omni_parser.py",
    "tools/omni_transpiler.py",
    "tools/universal_ir.py",
]


def generate_spec_file() -> Path:
    """Generates the enterprise PyInstaller spec file (omni-qc.spec) for Single-Binary distribution."""
    spec_path = REPO_ROOT / "omni-qc.spec"
    spec_content = """# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None
repo_root = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(repo_root, 'tools'), 'tools'),
    (os.path.join(repo_root, '.agents'), '.agents'),
    (os.path.join(repo_root, 'templates'), 'templates'),
    (os.path.join(repo_root, 'skills_manifest.json'), '.'),
]

hiddenimports = [
    'sqlite3',
    'json',
    'math',
    're',
    'dataclasses',
    'enum',
    'typing',
    'collections',
    'argparse',
    'pathlib',
    'subprocess',
    'tempfile',
    'tools.universal_ir',
    'tools.omni_parser',
    'tools.omni_emitter',
    'tools.omni_transpiler',
    'tools.config_decoupler',
    'tools.cache_resolver',
    'tools.auto_heal',
    'tools.micro_mutator',
    'tools.verify_all',
]

a = Analysis(
    [os.path.join(repo_root, 'tools', 'cli.py')],
    pathex=[repo_root, os.path.join(repo_root, 'tools')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='omni-qc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    print(f"📄 Generated PyInstaller spec: {spec_path.name}")
    return spec_path


def build_binary() -> Path:
    """Builds the single-file binary executable (omni-qc.exe / omni-qc) via PyInstaller."""
    import subprocess
    import shutil

    spec_path = generate_spec_file()
    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    bat_path = dist_dir / "omni-qc.bat"
    bat_content = """@echo off
setlocal
set "SCRIPT_DIR=%~dp0.."
python "%SCRIPT_DIR%\\tools\\cli.py" %*
"""
    with open(bat_path, "w", encoding="utf-8") as bf:
        bf.write(bat_content)

    sh_path = dist_dir / "omni-qc"
    sh_content = """#!/usr/bin/env sh
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$SCRIPT_DIR/tools/cli.py" "$@"
"""
    with open(sh_path, "w", encoding="utf-8") as sf:
        sf.write(sh_content)
    try:
        os.chmod(sh_path, 0o755)
    except Exception:
        pass

    print("🔨 Checking for PyInstaller compilation toolchain...")
    pyinstaller_exe = shutil.which("pyinstaller")

    if pyinstaller_exe:
        print("⚡ Running PyInstaller single-file build...")
        cmd = [pyinstaller_exe, "--clean", "--noconfirm", str(spec_path)]
        res = subprocess.run(cmd, cwd=REPO_ROOT)
        if res.returncode == 0:
            exe_ext = ".exe" if sys.platform == "win32" else ""
            target_bin = dist_dir / f"omni-qc{exe_ext}"
            print(f"✅ [BINARY COMPILED] Single portable executable ready: {target_bin}")
            return target_bin
        else:
            print("⚠️ PyInstaller compilation failed. Falling back to portable distribution launcher.")
    else:
        print("💡 PyInstaller is not installed in the local environment.")
        print(f"✅ Generated portable launchers in {dist_dir}/ (omni-qc.bat & omni-qc).")
        print("👉 To compile full native binary: pip install pyinstaller && python scripts/package_dist.py --binary")

    return dist_dir / ("omni-qc.bat" if sys.platform == "win32" else "omni-qc")


def create_package(output_zip: str = "agent-skills.zip") -> Path:
    out_path = REPO_ROOT / output_zip
    print(f"📦 Packaging Enterprise Agent-Skills Hub into: {out_path.name}")
    print("=" * 60)

    total_files = 0
    total_size = 0

    with zipfile.ZipFile(out_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(REPO_ROOT):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".temp-")]

            rel_root = Path(root).relative_to(REPO_ROOT)
            if any(part in EXCLUDE_DIRS for part in rel_root.parts):
                continue

            for file_name in files:
                if any(file_name.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                if file_name == output_zip:
                    continue

                full_path = Path(root) / file_name
                rel_path = full_path.relative_to(REPO_ROOT)
                arc_name = rel_path.as_posix()

                zf.write(full_path, arcname=arc_name)
                total_files += 1
                total_size += full_path.stat().st_size

    zip_size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"✅ Packaging complete:")
    print(f"   • Total files packaged : {total_files}")
    print(f"   • Uncompressed size    : {total_size / (1024 * 1024):.2f} MB")
    print(f"   • Archive size (.zip)  : {zip_size_mb:.2f} MB")

    # Verify mandatory files
    print("\n🔍 Verifying mandatory files inside archive:")
    with zipfile.ZipFile(out_path, mode="r") as zf:
        namelist = set(zf.namelist())
        all_ok = True
        for chk in MANDATORY_CHECKS:
            if chk in namelist:
                print(f"   [PASS] {chk}")
            else:
                print(f"   [FAIL] Missing: {chk}")
                all_ok = False

    if not all_ok:
        print("\n❌ Error: Archive is missing critical files!")
        sys.exit(1)

    print(f"\n✨ Archive is 100% intact and ready for distribution: {out_path}")
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enterprise Hub Packager & Portable Binary Distribution")
    parser.add_argument("--zip", action="store_true", help="Package clean repository archive into agent-skills.zip")
    parser.add_argument("--binary", action="store_true", help="Build single-file portable executable (omni-qc)")
    parser.add_argument("--all", action="store_true", help="Build both ZIP distribution and portable binary")
    args = parser.parse_args()

    if args.binary:
        build_binary()
    elif args.all:
        create_package()
        build_binary()
    else:
        create_package()
