# 🧠 Synapse Hub — AI Agent Intelligence Core & Skill Network

[🇻🇳 Tiếng Việt](README.md) | [🇬🇧 English Edition](README.en.md)

> **The shared intelligence core and autonomous skill hub empowering AI coding assistants (Google Antigravity / Cursor / Windsurf / Claude Code) across automated testing suites.**  
> **Author:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))  
> **Hub Version:** `v2.3.0` (Semantic Versioning) | **Integrity Index:** 29 Skills, 7 Workflows, 6 Swarm Roles, 10 Core Rules, 50+ Tools, 9 Quality Gates.

---

## ⚡ 30-Second Quickstart (Zero-Clone All-in-One 🚀)

Configure your test repository in **5 seconds** without cloning or setting up multi-root workspaces:

```bash
# Run directly inside your target test project root:
npx synapse-hub setup
```

👉 **What happens automatically:**
1. 🧠 **Injects Global Antigravity Plugin:** Mounts into `~/.gemini/config/plugins/synapse-hub` (all Antigravity projects inherit 29 Skills immediately).
2. 🌐 **Deploys Universal AI Bridges:** Generates rules for Cursor (`.cursor/rules/`), Claude Code (`CLAUDE.md`), GitHub Copilot (`.github/copilot-instructions.md`), and Windsurf (`.windsurfrules`).
3. 📋 **Generates Project Guide & Hook:** Creates `PROJECT_AI_GUIDE.md` and installs pre-push verification gate.
4. 💾 **Initializes Episodic Memory:** Seeds offline SQLite healing memory at `~/.agent_memory/global_cache.db` (0 token cost).

### Instant CLI Verification:
```bash
npx synapse-hub verify         # Run 9 Quality Gates DoD (Gate 0–8)
npx synapse-hub analyze        # 5-in-1 Comprehensive Project Health Audit
agent-qa export-excel          # Export test cases to formatted Excel (.xlsx)
```

---

## 💎 Breakthrough Architectural Pillars

```mermaid
flowchart TD
    subgraph Hub["🧠 Synapse Hub (Intelligence Core v2.3.0)"]
        Skills[".agents/skills/ (29 Skills)"]
        Agents[".agents/agents/ (6 Specialized Roles)"]
        Rules[".agents/rules/ (10 Core Rules)"]
        Tools["tools/ (50+ Universal Python Tools)"]
        Workflows[".agents/workflows/ (7 Workflows)"]
        Practices["examples/practices/ (Corpus)"]
    end

    subgraph ChatSession["💬 AI Agent Workspace / Chat Session"]
        Hub -->|Mount/Add Workspace| ChatSession
    end

    subgraph Projects["📁 Target Projects"]
        ProjectA["Project A<br/>(PROJECT_AI_GUIDE.md + Source Code)"]
        ProjectB["Project B<br/>(PROJECT_AI_GUIDE.md + Test Code)"]
        Other["Other Projects..."]
    end

    ProjectA -->|Mount Workspace| ChatSession
    ProjectB -.->|Mount Workspace| ChatSession
    Other -.->|Mount Workspace| ChatSession
```

### 1. 🧠 System-2 Reasoning & Cognitive Forcing
- **Eliminates Unconscious Autocomplete:** Forces AI through a 4-step thinking protocol: *Invariant Extraction ➔ Popper Falsification ➔ Self-Debate ➔ Defensive Synthesis*.
- **Red-Team vs Blue-Team Mutation Testing:** Injects AST micro-mutants (`tools/micro_mutator.py`), rejecting test suites with **Mutation Score < 80%**.

### 2. ⚡ Radical Token Optimization (85% – 95% Context Savings)
- **95% Log Distillation:** `tools/distill_log.py` compresses 3,000 noise lines to ~10 actionable exception lines (< 50 tokens).
- **90% AST Repo Mapping:** `tools/repo_map.py` compresses 500+ method signatures to < 600 tokens; no reading 4,000-line monolithic files.
- **Zero-Token Episodic SQLite Memory:** Query solutions offline via vector cosine similarity (`~/.agent_memory/global_cache.db`).

| Metric | Naive AI Coding | With Synapse Hub 🧠 | Verification Proof |
| :--- | :---: | :---: | :--- |
| **Token Cost / Bug Fix** | 15k – 40k tokens | **300 – 800 tokens** | Micro-turn payload via `distill_log.py` + `repo_map.py`. |
| **Fake-Pass Rate** | 30% – 50% | **0% (Blocked)** | Gate 0 & 7 (`infer_linter.py`) + Gate 8 Mutation Score ≥ 80%. |
| **Cross-Session Fix Memory** | Forgotten immediately | **Persistent in SQLite** | Offline cosine cache in `~/.agent_memory/global_cache.db`. |
| **Mean Time-to-Heal (MTTR)** | 5 – 15 minutes | **< 1s on cache hits** | Pre-cached resolutions resolve in 0.1s. |

> 📝 **Measurement Methodology & Scope:** The figures above are **internal self-measurements**, captured via the Hub's own harness (`benchmarks/qa_eval/eval_runner.py` — 25 standardized challenges; `tools/distill_log.py`; `tools/repo_map.py`) on the bundled sample corpus, and are **not independently verified by any third party**. Real-world results vary by project, stack, and log/test size. Reproduce them on your own project with `agent-qa verify` + the benchmark harness before making decisions based on these numbers.

---

## 👥 Multi-Agent Swarm System (6 Specialized Roles)

| Agent Role | Core Responsibility | Key Skills | Primary Tools |
| :--- | :--- | :--- | :--- |
| **`orchestrator`** | Swarm lead, bootstrapping, health auditing, state anchoring. | `agent-orchestration`, `graphify`, `adr` | `setup_project.py`, `analyze_project.py`, `repo_map.py` |
| **`live-explorer`** | Headless DOM/AOM probing, destructive click firewall. | `playwright-live`, `self-healing`, `visual-diff` | `safety_firewall.py`, `browser_helpers.js` |
| **`pom-crafter`** | Clean POM, API drift detection, User Story to test compiler. | `clean-pom`, `lam-script`, `synthetic-data` | `generate_tc_from_story.py`, `api_drift_sentinel.py` |
| **`test-runner`** | Headless CLI suite manager, CI sharding, log filtering. | `katalon-cli`, `e2e-patterns`, `flaky-sentinel` | `matrix_sharder.py`, `distill_log.py`, `pinpoint_failure.py` |
| **`failure-analyst`**| Closed-loop failure autopsy, healing PR automator. | `failure-autopsy`, `self-healing-locator` | `auto_heal.py`, `heal_pr_automator.py`, `cache_resolver.py` |
| **`quality-gatekeeper`**| 9 Quality Gates DoD (Gate 0–8), fake-pass scan, mutation testing. | `antigravity-sentinel`, `skillspector`, `dast` | `verify_all.py`, `infer_linter.py`, `micro_mutator.py` |

---

## 📦 Complete Skills, Workflows & Tools Catalog

<details>
<summary><b>📦 Click to expand: 29 Standardized Skills (.agents/skills/)</b></summary>

| # | Skill Name | Operational Scope |
|:---:|---|---|
| 1 | `agent-orchestration-multi-agent-optimize` | Multi-agent coordination profiling, workload distribution, and token cost budgeting. |
| 2 | `antigravity-test-sentinel` | Verification-First sentinel, locking task completion until exit code 0 is proven. |
| 3 | `api-network-mocking-interception` | HTTP/GraphQL request interception, route stubbing, and chaos network resilience testing. |
| 4 | `api-spec-to-e2e-matrix` | Transforms OpenAPI/Swagger specifications into equivalence, boundary, and error test matrices. |
| 5 | `architecture-decision-records` | Documents and maintains technical Architecture Decision Records (ADR). |
| 6 | `auth-session-and-cookie-manager` | Manages sessions, JWT tokens, and storageState for zero-second authentications. |
| 7 | `backend-load-and-stress-patterns` | Backend load/stress testing via k6 & Locust with P95/P99 SLA threshold assertions. |
| 8 | `bats-testing-patterns` | Automated testing for Shell scripts, CI/CD pipelines, CLI mocks, and exit codes. |
| 9 | `clean-pom-crafter` | Clean Page Object Model standards, Flat Architecture, and dynamic `uniqueCode` test data. |
| 10 | `code-refactoring-refactor-clean` | Clean code refactoring, code smells elimination, technical debt remediation, and SOLID. |
| 11 | `db-state-verifier-and-seeder` | Direct DB state assertions (PostgreSQL, MySQL, MongoDB, Redis) and isolated fixtures. |
| 12 | `e2e-testing-patterns` | Multi-browser E2E testing architecture (Playwright/Cypress), Typed POM, parallel sharding. |
| 13 | `failure-autopsy-and-healing` | Automated failure triage from JUnit XML, Allure reports, and visual error screenshots. |
| 14 | `file-and-report-validator` | Verifies uploaded/downloaded files (Excel .xlsx, streaming CSV, PDF text/layout). |
| 15 | `flaky-test-sentinel-and-quarantine` | Flaky test detection, flakiness index scoring, and quarantine isolation governance. |
| 16 | `github-actions-templates` | Production-ready GitHub Actions CI/CD workflows and sharded testing matrix. |
| 17 | `graphify-impact-analyzer` | AST Knowledge Graph navigation and zero-waste test impact analysis. |
| 18 | `katalon-cli-runner` | Headless KRE CLI execution coordinator, licensing fallback, and zombie driver cleanup. |
| 19 | `lam-script-generator` | Large Action Model generator compiling User Stories into 100% test scripts with zero replay. |
| 20 | `playwright-live-interaction` | Real-time DOM/AOM probing via Playwright MCP with sub-200ms selector verification. |
| 21 | `security-dast-sentinel` | Dynamic Application Security Testing (DAST), OWASP Top 10, Security Headers, BOLA/IDOR. |
| 22 | `self-healing-locator` | Micro-locator self-healing via Accessibility Tree (AOM), Role > Label > TestId hierarchy. |
| 23 | `synthetic-test-data-generator` | Robust synthetic boundary test data generation (BVT, anti-injection, multilingual, GIS). |
| 24 | `token-and-context-optimizer` | Context engineering, 95% log distillation, anti-degradation, and disk scratchpads. |
| 25 | `visual-regression-sentinel` | Pixel-level and SSIM visual regression testing with dynamic masking. |
| 26 | `wcag-audit-patterns` | Automated WCAG 2.2 Level A/AA accessibility auditing via AST and `@axe-core`. |
| 27 | `web-vitals-and-performance-profiler` | Core Web Vitals (LCP, CLS, TTFB) profiling and slow API endpoint detection via CDP. |
| 28 | `skillspector-security-guard` | AI agent skill & MCP config security auditing against 71 vulnerability vectors (Prompt Injection, Data Exfiltration, Privilege Escalation) powered by NVIDIA SkillSpector spec. |
| 29 | `rbt-manual-testing` | 6-stage Risk-Based Testing (AI-RBT) manual test case synthesis, P × I risk scoring, Ambiguity Q&A log, 12-column matrix, 15-field validation checklist, and non-functional resilience scenarios (Double-Submit, Race Conditions). |

</details>

<details>
<summary><b>📋 Click to expand: 7 Production Workflows (.agents/workflows/)</b></summary>

| Workflow | Core Engineering Purpose |
| :--- | :--- |
| **`generate_manual_testcases_rbt.md`** | Comprehensive 6-stage AI-RBT manual test generation with P × I risk scoring and 12-column table output. |
| **`generate_testcases_from_requirements.md`** | Direct compilation of requirement documents (SRS, PRD, User Stories) into acceptance test suites. |
| **`generate_cross_module_test_plan.md`** | E2E integration test planning across interconnected modules (Cart ➔ Checkout ➔ Payment ➔ Warehouse). |
| **`generate_combinatorial_test_data.md`** | All-Pairs / Pairwise test data generation optimizing boundary coverage with minimal test cases. |
| **`generate_requirements_from_website.md`** | Autonomous reverse-engineering of functional specs from live web pages via headless Playwright probing. |
| **`analyze_requirement_document.md`** | Static requirements linter surfacing logic contradictions, edge-case gaps, and ambiguity debt. |
| **`export_testcases_excel.md`** | Automated conversion of Markdown test cases into professionally styled Excel spreadsheets (.xlsx) via OpenPyXL. |

</details>

<details>
<summary><b>📜 Click to expand: 10 Core Rules (.agents/rules/)</b></summary>

1. **`context-engineering.md`**: Observation masking, lazy progressive disclosure, and KV-cache optimization.
2. **`git-push-protocol.md`**: Clean git push protocol (decoupled architecture guarantees zero AI leakage).
3. **`graphify.md`**: Navigating the AST knowledge graph over reading entire large source files.
4. **`lessons-learned.md`**: Episodic anti-pattern blacklist (strictly capped under 40 lines).
5. **`mandatory-playwright-live.md`**: Mandatory headless Full HD 1920x1080 and live DOM probing before codifying.
6. **`skill-precedence.md`**: Tier-1 local skill precedence resolving external plugin collisions.
7. **`systematic-debugging.md`**: Evidence-first debugging discipline; zero guessing; 9 Quality Gates DoD.
8. **`author-integrity-guard.md`**: Mandatory MIT copyright notice preservation and anti-plagiarism guard.
9. **`mobile_appium_rules.md`**: Native mobile automation rules (Appium, Screen Object Model, iOS/Android locator hierarchy, smart synchronization, app lifecycle handling).
10. **`performance_testing_rules.md`**: Enterprise load & performance testing invariants (k6/JMeter/Locust, mandatory pre-flight approval, hard caps, `abortOnFail` kill-switch, open/closed workload modeling, third-party isolation, and Truth Anchor reporting).

</details>

<details>
<summary><b>🛠️ Click to expand: 50+ Specialized Python Tools (tools/)</b></summary>

For full details, refer to [tools/TOOLS_RUNBOOK.md](tools/TOOLS_RUNBOOK.md):

- `tools/verify_all.py`: 9 Quality Gates DoD verification (Gate 0–8: UTF-8, No XPaths, UniqueCode, Clean POM, AST Mutation).
- `tools/md_to_xlsx.py` (`agent-qa export-excel`): Converts Markdown test cases to styled corporate Excel workbooks (.xlsx) with frozen panes and priority badges.
- `tools/generate_jmx_plan.py`: Multi-protocol Apache JMeter 5.x (.jmx) plan generator (HTTP, JDBC, WS, gRPC, Kafka) with Pareto traffic shaping.
- `tools/jtl_analyzer.py`: JTL execution metrics analyzer, P95/P99 SLA gatekeeper, and CI/CD Quality Gate enforcer.
- `tools/telemetry_correlator.py`: Full-stack Pearson correlation analyzer between client-side latency and server APM (CPU, RAM, DB Pool).
- `tools/export_postman_collection.py`: Exports Postman Collections v2.1 with native AJV JSON Schema, DDT CSV, and Zero-Input domain synthesis.
- `tools/newman_analyzer.py`: Newman automated test results analyzer, assertion failure triage, and CI/CD Quality Gate.
- `tools/api_fuzzer.py`: Autonomous API fuzzer detecting HTTP 500 crashes, database stacktrace leaks, and latency SLA breaches.
- `tools/api_drift_sentinel.py`: Contract drift detector comparing OpenAPI/Swagger specifications for breaking changes.
- `tools/auto_heal.py`: In-place locator self-healing engine correlating JUnit XML and screenshots via AOM diffing.
- `tools/flaky_detector.py`: Flaky test detector and automated quarantine lifecycle manager.
- `tools/skillspector.py`: AI Agent Skill & MCP Security Sentinel (71 detection vectors, Prohibition Context Engine, SARIF/JSON reporting).
- `tools/omni_transpiler.py`: 0-token polyglot test transpiler (Playwright TS/Python, Java, Groovy, Cypress).
- `tools/infer_linter.py`: Static AST analysis detecting fake passes (zero asserts) and empty catch blocks.
- `tools/test_impact.py`: Scopes affected test cases based on git diffs.
- `tools/cache_resolver.py`: Manages the central SQLite error memory cache (`~/.agent_memory/global_cache.db`).
- `tools/distill_log.py`: Filters 95% noise from CLI/Gradle/KRE logs, preserving stacktraces and pointers.
- `tools/agent_canary.py`: Injects 8 failure vectors to benchmark MTTR and autonomous recovery rate.
- `tools/repo_map.py`: Extracts a compressed method and Page Class map (~500 tokens).
- `tools/visual_diff_canvas.py`: Pixel/SSIM comparison for canvas/GIS interfaces lacking standard DOM.
- `tools/wcag_audit.py`: Automated scanning for WCAG 2.2 Level A/AA criteria.
- `tools/generate_api_matrix.py`: Generates positive, boundary, and negative test matrices from Swagger/OpenAPI.
- `tools/generate_tc_from_story.py`: Large Action Model parser generating Clean POM skeletons from stories.
- `tools/trace_data_flow.py`: Taint analysis tracking test data flow and preventing database orphan junk.
- `scripts/install.ps1` & `scripts/setup.sh`: 1-click bootstrap scripts setting up the hub environment.
- `scripts/lint_skills.ps1`: Linter verifying skill integrity across 29 skills and metadata manifest.
- `pyproject.toml` & `tools/cli.py`: PEP 621 packaging for the global `agent-qa` CLI.

</details>

<details>
<summary><b>🤝 Click to expand: Acknowledgments & Upstream Inspirations</b></summary>

| Project & Author | Architectural Inspiration in Synapse Hub |
| :--- | :--- |
| **[NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector)** *(NVIDIA AI Security Team)* | AI Agent skill & MCP security vetting engine (`tools/skillspector.py`, Skill #28 `skillspector-security-guard`) featuring 71 vulnerability vectors across 17 categories and the Prohibition Context Engine. |
| **[muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)** | Context Engineering foundations, observation masking, and LLM attention budget optimization. |
| **[alexgreensh/token-optimizer](https://github.com/alexgreensh/token-optimizer)** | Token-efficient reasoning, 95% log distillation, and KV-cache serialization protocols. |
| **[obra/superpowers](https://github.com/obra/superpowers)** *(Jesse Vincent)* | Systematic evidence-based debugging, cognitive forcing functions, and Red-Team vs Blue-Team verification. |
| **[Aider-AI/aider](https://github.com/Aider-AI/aider)** *(Paul Gauthier)* | Ultra-compact AST repository mapping algorithm (`tools/repo_map.py`) fitting 500+ signatures in < 600 tokens. |
| **[lavague-ai/LaVague](https://github.com/lavague-ai/LaVague)** | Large Action Model (LAM) concept compiling natural language stories into deterministic Clean POM scripts. |
| **[facebook/infer](https://github.com/facebook/infer)** *(Meta Infer)* | Static AST defect sentinel (`tools/infer_linter.py`) catching swallowed exceptions and 0-assertion fake passes. |
| **[microsoft/playwright](https://github.com/microsoft/playwright)** | Sub-200ms headless live DOM/AOM probing, route stubbing, and anti-flake network shielding. |
| **[dequelabs/axe-core](https://github.com/dequelabs/axe-core)** | Automated accessibility rule heuristics inspiring WCAG 2.2 Level A/AA AST auditing. |
| **[bats-core/bats-core](https://github.com/bats-core/bats-core)** | Bash Automated Testing System patterns for CI/CD pipelines and cross-platform CLI verification. |
| **[npryce/adr-tools](https://github.com/npryce/adr-tools)** | Architecture Decision Record (ADR) conventions and lifecycle workflows. |

</details>

---

## 📚 Technical Documentation & CLI Package (docs/)

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Hub/Spoke architecture, 4-tier skill model, and 6-agent swarm coordination.
2. **[docs/TOKEN_QUOTA_PLAYBOOK.md](docs/TOKEN_QUOTA_PLAYBOOK.md)**: Model tiering strategy (Claude Sonnet vs Gemini Pro vs Gemini Flash) and quota-conscious execution modes.
3. **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Contribution standards, new skill authoring principles, and verification pipelines.
4. **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)**: Comprehensive command-line reference for the `agent-qa` CLI.

### Quick CLI Installation:
```bash
pip install -e .
agent-qa --help
agent-qa verify
agent-qa export-excel
```

---

## 📄 License & Author Attribution

This project is licensed under the **[MIT License](LICENSE)**.

**Provenance & Copyright Notice:**
- **Author & Founder:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))
- **Original Repository:** [https://github.com/TeeVee998/Synapse-Hub](https://github.com/TeeVee998/Synapse-Hub)
- **Copyright:** Copyright (c) 2026 Thế Vị (@TeeVee998). Distributed under the MIT License.

> ⚖️ **MIT License Attribution Requirement:** Under the terms of the MIT License, you are granted permission to use, copy, modify, merge, publish, and distribute this software freely, **PROVIDED** that the original copyright notice crediting **Thế Vị (@TeeVee998)** and this permission notice are included in all copies or substantial portions of the Software.
