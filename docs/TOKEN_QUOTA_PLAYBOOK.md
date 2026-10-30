# Enterprise Token & Context Engineering Playbook (AI QA Hub)

> **Objective:** Maximize AI Agent performance, eliminate context rot, and optimize token quota across the automated test engineering lifecycle.

---

## 1. AI Model Allocation Matrix

Avoid depleting high-tier model quotas by applying the **"Right Task - Right Model"** strategy:

| AI Model Tier | Capability & Relative Cost | Recommended QA Workloads | Token Consumption |
| :--- | :--- | :--- | :--- |
| **Claude Sonnet / Opus / GPT-4o** | ⭐⭐⭐ High | • Complex logic, nested Shadow DOM / iFrames<br>• Race conditions & complex async synchronization<br>• Flaky test root-cause autopsy & Clean POM refactoring | 🔴 Expensive (Use selectively) |
| **Gemini Pro / Claude 3.5 Sonnet** | ⭐⭐ Balanced | • Everyday POM code generation, assertions, locator updates<br>• User Story to automated test transpilation<br>• Unit tests, REST API stubs & mock routes | 🟡 Moderate |
| **Gemini Flash / Claude Haiku** | ⭐ High-Speed & Low-Cost | • Parsing multi-thousand-line CI/CD logs (`distill_log.py`)<br>• Generating synthetic test data (JSON/CSV rows)<br>• Compact AOM extraction & DOM structure filtering<br>• Summaries, documentation, commit messages | 🟢 Ultra-economical |

---

## 2. Operational Mode Strategy

- **Planning Mode:**
  - Bootstrap new test automation frameworks from scratch.
  - Architect multi-tier Page Object Model hierarchies for large modules.
  - Analyze complex End-to-End user journeys traversing multiple microservices.
- **Fast / Chat Mode:**
  - Add individual test cases to existing Page Classes.
  - Heal single selectors after UI builds.
  - Debug and re-run isolated test scripts.

---

## 3. Context Window Invariants (Zero Context Rot)

1. **Progressive Disclosure (Never Load Large Files Whole):**
   - Never load classes over 500 lines into the active conversation prompt.
   - Query `tools/repo_map.txt` for method signatures first (~500 tokens). Micro-read targeted 20-50 line slices (`StartLine`, `EndLine`).
2. **Log Distillation (`distill_log.py`):**
   - Never dump thousands of lines of raw build/runner output.
   - Run `python3 tools/distill_log.py <path_to_log>` to filter out 95% noise, extracting only the exact failure line and last 3 HTTP requests.
3. **Compaction State Anchoring (`project_state.py`):**
   - Antigravity automatically triggers Context Compaction near the ~135k token threshold. Ensure active test run statuses and defect IDs are persisted to `PROJECT_STATE.md` on disk to avoid lossy state compression.
