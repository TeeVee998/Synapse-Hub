#!/usr/bin/env python3
"""
Enterprise Repository Map Compressor (Inspired by Aider-AI/aider)
-----------------------------------------------------------
Extracts an ultra-compact, token-budgeted AST map of all Page Classes and Helpers.
Compresses hundreds of kilobytes of Groovy source code into a clean ~150-line summary.
Enables AI Agents to discover all available methods and signatures with < 600 tokens.
Supports dynamic target repository resolution (CLI flag, CWD auto-detect, ENV var).
Saves a persistent in-place copy (repo_map.txt) inside the target project directory.
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_TXT = os.path.join(SCRIPT_DIR, "repo_map.txt")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "repo_map.json")

# Regex patterns for Groovy classes and methods
CLASS_PATTERN = re.compile(r'^\s*(?:public\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', re.MULTILINE)
METHOD_PATTERN = re.compile(
    r'^\s*(?:@\w+\s+)*(?:public\s+|protected\s+|private\s+)?(?:static\s+)?(?:def\s+|void\s+|[\w<>\[\],]+\s+)?(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s]+)?\s*\{',
    re.MULTILINE
)
DOC_PATTERN = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)


def resolve_target_repo(cli_target=None, cli_repo=None):
    """
    Resolves the target repository path for repo mapping:
    1. Explicit CLI flag: --repo / --path or positional target.
    2. Environment variable: TARGET_PROJECT_DIR.
    3. Current Working Directory (if different from Hub and has Keywords/ or Scripts/).
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
        if os.path.exists(os.path.join(cwd, "Keywords")) or os.path.exists(os.path.join(cwd, "Scripts")):
            return cwd

    return HUB_ROOT


def extract_class_info(file_path, repo_root=None):
    """Parses a Groovy file and extracts class name, parent, and exported methods."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    base_root = repo_root or HUB_ROOT
    try:
        rel_path = os.path.relpath(file_path, base_root)
    except ValueError:
        rel_path = os.path.abspath(file_path)

    class_match = CLASS_PATTERN.search(content)
    if not class_match:
        return None

    class_name = class_match.group(1)
    extends_name = class_match.group(2) or ""

    methods = []
    control_keywords = {"if", "for", "while", "switch", "catch", "synchronized"}

    lines = content.splitlines()
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("//") or line_clean.startswith("/*") or line_clean.startswith("*"):
            continue

        # If '=' appears before '(', it's a variable assignment / constant declaration, not a method
        if "=" in line_clean:
            eq_pos = line_clean.find("=")
            paren_pos = line_clean.find("(")
            if paren_pos != -1 and eq_pos < paren_pos:
                continue

        # Must have parentheses and end with '{' or next line starts with '{'
        if "(" in line_clean and ")" in line_clean:
            has_brace = line_clean.endswith("{") or (idx + 1 < len(lines) and lines[idx + 1].strip().startswith("{"))
            if has_brace:
                # Match method definition: modifiers + return type + name + (params)
                m = re.search(r'(?:public\s+|protected\s+|private\s+|static\s+|def\s+|void\s+|[\w<>\[\],]+\s+)+([a-zA-Z_]\w*)\s*\(([^)]*)\)', line_clean)
                if m:
                    name = m.group(1)
                    params = m.group(2).strip()
                    if name not in control_keywords and name != class_name:
                        # Extract preceding single-line comment if any
                        comment = ""
                        if idx > 0 and lines[idx - 1].strip().startswith("//"):
                            comment = lines[idx - 1].strip().lstrip("/ ").strip()
                        methods.append({
                            "name": name,
                            "params": re.sub(r'\s+', ' ', params),
                            "comment": comment
                        })

    # Deduplicate methods preserving order
    seen = set()
    unique_methods = []
    for meth in methods:
        sig = f"{meth['name']}({meth['params']})"
        if sig not in seen:
            seen.add(sig)
            unique_methods.append(meth)

    return {
        "rel_path": rel_path,
        "class_name": class_name,
        "extends": extends_name,
        "raw_size_bytes": len(content.encode("utf-8")),
        "line_count": len(lines),
        "methods": unique_methods
    }


def build_repo_map(target_repo=None, output_txt=None, output_json=None):
    """Scans Keywords in target_repo and builds the condensed repo map."""
    repo = target_repo or resolve_target_repo()
    txt_dest = output_txt or OUTPUT_TXT
    json_dest = output_json or OUTPUT_JSON

    classes = []
    total_raw_bytes = 0
    total_raw_lines = 0

    keywords_dir = os.path.join(repo, "Keywords")

    if os.path.isdir(keywords_dir):
        for root, dirs, files in os.walk(keywords_dir):
            for fname in sorted(files):
                if fname.endswith(".groovy"):
                    full_path = os.path.join(root, fname)
                    info = extract_class_info(full_path, repo_root=repo)
                    if info:
                        classes.append(info)
                        total_raw_bytes += info["raw_size_bytes"]
                        total_raw_lines += info["line_count"]

    # Sort classes: BasePage first, then alphabetical
    classes.sort(key=lambda c: (0 if c["class_name"] == "BasePage" else 1, c["class_name"]))

    # Render text map
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_lines = [
        f"# ==============================================================================",
        f"# ENTERPRISE AUTOMATION REPOSITORY MAP (Aider-Style AST Compression)",
        f"# Generated : {timestamp}",
        f"# Target    : {repo}",
        f"# Scope     : {len(classes)} Classes ({total_raw_lines} source lines, {total_raw_bytes / 1024:.1f} KB)",
        f"# Purpose   : Token-budgeted index (< 600 tokens) for instant method lookup",
        f"# ==============================================================================\n"
    ]

    total_methods = 0
    for cls in classes:
        ext_str = f" extends {cls['extends']}" if cls['extends'] else ""
        out_lines.append(f"{cls['rel_path']} ({cls['line_count']} lines)")
        out_lines.append(f"  class {cls['class_name']}{ext_str}:")
        for m in cls["methods"]:
            total_methods += 1
            cmt = f" # {m['comment']}" if m['comment'] else ""
            out_lines.append(f"    def {m['name']}({m['params']}){cmt}")
        out_lines.append("")

    rendered_text = "\n".join(out_lines)
    compressed_bytes = len(rendered_text.encode("utf-8"))
    ratio = (1.0 - (compressed_bytes / max(1, total_raw_bytes))) * 100
    est_tokens = len(rendered_text) // 4

    # 1. Save to primary destination (tools/repo_map.txt in Hub)
    os.makedirs(os.path.dirname(txt_dest), exist_ok=True)
    with open(txt_dest, "w", encoding="utf-8") as f:
        f.write(rendered_text)

    os.makedirs(os.path.dirname(json_dest), exist_ok=True)
    with open(json_dest, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": timestamp,
            "target_repository": repo,
            "classes_count": len(classes),
            "methods_count": total_methods,
            "source_lines": total_raw_lines,
            "raw_bytes": total_raw_bytes,
            "compressed_bytes": compressed_bytes,
            "compression_ratio_pct": round(ratio, 2),
            "estimated_tokens": est_tokens,
            "classes": classes
        }, f, indent=2, ensure_ascii=False)

    # 2. Save a persistent copy directly into target repository root (for AI self-contained inspection)
    if os.path.abspath(repo).lower() != os.path.abspath(HUB_ROOT).lower():
        try:
            target_txt = os.path.join(repo, "repo_map.txt")
            with open(target_txt, "w", encoding="utf-8") as f:
                f.write(rendered_text)
            target_json = os.path.join(repo, "repo_map.json")
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump({
                    "generated_at": timestamp,
                    "target_repository": repo,
                    "classes_count": len(classes),
                    "methods_count": total_methods,
                    "source_lines": total_raw_lines,
                    "raw_bytes": total_raw_bytes,
                    "compressed_bytes": compressed_bytes,
                    "compression_ratio_pct": round(ratio, 2),
                    "estimated_tokens": est_tokens,
                    "classes": classes
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    return {
        "target_repo": repo,
        "classes_count": len(classes),
        "methods_count": total_methods,
        "source_lines": total_raw_lines,
        "raw_bytes": total_raw_bytes,
        "compressed_bytes": compressed_bytes,
        "compression_ratio_pct": ratio,
        "estimated_tokens": est_tokens,
        "output_file": txt_dest
    }


def main():
    parser = argparse.ArgumentParser(description="Enterprise Repository Map Compressor")
    parser.add_argument("target", nargs="?", default=None, help="Target repository containing Keywords/")
    parser.add_argument("--repo", "--path", dest="repo_path", default=None, help="Target repository path")
    parser.add_argument("--print", action="store_true", help="Print repository map to console")
    args = parser.parse_args()

    try:
        target_repo = resolve_target_repo(cli_target=args.target, cli_repo=args.repo_path)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    stats = build_repo_map(target_repo=target_repo)
    print(f"\n======================================================================")
    print(f"       Enterprise Repository Map Compressor (Aider-Style AST Map)           ")
    print(f"======================================================================")
    print(f"  Target Repository       : {stats['target_repo']}")
    print(f"  Indexed Classes         : {stats['classes_count']} Page Classes & Helpers")
    print(f"  Extracted Methods       : {stats['methods_count']} API signatures")
    print(f"  Source Lines Processed  : {stats['source_lines']:,} lines ({stats['raw_bytes'] / 1024:.1f} KB)")
    print(f"  Compressed Map Size     : {stats['compressed_bytes'] / 1024:.1f} KB (~{stats['estimated_tokens']} tokens)")
    print(f"  Compression Ratio       : {stats['compression_ratio_pct']:.1f}% reduction")
    print(f"  Artifact Generated      : {stats['output_file']}")
    print(f"======================================================================\n")

    if args.print:
        with open(stats['output_file'], "r", encoding="utf-8") as f:
            print(f.read())

    return 0


if __name__ == "__main__":
    sys.exit(main())
