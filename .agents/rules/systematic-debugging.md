---
trigger: always_on
description: Enforce rigorous engineering discipline, systematic debugging without guesswork, and verification before completion.
---

# Systematic Debugging & Verification Discipline (Superpowers Standard)

*(Inherited from `obra/superpowers`)*

This rule governs all AI Agents operating on the repository. It mandates strict engineering rigor, prohibiting intuitive guesswork and unverified declarations of completion.

---

## 1. Iron Discipline: Zero Guesswork Debugging

1. **Evidence Before Action:**
   - Never modify code based on a hunch or assumption.
   - Every bug fix or locator update must be preceded by concrete ground-truth evidence:
     - Log excerpt showing the exact failing line and exception.
     - Visual inspection of `Screenshots/FAILED_*.png`.
     - Live DOM element state verified via Playwright Live Interaction.
2. **Preserve Working Code:**
   - When fixing an issue in a Page Class or script, touch only the minimal lines required. Never rewrite working methods speculatively.

---

## 2. Verification-First & Zero False Completion

1. **Never Declare Complete Without Running Verification:**
   - Any agent claiming a fix or refactoring is finished MUST run:
     ```bash
     python3 tools/verify_all.py
     ```
   - All 8 Gates must return `PASS`. If any gate fails, the task is NOT complete.
2. **Targeted Re-Test:**
   - After modifying Page Classes, check impacted Test Cases with:
     ```bash
     python3 tools/test_impact.py --git-diff
     ```
   - Verify the affected test cases pass before handoff.
3. **Synchronize Knowledge Graph & Repo Map:**
   - Run `graphify update .` to keep the AST knowledge graph updated.
   - Run `python3 tools/repo_map.py` if any Page Class or Helper was modified.

---

## 3. Situational Tool Dispatch Matrix & Zero-Command Autonomy

> 🚀 **Zero-Command Autonomous Invariant (Zero Manual Commands):**  
> The user **NEVER** needs to remember syntax or manually type tool commands (`agent-qa setup`, `agent-qa analyze`, `verify_all.py`...).  
> The AI Agent **MUST AUTONOMOUSLY recognize context and trigger** the corresponding tools below on-demand whenever the situation arises.  
>  
> 🎯 **On-Demand Activation Principle (Situation-Specific — Never Run Blindly):**  
> Tools assigned to AI and Subagents are **situational weapons**, **NEVER executed all at once**. Agents draw the specific tool from the arsenal if and only if a concrete need arises (e.g.: failing test triggers `auto_heal`, new project triggers `setup_project`, API breaking change triggers `api_drift_sentinel`).

| Context / Trigger | Mandatory Tool | Specific Objective |
| :--- | :--- | :--- |
| **New project / Missing `PROJECT_AI_GUIDE.md` / Fresh clone** | `python3 tools/setup_project.py [target]` | 100% Autonomous: Detects framework (Playwright/Katalon/Pytest), generates `PROJECT_AI_GUIDE.md`, installs `pre-push` hook, extracts `repo_map.txt`, runs initial audit. |
| **User requests: "analyze project" / "re-analyze" / "project audit"** | `python3 tools/analyze_project.py [target]` | Execute comprehensive 5-in-1 health audit, sync repo_map, infer_linter, data_flow, verify_all & generate PROJECT_HEALTH_REPORT.md.<br/>**Post-Action:** Stage, commit & push updated project files (`PROJECT_HEALTH_REPORT.md`, `repo_map.txt`) to git. |
| **Starting task / Querying Page Class methods** | `tools/repo_map.txt`<br/>*(run `python3 tools/repo_map.py` if classes changed)* | Read compressed 500-token map for signatures; avoid reading 4,000-line files. |
| **Dispatching Browser Actions (Live/CDP)** | `python3 tools/safety_firewall.py --dry-run` | Mandatory Pre-execution Hook: Block irreversible/destructive operations before browser dispatch. |
| **Creating or updating Test Scripts** | `python3 tools/infer_linter.py` | Run AST scan for Fake-Pass (0 asserts) and empty catch blocks. |
| **New/Modified Test Case Quality** | `python3 tools/micro_mutator.py --min-score 80` | AST Mutation Testing: Reject test suites with mutation score < 80%. |
| **Before Git Commit or Completing Task** | `python3 tools/verify_all.py` | Validate all 8 Quality Gates DoD. |
| **After modifying Page Classes** | `python3 tools/test_impact.py --git-diff` | Scope impacted test cases; avoid re-running entire test suites. |
| **When Test FAILS in CLI/KRE** | `python3 tools/pinpoint_failure.py` | Parse JUnit XML to identify exact failing line and exception in 0.1s. |
| **When CLI / Gradle logs are verbose** | `python3 tools/distill_log.py <log>` | Filter 95% noise; preserve only actionable stacktraces and pointers. |
| **Handling UI exceptions (Overlay, Stale)** | `python3 tools/cache_resolver.py query "<error>"` | Lookup 0-token solution from local SQLite memory cache before improvising. |
| **Pre-Push / Suite Acceptance** | `python3 tools/trace_data_flow.py` | Run Taint Analysis to verify no orphan database junk remains uncleaned. |
| **Canary Self-Healing Audit** | `python3 tools/agent_canary.py --run` | Inject 8 failure vectors to benchmark MTTR and autonomous recovery rate. |
| **Testing GIS Canvas / Chart without DOM** | `python3 tools/visual_diff_canvas.py` | Compare pixel / SSIM to detect visual rendering regression. |
| **Pulling code / New clone** | `python3 tools/cache_resolver.py init` | Automatically sync Central Agent Memory (`~/.agent_memory/global_cache.db`). |
| **Before authoring test for Page/Flow** | `python3 tools/cache_resolver.py get-lessons --context "<page>"` | Query top 2 episodic lessons learned to avoid repeating past failure patterns. |
| **After healing a bug / failure** | `python3 tools/cache_resolver.py record-lesson` | Record a concise 2-line lesson into SQLite memory for cross-session reflexion. |

---

## 4. Cognitive Forcing Functions (Structured Reasoning Pipeline)

> **Core Principle:** Autocomplete mode generates weak, tautological tests. Before outputting any test script, Universal IR, or Page Class, the agent **MUST** pass through a 4-step System-2 reasoning pipeline:

```markdown
<reasoning_protocol>
Step 1 - Boundary & Invariant Extraction: Xác định các bất biến (invariants) của hệ thống. Cái gì bắt buộc không bao giờ được phép xảy ra?
Step 2 - Falsification Hypotheses (Phản đề Popper): Đưa ra 3 kịch bản lập trình viên có thể làm hàm chạy sai mà test thông thường vẫn pass (False Negatives).
Step 3 - Self-Debate: Tự giải thích tại sao assertion chuẩn bị viết sẽ bắt chết cả 3 kịch bản phá hoại ở Step 2.
Step 4 - Emit Code / Universal IR: Chỉ sinh code khi đã hoàn thành 3 bước trên.
</reasoning_protocol>
```

---

## 5. Adversarial Self-Play: Red-Team vs Blue-Team

- **Agent Blue (`pom-crafter`):** Synthesizes Clean POM code and defensive assertions.
- **Agent Red (`failure-analyst`):** Acts as the rogue developer, actively injecting AST mutants via `tools/micro_mutator.py` into source/mocks.
- **Evaluation Loop:**
  - If Blue's tests let mutants survive (Mutation Score $< 80\%$), Red-Team **REJECTS** the code and commands Blue to strengthen assertions.
  - Test suites are only Approved when Mutation Score reaches $\ge 80\%$.
