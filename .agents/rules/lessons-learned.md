---
trigger: always_on
description: Critical anti-patterns, past mistakes, and strict avoidance rules (capped < 40 lines).
---

# Agent Anti-Pattern Blacklist & Failure Prevention

> **Policy:** Hot-memory lessons learned. Hard-capped at **Max 8 rules (< 40 lines, ~150 tokens)**.
> When table exceeds 8 rows, consolidate similar rules into higher-order invariants or archive to `~/.agent_memory/global_cache.db`.

| # | Mistake / Anti-Pattern | Root Cause | Mandatory Avoidance Rule |
|---|---|---|---|
| **1** | **XPath strings parsed as methods** | Regex captured `String TXT = "...contains(...)"`. | In Groovy, `=` before `(` denotes a variable/constant, **never** a method. |
| **2** | **GIS map polygon rejected** | Fixed `(100, 200)` coordinates caused overlap. | Always randomize coordinates via `TestHelper.getUniquePolygonCoordinates()`. |
| **3** | **`ElementClickInterceptedException`** | Clicked while PrimeNG overlay backdrop was fading. | Always use `BasePage.clickJS()` or `window.__helper.clickSafe()` to bypass overlays. |
| **4** | **Context window blowout** | Read 4,368-line `DataMiningPage.groovy` directly. | **Never read large files whole.** Query `tools/repo_map.txt` or read 20-50 line ranges. |
| **5** | **Flaky timing on CI/CD** | `Thread.sleep` failed under variable network lag. | Replace 100% with Smart Wait: Angular `isStable()` and CDP `Network Idle 0`. |
| **6** | **DB polluted with test junk** | Created entities without executing deletion. | Every data creation test case **must** execute idempotent teardown cleanup. |
| **7** | **Graphify/CLI ran on Skill Hub instead of target project** | Defaulted to `CWD = Agent Skill` without checking Active Workspaces. | **Agent Skill folder = read-only hub, NEVER a CLI target.** Always identify the real target project from `Active Workspaces` (the non-hub workspace). If multiple project workspaces exist, ask the user. All outputs (graphify-out/, reports) must land inside the target project folder. |

### Memory Management & Consolidation Protocol:
- **Max capacity:** 8 active rules in prompt hot memory.
- **Negative Feedback Cache (Blind Retry Prevention):** Whenever a bug fix attempt fails during test verification, AI agents MUST immediately persist it via `agent-qa heal record-failed --error "<sig>" --patch "<failed_code>" --reason "<why_failed>"` to prevent repeating the failed patch.
- **Overflow policy:** Consolidate related patterns into a single generalized invariant; offload edge cases to SQLite `~/.agent_memory/global_cache.db` (0-token cold storage).
