#!/usr/bin/env python3
"""
Omni-Transpiler & Repository Scanner
-----------------------------------
Connects OmniParser and OmniEmitter to provide:
  1. Instant 0-token transpilation between test automation frameworks.
  2. Recursive repo scanner that inventories Page Classes, Locators, and Test Cases
     across polyglot codebases (Java, Groovy, TS, Python, C#).
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

# Dynamic imports
try:
    from tools.universal_ir import ProjectIR, resolve_hermetic_fixtures, analyze_data_dependencies
    from tools.omni_parser import OmniParser
    from tools.omni_emitter import OmniEmitter
except ImportError:
    from universal_ir import ProjectIR, resolve_hermetic_fixtures, analyze_data_dependencies
    from omni_parser import OmniParser
    from omni_emitter import OmniEmitter


def transpile_file(
    source_path: str,
    target_framework: str,
    output_dir: Optional[str] = None,
    hermetic: bool = True
) -> Dict[str, str]:
    """Transpiles a single automation source file to the target framework."""
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")

    # 1. Parse source with 0-token deterministic parser
    project_ir = OmniParser.parse_file(source_path)

    # 2. Resolve data dependencies & inject hermetic pre-flight fixtures
    if hermetic:
        project_ir = resolve_hermetic_fixtures(project_ir)

    # 3. Emit target code
    emitted_files = OmniEmitter.emit(project_ir, target_framework)

    # 4. Write to disk if output_dir specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for rel_path, content in emitted_files.items():
            full_out_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_out_path), exist_ok=True)
            with open(full_out_path, "w", encoding="utf-8") as f:
                f.write(content)

    return emitted_files


def scan_repository(repo_path: str) -> Dict[str, Any]:
    """
    Recursively scans a repository and builds a unified polyglot inventory
    of all Page Objects, Locators, and Test Cases with 0 tokens.
    """
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Path does not exist: {repo_path}")

    inventory = {
        "repository": os.path.abspath(repo_path),
        "total_files_scanned": 0,
        "languages": {},
        "frameworks": {},
        "pages": [],
        "test_cases": [],
        "total_locators": 0,
        "total_methods": 0
    }

    test_extensions = {".java", ".ts", ".js", ".groovy", ".py", ".cs"}
    exclude_dirs = {"node_modules", ".git", ".gradle", "build", "target", "dist", ".gemini", "__pycache__"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in test_extensions:
                file_full = os.path.join(root, f)
                try:
                    p_ir = OmniParser.parse_file(file_full)
                    inventory["total_files_scanned"] += 1
                    
                    # Language counts
                    inventory["languages"][p_ir.source_language] = inventory["languages"].get(p_ir.source_language, 0) + 1
                    inventory["frameworks"][p_ir.source_framework] = inventory["frameworks"].get(p_ir.source_framework, 0) + 1

                    for p in p_ir.pages:
                        if p.locators or p.methods:
                            inventory["pages"].append({
                                "name": p.name,
                                "file": os.path.relpath(file_full, repo_path).replace("\\", "/"),
                                "locators_count": len(p.locators),
                                "methods_count": len(p.methods)
                            })
                            inventory["total_locators"] += len(p.locators)
                            inventory["total_methods"] += len(p.methods)

                    for tc in p_ir.test_cases:
                        inventory["test_cases"].append({
                            "id": tc.id,
                            "title": tc.title,
                            "file": os.path.relpath(file_full, repo_path).replace("\\", "/"),
                            "steps_count": len(tc.steps)
                        })
                except Exception:
                    pass

    return inventory


def main():
    parser = argparse.ArgumentParser(description="Omni-Transpiler & Polyglot Test Inventory Scanner")
    sub = parser.add_subparsers(dest="cmd")

    # transpile command
    p_trans = sub.add_parser("transpile", help="Transpile test files across languages and frameworks")
    p_trans.add_argument("source", help="Source file path")
    p_trans.add_argument("--to", required=True, choices=OmniEmitter.SUPPORTED_TARGETS, help="Target framework")
    p_trans.add_argument("--out", default=None, help="Output directory")
    p_trans.add_argument("--no-hermetic", action="store_true", help="Disable automatic hermetic data dependency resolution")

    # scan command
    p_scan = sub.add_parser("scan", help="Scan repository and build polyglot test inventory")
    p_scan.add_argument("path", default=".", nargs="?", help="Directory to scan")
    p_scan.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.cmd == "transpile":
        res = transpile_file(args.source, args.to, args.out, hermetic=not args.no_hermetic)
        print(f"✅ Successfully transpiled '{args.source}' -> {args.to} ({len(res)} files generated):")
        for p, code in res.items():
            print(f"  • {p} ({len(code.splitlines())} lines)")
            if not args.out:
                print("---")
                print(code)
                print("---")

    elif args.cmd == "scan":
        inv = scan_repository(args.path)
        if args.json:
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


if __name__ == "__main__":
    main()
