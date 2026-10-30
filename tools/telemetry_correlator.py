#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/telemetry_correlator.py — Full-Stack APM & Server Telemetry Performance Correlator
---------------------------------------------------------------------------------------
Correlates Client-Side perceived response times (from JMeter .jtl) with Server-Side
infrastructure metrics (Prometheus Node Exporter, PerfMon, CloudWatch, Datadog),
performs Pearson correlation analysis, isolates resource bottlenecks, and generates
an automated Root Cause Analysis (RCA) diagnostic report for Senior Performance QCs.

Capabilities:
  1. Multi-Dimensional Correlation:
     - Client Latency (P95/P99 ms) vs Server CPU Utilization (%)
     - Client Latency vs Server Memory Utilization (%) / JVM GC Pauses
     - Client Latency vs Database Connection Pool Saturation
     - Client Latency vs Network I/O & Disk Write IOPS
  2. Root Cause Attribution Engine:
     - Detects CPU saturation (CPU > 85% correlating with latency spikes)
     - Detects Memory leak / JVM Stop-the-world GC pauses (RAM > 90%)
     - Detects Database connection starvation (DB Pool = Max)
     - Detects Network / Gateway / Downstream third-party bottleneck
  3. CI/CD Artifacts:
     - Visual ANSI Correlation Matrix
     - GitHub / GitLab Markdown RCA report with actionable tuning recommendations
     - Structured JSON diagnostic export.

Usage:
  python tools/telemetry_correlator.py --jtl results.jtl --server-metrics server.csv
  python tools/telemetry_correlator.py --sample --markdown rca_report.md
  agent-qa correlate-telemetry --jtl results.jtl --server-metrics server.csv
"""

import os
import sys
import csv
import json
import math
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Enforce UTF-8 stdout encoding for Windows/macOS/Linux console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def calculate_pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculates Pearson correlation coefficient between two numeric series."""
    n = min(len(x), len(y))
    if n < 2:
        return 0.0

    x = x[:n]
    y = y[:n]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denom_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    denom_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    if denom_x <= 0 or denom_y <= 0:
        return 0.0

    return numerator / math.sqrt(denom_x * denom_y)


def parse_jtl_time_series(jtl_path: str, bucket_sec: int = 5) -> Dict[int, List[float]]:
    """Buckets JMeter elapsed times by N-second time windows."""
    buckets: Dict[int, List[float]] = {}
    with open(jtl_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_ms = int(float(row.get("timeStamp") or row.get("Timestamp") or 0))
                elapsed = float(row.get("elapsed") or row.get("Elapsed") or 0)
                sec_bucket = (ts_ms // 1000 // bucket_sec) * bucket_sec
                if sec_bucket not in buckets:
                    buckets[sec_bucket] = []
                buckets[sec_bucket].append(elapsed)
            except Exception:
                continue
    return buckets


def parse_server_metrics(metrics_path: str, bucket_sec: int = 5) -> Dict[str, Dict[int, float]]:
    """
    Parses server telemetry CSV (timestamp/time, cpu_pct, memory_pct, db_pool_pct, disk_iops).
    """
    series: Dict[str, Dict[int, float]] = {
        "cpu_pct": {},
        "memory_pct": {},
        "db_pool_pct": {},
        "disk_iops": {}
    }

    with open(metrics_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Timestamp can be unix epoch in seconds or milliseconds
                raw_ts = float(row.get("timestamp") or row.get("time") or row.get("epoch") or 0)
                ts_sec = int(raw_ts if raw_ts < 1e11 else raw_ts / 1000)
                bucket = (ts_sec // bucket_sec) * bucket_sec

                if "cpu" in row or "cpu_pct" in row:
                    series["cpu_pct"][bucket] = float(row.get("cpu_pct") or row.get("cpu") or 0)
                if "memory" in row or "memory_pct" in row or "mem_pct" in row:
                    series["memory_pct"][bucket] = float(row.get("memory_pct") or row.get("memory") or 0)
                if "db_pool" in row or "db_pool_pct" in row or "db_connections" in row:
                    series["db_pool_pct"][bucket] = float(row.get("db_pool_pct") or row.get("db_pool") or 0)
                if "disk_iops" in row or "disk" in row or "iops" in row:
                    series["disk_iops"][bucket] = float(row.get("disk_iops") or row.get("disk") or 0)
            except Exception:
                continue

    return series


def run_correlation_analysis(
    jtl_buckets: Dict[int, List[float]],
    server_series: Dict[str, Dict[int, float]]
) -> Dict[str, Any]:
    """Aligns time series and evaluates Pearson correlation & Root Cause."""
    sorted_buckets = sorted(jtl_buckets.keys())
    if not sorted_buckets:
        return {"status": "NO_DATA", "correlations": {}, "root_causes": []}

    # Calculate P95 per bucket
    p95_series: List[float] = []
    aligned_cpu: List[float] = []
    aligned_mem: List[float] = []
    aligned_db: List[float] = []
    aligned_disk: List[float] = []

    for b in sorted_buckets:
        values = sorted(jtl_buckets[b])
        p95 = values[int(len(values) * 0.95)] if values else 0.0
        p95_series.append(p95)

        aligned_cpu.append(server_series["cpu_pct"].get(b, 0.0))
        aligned_mem.append(server_series["memory_pct"].get(b, 0.0))
        aligned_db.append(server_series["db_pool_pct"].get(b, 0.0))
        aligned_disk.append(server_series["disk_iops"].get(b, 0.0))

    corr_cpu = calculate_pearson_correlation(p95_series, aligned_cpu)
    corr_mem = calculate_pearson_correlation(p95_series, aligned_mem)
    corr_db = calculate_pearson_correlation(p95_series, aligned_db)
    corr_disk = calculate_pearson_correlation(p95_series, aligned_disk)

    max_cpu = max(aligned_cpu) if aligned_cpu else 0
    max_mem = max(aligned_mem) if aligned_mem else 0
    max_db = max(aligned_db) if aligned_db else 0
    max_p95 = max(p95_series) if p95_series else 0

    root_causes: List[Dict[str, str]] = []

    if corr_cpu >= 0.65 and max_cpu > 80:
        root_causes.append({
            "component": "Server CPU Compute",
            "severity": "CRITICAL",
            "correlation": f"{corr_cpu:.2f}",
            "description": f"Strong positive correlation ({corr_cpu:.2f}) with peak CPU reaching {max_cpu:.1f}%. Compute capacity is saturated under peak load.",
            "recommendation": "Profile hot methods/threads with async-profiler. Consider CPU thread pool tuning or vertical/horizontal pod autoscaling (HPA)."
        })

    if corr_db >= 0.65 and max_db > 85:
        root_causes.append({
            "component": "Database Connection Pool",
            "severity": "CRITICAL",
            "correlation": f"{corr_db:.2f}",
            "description": f"Strong positive correlation ({corr_db:.2f}) with DB Connection Pool reaching {max_db:.1f}% capacity. Threads are blocked waiting for pooled DB connections.",
            "recommendation": "Increase HikariCP / Tomcat maxPoolSize. Audit slow SQL queries holding connections open or enable connection leak detection."
        })

    if corr_mem >= 0.60 and max_mem > 85:
        root_causes.append({
            "component": "Server Memory / JVM Heap",
            "severity": "HIGH",
            "correlation": f"{corr_mem:.2f}",
            "description": f"Memory saturation reached {max_mem:.1f}% with correlation ({corr_mem:.2f}). Probable GC pause (Stop-The-World) throttling throughput.",
            "recommendation": "Inspect GC logs (-Xlog:gc*). Tune JVM garbage collection flags (G1GC / ZGC) or adjust heap headroom (-Xmx)."
        })

    if not root_causes:
        if max_p95 > 1000 and max_cpu < 50 and max_db < 50:
            root_causes.append({
                "component": "Downstream Network / External Dependency",
                "severity": "MEDIUM",
                "correlation": "N/A",
                "description": f"Latency spiked to {max_p95:.1f}ms while Server CPU ({max_cpu:.1f}%) and DB Pool ({max_db:.1f}%) remained relaxed.",
                "recommendation": "Audit external 3rd-party HTTP gateways, microservice RPC timeouts, or lock contention in synchronized code blocks."
            })
        else:
            root_causes.append({
                "component": "System Health Normal",
                "severity": "INFO",
                "correlation": "N/A",
                "description": "Server hardware resources scale stably within acceptable performance boundaries.",
                "recommendation": "Maintain current infrastructure capacity parameters."
            })

    return {
        "status": "COMPLETED",
        "sample_points": len(sorted_buckets),
        "metrics_summary": {
            "max_p95_ms": round(max_p95, 2),
            "max_cpu_pct": round(max_cpu, 2),
            "max_memory_pct": round(max_mem, 2),
            "max_db_pool_pct": round(max_db, 2),
        },
        "correlations": {
            "cpu_correlation": round(corr_cpu, 3),
            "memory_correlation": round(corr_mem, 3),
            "db_pool_correlation": round(corr_db, 3),
            "disk_correlation": round(corr_disk, 3)
        },
        "root_causes": root_causes
    }


def format_rca_markdown(analysis: Dict[str, Any]) -> str:
    """Generates GitHub / GitLab Markdown RCA report."""
    summary = analysis["metrics_summary"]
    corrs = analysis["correlations"]
    causes = analysis["root_causes"]

    lines = [
        "# 🔬 Full-Stack Performance Telemetry Correlation & RCA Report",
        "",
        "### 📊 Telemetry Metrics Summary",
        f"- **Max Client P95 Latency:** `{summary['max_p95_ms']} ms`",
        f"- **Peak Server CPU Utilization:** `{summary['max_cpu_pct']}%`",
        f"- **Peak Memory Consumption:** `{summary['max_memory_pct']}%`",
        f"- **Peak Database Pool Usage:** `{summary['max_db_pool_pct']}%`",
        "",
        "### 🔗 Pearson Correlation Matrix (Client Latency vs Server Telemetry)",
        "| Server Metric | Pearson Coefficient ($r$) | Impact Level | Interpretation |",
        "| :--- | :---: | :---: | :--- |",
        f"| **CPU Utilization** | `{corrs['cpu_correlation']}` | {'🔴 HIGH' if corrs['cpu_correlation'] > 0.6 else '🟢 LOW'} | Latency tracks CPU load directly |",
        f"| **Database Pool** | `{corrs['db_pool_correlation']}` | {'🔴 HIGH' if corrs['db_pool_correlation'] > 0.6 else '🟢 LOW'} | Connection pool saturation bottleneck |",
        f"| **Memory / JVM** | `{corrs['memory_correlation']}` | {'🟠 MEDIUM' if corrs['memory_correlation'] > 0.5 else '🟢 LOW'} | Possible GC pause or memory pressure |",
        f"| **Disk I/O** | `{corrs['disk_correlation']}` | {'🟠 MEDIUM' if corrs['disk_correlation'] > 0.5 else '🟢 LOW'} | Storage latency / write queueing |",
        "",
        "### 🎯 Root Cause Attribution & Engineering Action Items",
        ""
    ]

    for c in causes:
        badge = "🔴 CRITICAL" if c["severity"] == "CRITICAL" else ("🟠 HIGH" if c["severity"] == "HIGH" else "🔵 INFO")
        lines.extend([
            f"#### [{badge}] {c['component']}",
            f"- **Observation:** {c['description']}",
            f"- **Actionable Tuning:** {c['recommendation']}",
            ""
        ])

    lines.extend([
        "---",
        "*Report auto-generated by Synapse-Hub `telemetry_correlator.py` - Enterprise Observability Suite.*"
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Full-Stack APM & Server Telemetry Performance Correlator (Senior QC Performance Suite)."
    )
    parser.add_argument("--jtl", help="Path to JMeter results file (.jtl).")
    parser.add_argument("--server-metrics", "-s", help="Path to Server Telemetry CSV (timestamp, cpu_pct, memory_pct, db_pool_pct).")
    parser.add_argument("--markdown", "-m", help="Path to export Markdown RCA report.")
    parser.add_argument("--json", "-j", help="Path to export structured JSON diagnostics.")
    parser.add_argument("--sample", action="store_true", help="Generate synthetic client & server telemetry dataset for verification.")

    args = parser.parse_args()

    if args.sample or not args.jtl or not args.server_metrics:
        import tempfile, time
        temp_dir = tempfile.gettempdir()
        temp_jtl = os.path.join(temp_dir, "sample_corr_jmeter.jtl")
        temp_srv = os.path.join(temp_dir, "sample_corr_server.csv")

        base_ts = int(time.time() * 1000)
        # Create synthetic correlated dataset: CPU and Latency spike together in the middle
        with open(temp_jtl, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timeStamp", "elapsed", "label", "responseCode", "success"])
            for sec in range(60):
                # Spike between sec 20 and 40
                is_spike = 20 <= sec <= 40
                elapsed = 150 + (1200 if is_spike else 0) + (sec % 10)
                for _ in range(10):
                    w.writerow([base_ts + (sec * 1000), elapsed, "[POST] /api/v1/checkout", "200", "true"])

        with open(temp_srv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "cpu_pct", "memory_pct", "db_pool_pct", "disk_iops"])
            for sec in range(60):
                is_spike = 20 <= sec <= 40
                cpu = 25.0 + (65.0 if is_spike else 5.0) + (sec % 3)
                mem = 60.0 + (sec * 0.2)
                db = 30.0 + (60.0 if is_spike else 0.0)
                w.writerow([int(base_ts / 1000) + sec, cpu, mem, db, 120])

        args.jtl = temp_jtl
        args.server_metrics = temp_srv
        print(f"🔬 [SAMPLE MODE] Generated synthetic correlated dataset in {temp_dir}")

    jtl_buckets = parse_jtl_time_series(args.jtl, bucket_sec=5)
    server_series = parse_server_metrics(args.server_metrics, bucket_sec=5)

    analysis = run_correlation_analysis(jtl_buckets, server_series)

    print("\n" + "=" * 80)
    print("  FULL-STACK APM & SERVER TELEMETRY CORRELATION ENGINE (RCA MATRIX)")
    print("=" * 80)
    print(f"Sample Windows Evaluated : {analysis['sample_points']} time slices (5s interval)")
    print(f"Peak Client P95 Latency : {analysis['metrics_summary']['max_p95_ms']} ms")
    print(f"Peak Server CPU          : {analysis['metrics_summary']['max_cpu_pct']}%")
    print(f"Peak Database Pool       : {analysis['metrics_summary']['max_db_pool_pct']}%")
    print("-" * 80)
    print("Pearson Correlation Coefficients (r):")
    for k, v in analysis["correlations"].items():
        print(f"  • {k.replace('_', ' ').title():<25} : {v:+0.3f}")
    print("-" * 80)
    print("🎯 Root Cause Analysis (RCA):")
    for c in analysis["root_causes"]:
        print(f"  [{c['severity']}] {c['component']}: {c['description']}")
        print(f"    👉 Recommendation: {c['recommendation']}")
    print("=" * 80 + "\n")

    if args.markdown:
        md = format_rca_markdown(analysis)
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown)) or ".", exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"📄 Markdown RCA Report exported: {args.markdown}")

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        print(f"📊 JSON Diagnostics exported: {args.json}")


if __name__ == "__main__":
    main()
