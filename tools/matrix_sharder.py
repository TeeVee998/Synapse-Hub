#!/usr/bin/env python3
"""
Enterprise Duration-Balanced Test Matrix Sharder
------------------------------------------------
Balances parallel CI/CD test execution across N containers using historical
runtimes and the Greedy LPT (Longest Processing Time First) Bin-Packing algorithm.
Eliminates CI runner bottlenecks where one worker runs for 15m while others finish in 2m.
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CACHE_DB_PATH = os.path.join(SCRIPT_DIR, "memory_cache.db")


def find_test_files(target_dir: str) -> List[str]:
    """Discovers all executable test scripts across Katalon, Playwright, or Pytest suites."""
    target_path = Path(target_dir)
    test_files = []
    valid_exts = {".groovy", ".ts", ".js", ".py"}

    for root, _, files in os.walk(target_path):
        for f in files:
            # Match standard test naming patterns
            lower = f.lower()
            if any(lower.endswith(ext) for ext in valid_exts):
                if "test" in lower or "spec" in lower or "tc_" in lower or "scripts" in root.lower():
                    rel_p = os.path.relpath(os.path.join(root, f), target_dir).replace("\\", "/")
                    test_files.append(rel_p)

    return sorted(test_files)


def estimate_test_duration(file_path: str, full_path: str) -> float:
    """Estimates test execution duration in seconds using historical cache or file heuristic."""
    # Check SQLite historical runtime cache if available
    if os.path.exists(CACHE_DB_PATH):
        try:
            conn = sqlite3.connect(CACHE_DB_PATH)
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS test_runtimes (test_path TEXT PRIMARY KEY, duration REAL)")
            cur.execute("SELECT duration FROM test_runtimes WHERE test_path = ?", (file_path,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return float(row[0])
        except Exception:
            pass

    # Heuristic fallback: ~0.5s per line of script
    try:
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                lines = len(fp.readlines())
            return max(5.0, round(lines * 0.25, 1))
    except Exception:
        pass

    return 10.0


def shard_tests_lpt(test_files: List[str], target_dir: str, num_shards: int) -> List[Dict[str, Any]]:
    """
    Applies Longest Processing Time First (LPT) bin-packing to distribute tests evenly.
    """
    num_shards = max(1, num_shards)
    if not test_files:
        return [{"shard_index": i + 1, "total_duration": 0.0, "tests": []} for i in range(num_shards)]

    # 1. Calculate duration for each test
    tests_with_cost = []
    for tf in test_files:
        fp = os.path.join(target_dir, tf)
        dur = estimate_test_duration(tf, fp)
        tests_with_cost.append((tf, dur))

    # 2. Sort descending by duration
    tests_with_cost.sort(key=lambda x: x[1], reverse=True)

    # 3. Initialize shards
    shards = [{"shard_index": i + 1, "total_duration": 0.0, "tests": []} for i in range(num_shards)]

    # 4. Greedily assign to the shard with the least current cumulative duration
    for test_file, dur in tests_with_cost:
        # Find shard with min duration
        min_shard = min(shards, key=lambda s: s["total_duration"])
        min_shard["tests"].append(test_file)
        min_shard["total_duration"] = round(min_shard["total_duration"] + dur, 2)

    return shards


def main():
    parser = argparse.ArgumentParser(description="Duration-Balanced Test Matrix Sharder")
    parser.add_argument("target", nargs="?", default=os.getcwd(), help="Target repository root")
    parser.add_argument("--shards", "-n", type=int, default=4, help="Number of parallel shards/workers (default: 4)")
    parser.add_argument("--json", action="store_true", help="Output matrix in JSON format")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target)
    test_files = find_test_files(target_dir)
    shards = shard_tests_lpt(test_files, target_dir, args.shards)

    if args.json:
        print(json.dumps({"total_tests": len(test_files), "shards_count": args.shards, "shards": shards}, indent=2))
    else:
        print(f"\n======================================================================")
        print(f"      DURATION-BALANCED TEST MATRIX SHARDER ({args.shards} PARALLEL WORKERS)    ")
        print(f"======================================================================")
        print(f"  Target Scope : {target_dir}")
        print(f"  Total Tests  : {len(test_files)} files\n")

        for s in shards:
            print(f"📦 Shard {s['shard_index']}: {len(s['tests'])} tests (~{s['total_duration']}s total)")
            for t in s['tests'][:5]:
                print(f"   • {t}")
            if len(s['tests']) > 5:
                print(f"   ... and {len(s['tests']) - 5} more")
            print()

        # Calculate imbalance delta
        durations = [s["total_duration"] for s in shards]
        delta = max(durations) - min(durations) if durations else 0
        print(f"⚡ Shard Imbalance Delta: {delta:.1f}s (Optimal parallel distribution)")
        print(f"======================================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
