#!/usr/bin/env python3
"""
Enterprise QA: Fast XPath / Selector Lookup (lookup_xpath.py)
-------------------------------------------------------------
Fast lookup tool for XPaths and selectors from Page Class JSON specifications.
Enables AI Agents to retrieve only the relevant selectors (<300 tokens)
instead of reading entire selector repositories or rescanning live DOM.

Multi-tier Resolution:
  1. CLI Flag: python tools/lookup_xpath.py <query> --file <path_to_json> (-f)
  2. Environment variable: XPATH_DATA_FILE, SELECTORS_JSON, or LOCATORS_JSON
  3. Automatic discovery: selectors.json, locators.json, scraped_xpaths.json...
  4. Internal Hub archive fallback: archive/legacy_references/Enterprise_scraped_xpaths.json
"""

import sys
import json
import os
import argparse

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def resolve_json_path(cli_file=None):
    """Resolves Selector/XPath JSON file path via precedence order."""
    # 1. CLI flag
    if cli_file:
        if os.path.exists(cli_file):
            return os.path.abspath(cli_file)
        else:
            print(f"⚠️  Warning: File specified via --file '{cli_file}' does not exist.")

    # 2. Environment variable
    env_file = os.environ.get("XPATH_DATA_FILE") or os.environ.get("SELECTORS_JSON") or os.environ.get("LOCATORS_JSON")
    if env_file and os.path.exists(env_file):
        return os.path.abspath(env_file)

    # 3. Automatic discovery in CWD and common directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hub_root = os.path.abspath(os.path.join(script_dir, ".."))
    cwd = os.getcwd()

    search_dirs = [
        cwd,
        os.path.join(cwd, "references"),
        os.path.join(cwd, "data"),
        os.path.join(cwd, "tools"),
        os.path.join(cwd, "docs"),
        script_dir
    ]

    candidate_names = [
        "selectors.json",
        "scraped_xpaths.json",
        "locators.json",
        "Enterprise_scraped_xpaths.json",
        "page_selectors.json",
        "elements.json"
    ]

    for d in search_dirs:
        for name in candidate_names:
            candidate = os.path.join(d, name)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

    # 4. Hub Archive fallback
    for legacy_name in ["Enterprise_scraped_xpaths.json", "dmit_scraped_xpaths.json", "batch01_scraped_xpaths.json"]:
        legacy_file = os.path.join(hub_root, "archive", "legacy_references", legacy_name)
        if os.path.isfile(legacy_file):
            return os.path.abspath(legacy_file)

    return None


def normalize_selector_data(raw_data):
    """Normalizes Selector data across PageClass dictionary or flat list schemas."""
    if isinstance(raw_data, dict):
        return raw_data
    elif isinstance(raw_data, list):
        grouped = {}
        for item in raw_data:
            page = item.get("page") or item.get("page_class") or "GLOBAL"
            if page not in grouped:
                grouped[page] = []
            grouped[page].append(item)
        return grouped
    return {}


def main():
    parser = argparse.ArgumentParser(description="Fast Selector / XPath lookup from project JSON specifications")
    parser.add_argument("query", help="PageClass name or selector identifier keyword (e.g., TargetPlanPage, TXT_CODE)")
    parser.add_argument("-f", "--file", dest="file", help="Path to JSON file containing selector/xpaths")
    args = parser.parse_args()

    json_path = resolve_json_path(args.file)

    if not json_path:
        print("❌ Error: Selector / XPath JSON data file not found.")
        print("\n👉 Guidance to configure selector data for target project:")
        print("  1. Use CLI flag: python tools/lookup_xpath.py <query> --file <path_to_selectors.json>")
        print("  2. Set environment variable: export XPATH_DATA_FILE='path/to/selectors.json' (or set XPATH_DATA_FILE=...)")
        print("  3. Place 'selectors.json' in project root or declare path in PROJECT_AI_GUIDE.md")
        sys.exit(1)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file '{json_path}': {e}")
        sys.exit(1)

    data = normalize_selector_data(raw_data)
    query = args.query.strip()

    # 1. Match by Page Class name
    matched_page = None
    for page_name in data.keys():
        if query.lower() == page_name.lower():
            matched_page = page_name
            break

    if matched_page:
        selectors = data[matched_page]
        source_label = os.path.relpath(json_path, os.getcwd()) if os.path.exists(json_path) else json_path
        print(f"=== {matched_page} ({len(selectors)} selectors) [Source: {source_label}] ===")
        for item in selectors:
            c = item.get("constant") or item.get("name") or "SELECTOR"
            tag = item.get("tag") or "element"
            xp = item.get("xpath") or item.get("selector") or item.get("css") or ""
            print(f"- {c} ({tag}): {xp}")
        return

    # 2. Match keyword across constant or xpath
    found = []
    for page_name, selectors in data.items():
        if isinstance(selectors, list):
            for item in selectors:
                c = item.get("constant") or item.get("name") or ""
                xp = item.get("xpath") or item.get("selector") or item.get("css") or ""
                tag = item.get("tag") or "element"
                if query.lower() in c.lower() or query.lower() in xp.lower():
                    found.append((page_name, c, tag, xp))
        elif isinstance(selectors, dict):
            for c, xp in selectors.items():
                if query.lower() in c.lower() or query.lower() in str(xp).lower():
                    found.append((page_name, c, "element", str(xp)))

    if not found:
        print(f"No selectors found matching: '{query}' in file '{os.path.basename(json_path)}'")
        return

    source_label = os.path.relpath(json_path, os.getcwd()) if os.path.exists(json_path) else json_path
    print(f"=== Found {len(found)} selector(s) for query '{query}' [Source: {source_label}] ===")
    for page, c, tag, xp in found[:15]:
        print(f"[{page}] {c} ({tag}): {xp}")


if __name__ == "__main__":
    main()
