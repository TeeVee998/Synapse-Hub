#!/usr/bin/env python3
"""
Universal Test Impact Analyzer (Graphify AST-Powered)
---------------------------------------------------
Analyzes which Test Cases are directly or transitively impacted
when Page Classes or Helper classes are modified, saving CI/CD execution time.
Supports dynamic target repository resolution (CLI flag, CWD auto-detect, ENV var).

Usage:
  python3 tools/test_impact.py --file Keywords/pages/CommonCategoryPage.groovy
  python3 tools/test_impact.py --git-diff
  python3 tools/test_impact.py "D:/target-project" --git-diff
"""

import os
import sys
import json
import glob
import argparse
import subprocess

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))


def resolve_target_repo(cli_target=None, cli_repo=None):
    """
    Resolves the target repository path for test impact analysis:
    1. Explicit CLI flag: --repo / --path or positional target.
    2. Environment variable: TARGET_PROJECT_DIR.
    3. Current Working Directory (if different from Hub).
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
        return cwd

    return HUB_ROOT


def build_fallback_graph(repo_root):
    """
    Builds a lightweight in-memory AST/token dependency graph when graphify-out/graph.json is absent.
    Scans Keywords/ (or src/) for classes and Scripts/ (or tests/) for references.
    """
    nodes = []
    edges = []
    class_map = {}

    # 1. Scan Keywords / src classes
    class_files = []
    for ext in ("*.groovy", "*.java", "*.ts", "*.py"):
        for sub in ("Keywords", "src", "pages", "helpers"):
            for f in glob.glob(os.path.join(repo_root, sub, "**", ext), recursive=True):
                class_files.append(f)
                cls_name = os.path.splitext(os.path.basename(f))[0]
                rel_path = os.path.relpath(f, repo_root).replace("\\", "/")
                class_map[cls_name] = rel_path
                nodes.append({"id": cls_name, "label": cls_name, "file": rel_path})

    # Inter-class dependencies (e.g. PlanningPage extends BasePage)
    for f in class_files:
        cls_name = os.path.splitext(os.path.basename(f))[0]
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            for other_cls in class_map:
                if other_cls != cls_name and other_cls in content:
                    edges.append({"source": cls_name, "target": other_cls})
        except Exception:
            pass

    # 2. Scan Scripts / tests
    script_patterns = [
        os.path.join(repo_root, "Scripts", "**", "*.groovy"),
        os.path.join(repo_root, "tests", "**", "*.spec.ts"),
        os.path.join(repo_root, "tests", "**", "*.test.ts"),
        os.path.join(repo_root, "tests", "**", "test_*.py"),
    ]
    for pat in script_patterns:
        for f in glob.glob(pat, recursive=True):
            rel_path = os.path.relpath(f, repo_root).replace("\\", "/")
            parent_dir = os.path.basename(os.path.dirname(f))
            file_base = os.path.splitext(os.path.basename(f))[0]
            if file_base.startswith("Script") and parent_dir and parent_dir != "Scripts":
                script_label = parent_dir
            else:
                script_label = file_base

            nodes.append({"id": rel_path, "label": script_label, "file": rel_path})

            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                for cls_name in class_map:
                    if cls_name in content:
                        edges.append({"source": rel_path, "target": cls_name})
            except Exception:
                pass

    return {"nodes": nodes, "edges": edges}


def load_graph(repo_root=None):
    root = repo_root or HUB_ROOT
    graph_path = os.path.join(root, "graphify-out", "graph.json")
    if os.path.exists(graph_path):
        with open(graph_path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    hub_graph = os.path.join(HUB_ROOT, "graphify-out", "graph.json")
    if os.path.exists(hub_graph):
        with open(hub_graph, "r", encoding="utf-8") as fp:
            return json.load(fp)

    # Dynamic fallback graph
    return build_fallback_graph(root)


def get_git_modified_files(repo_root=None):
    root = repo_root or HUB_ROOT
    try:
        res = subprocess.run(
            ["git", "-C", root, "diff", "--name-only", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return files
    except Exception as e:
        print(f"⚠️  Failed to retrieve git diff from {root}: {e}")
        return []


def get_total_test_cases(workspace_dir=None, graph_data=None, override_total=None):
    """Dynamically counts test cases in repository or knowledge graph."""
    if override_total is not None and override_total > 0:
        return override_total

    root = workspace_dir or HUB_ROOT

    # 1. Scan filesystem for test scripts
    test_patterns = [
        os.path.join(root, "Scripts", "**", "*.groovy"),
        os.path.join(root, "Test Cases", "**", "*.tc"),
        os.path.join(root, "tests", "**", "*.spec.ts"),
        os.path.join(root, "tests", "**", "*.test.ts"),
        os.path.join(root, "tests", "**", "*.spec.js"),
        os.path.join(root, "tests", "**", "*.test.js"),
        os.path.join(root, "tests", "**", "test_*.py"),
        os.path.join(root, "tests", "**", "*_test.py"),
    ]
    files = set()
    for pat in test_patterns:
        files.update(glob.glob(pat, recursive=True))
    if files:
        return len(files)

    # 2. Count test case nodes in graph if available
    if graph_data and "nodes" in graph_data:
        tc_nodes = [
            n for n in graph_data["nodes"]
            if any(k in str(n.get("label", "")).lower() or k in str(n.get("name", "")).lower()
                   for k in ["tc-", "testcase", "test_case", "spec"])
        ]
        if tc_nodes:
            return len(tc_nodes)

    return 0


def analyze_impact(graph_data, target_files):
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    # Map target files to node IDs
    target_node_ids = set()
    for tf in target_files:
        norm_tf = tf.replace("\\", "/")
        base_name = os.path.basename(norm_tf)
        class_name = os.path.splitext(base_name)[0]

        for n_id, n in nodes.items():
            n_file = n.get("file", "").replace("\\", "/")
            if norm_tf in n_file or n_id == class_name or n.get("label") == class_name:
                target_node_ids.add(n_id)

    if not target_node_ids:
        return []

    # Build reverse dependency graph (who calls target)
    callers = {}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if tgt not in callers:
            callers[tgt] = set()
        callers[tgt].add(src)

    # BFS to find all upstream impacted nodes
    visited = set()
    queue = list(target_node_ids)
    while queue:
        curr = queue.pop(0)
        if curr in visited:
            continue
        visited.add(curr)
        for parent in callers.get(curr, []):
            if parent not in visited:
                queue.append(parent)

    # Filter for Test Case nodes
    impacted_test_cases = set()
    for node_id in visited:
        node = nodes.get(node_id, {})
        file_path = node.get("file", "")
        label = node.get("label", node_id)

        if "Scripts/" in file_path or "tests/" in file_path or "Test Cases/" in file_path or "TC-" in label or "TC_" in label or "TC" in label:
            impacted_test_cases.add(label)

    return sorted(list(impacted_test_cases))


def main():
    parser = argparse.ArgumentParser(description="Universal Test Impact Analyzer")
    parser.add_argument("target", nargs="?", default=None, help="Target repository path to analyze")
    parser.add_argument("--repo", "--path", dest="repo_path", default=None, help="Target repository path")
    parser.add_argument("--file", "-f", nargs="+", help="Target modified files (e.g. Keywords/pages/CommonCategoryPage.groovy)")
    parser.add_argument("--git-diff", action="store_true", help="Analyze git modified files automatically")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--total", "-t", type=int, default=None, help="Explicit total test case count override")
    args = parser.parse_args()

    try:
        target_repo = resolve_target_repo(cli_target=args.target, cli_repo=args.repo_path)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    target_files = []
    if args.file:
        target_files.extend(args.file)
    if args.git_diff or not target_files:
        git_files = get_git_modified_files(target_repo)
        target_files.extend([f for f in git_files if "Keywords/" in f or "pages/" in f or "src/" in f])

    if not target_files:
        print("ℹ️  No Page Class / Keywords files specified or modified in git.")
        return 0

    graph_data = load_graph(target_repo)
    impacted_tcs = analyze_impact(graph_data, target_files)

    total_tcs = get_total_test_cases(target_repo, graph_data, args.total)
    if total_tcs == 0:
        total_tcs = max(len(impacted_tcs), 1)

    impacted_count = len(impacted_tcs)
    saved_count = max(0, total_tcs - impacted_count)
    reduction_pct = (saved_count / total_tcs * 100) if total_tcs else 0

    if args.json:
        result = {
            "target_repository": target_repo,
            "target_files": target_files,
            "impacted_count": impacted_count,
            "total_test_cases": total_tcs,
            "time_saved_percent": round(reduction_pct, 1),
            "impacted_test_cases": impacted_tcs
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print("\n" + "=" * 70)
    print("  UNIVERSAL TEST IMPACT ANALYZER (GRAPHIFY AST KNOWLEDGE GRAPH)")
    print("=" * 70)
    print(f"📁 Target Repository : {target_repo}")
    print("🔍 Modified / inspected target files:")
    for tf in target_files:
        print(f"   • {tf}")

    print("\n📊 Test Impact Assessment:")
    print(f"   - Directly impacted Test Cases        : {impacted_count} / {total_tcs} TCs")
    print(f"   - Test Cases unaffected (Skipped)     : {saved_count} TCs")
    print(f"   - CI/CD execution time reduction       : {reduction_pct:.1f}%")

    if impacted_tcs:
        print("\n📋 Candidate Test Cases for re-test:")
        for idx, tc in enumerate(impacted_tcs[:20], 1):
            print(f"   {idx:2d}. {tc}")
        if len(impacted_tcs) > 20:
            print(f"   ... and {len(impacted_tcs) - 20} additional Test Cases.")

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
