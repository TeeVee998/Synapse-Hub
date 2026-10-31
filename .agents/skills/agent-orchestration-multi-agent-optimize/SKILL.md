---
name: agent-orchestration-multi-agent-optimize
description: "Profile, benchmark, and orchestrate multi-agent test workloads and token throughput. Use when orchestrating multi-agent swarms, partitioning workloads, or optimizing agent roles."
---

# Multi-Agent Optimization & Orchestration Skill

> **Target:** Optimize multi-agent test workloads, reduce context overhead, streamline agent handoffs, and monitor token consumption across autonomous test swarms.

---

## 1. When to Use

- Managing multi-agent coordination, test suite sharding, and throughput.
- Profiling sub-agent task decomposition to eliminate redundant execution.
- Implementing dynamic model tiering (fast models for search, deep models for healing).
- Budgeting context tokens across collaborative agent swarms.

---

## 2. Core Orchestration Principles

1. **Single Front-Door Protocol:**
   - All inbound tasks route through `orchestrator` to prevent split-brain execution.
2. **Context Isolation (`Workspace: 'share'`):**
   - Subagents run in isolated workspaces to avoid git index collisions and context pollution.
3. **Observation Distillation:**
   - Subagents return only 3-5 line summaries and pointers to logs on disk, never dumping thousands of stdout lines into the parent context.
4. **Dynamic Model Routing:**
   - Use lighter models (`flash`, `flash_lite`) for element exploration and log filtering.
   - Use deeper models (`inherit`, `pro`) for root-cause synthesis and AST mutation testing.

---

## 3. Workload Sharding & Matrix Execution

```python
# Multi-agent workload partition example
def shard_test_workload(suite_files: list, max_agents: int = 4) -> list:
    """Partitions test cases across parallel subagents to minimize total execution wall-clock time."""
    shards = [[] for _ in range(max_agents)]
    for idx, test_file in enumerate(suite_files):
        shards[idx % max_agents].append(test_file)
    return [s for s in shards if s]
```

---

## 4. Token & Latency Governance

| Optimization Layer | Baseline (Naive) | Optimized (Synapse Swarm) | Savings |
| :--- | :--- | :--- | :--- |
| **CLI Log Output** | Dump 3,000 lines | `tools/distill_log.py` (< 50 tokens) | **95%** |
| **Codebase Reading** | Read whole classes | `tools/repo_map.txt` (< 600 tokens) | **90%** |
| **Failure Resolution**| Multiple prompt loops | SQLite cache lookup (< 0.1s) | **> 90%** |
| **DOM Inspection** | Raw HTML DOM | Compact AOM (< 500 tokens) | **90%** |

---

## 5. Verification & Safety Guidelines

- Always establish baseline metrics before applying workflow changes.
- Ensure subagent dynamic test data uses unique runtime IDs (`AUTO_<timestamp>_<agentId>`).
- Enforce automated teardown for all creation actions dispatched by subagents.
