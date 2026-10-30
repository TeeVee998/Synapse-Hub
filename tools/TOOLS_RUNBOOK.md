# TOOLS RUNBOOK — Automated Tools Handbook for AI Agents

> **Standard reference guide for AI Agents (Google Antigravity, Cursor, Claude Code, Windsurf)**  
> Every script in the `tools/` directory has an explicit purpose, CLI syntax, and mandatory dispatch trigger. Guessing syntax is strictly prohibited.

---

## 1. SITUATIONAL TOOL DISPATCH MATRIX

| Practical Agent Context | Required Tool | Typical Execution Command |
| :--- | :--- | :--- |
| **Autonomous Bootstrap (New project / "setup project")** | `tools/setup_project.py` | `python tools/setup_project.py [target]` (or `agent-qa setup`).<br/>*Autonomous:* Detects stack, generates `PROJECT_AI_GUIDE.md`, installs `pre-push` Git hook, runs initial audit. |
| **Comprehensive Health & AST Analysis ("analyze project")** | `tools/analyze_project.py` | `python tools/analyze_project.py [target]` (or `agent-qa analyze`).<br/>*Post-Audit:* Stages, commits, and pushes `PROJECT_HEALTH_REPORT.md` & `repo_map.txt` to project Git. |
| **Action Safety Firewall (Environment Protection)** | `tools/safety_firewall.py` | `python tools/safety_firewall.py --text "Delete" --action click` (or `agent-qa safety-check`) |
| **API Contract Drift (Breaking Change Detection)** | `tools/api_drift_sentinel.py` | `python tools/api_drift_sentinel.py --old base.json --new curr.json` (or `agent-qa contract-drift`) |
| **Autonomous API Fuzzing & Chaos Breaker** | `tools/api_fuzzer.py` | `agent-qa fuzz-api --base-url <url> --spec <swagger.json>` (Catches 500, DB leaks, SLA breach) |
| **FastMCP JSON-RPC Server (Cursor/Claude/Antigravity)** | `tools/mcp_server.py` | `python tools/mcp_server.py` (or `agent-qa mcp-serve`) |
| **AST Micro-Mutation (Assertion Quality Verification)** | `tools/micro_mutator.py` | `python tools/micro_mutator.py [target]` (or `agent-qa mutate`) |
| **Self-Healing PR Automator (Trace & Visual Diff Proof)** | `tools/heal_pr_automator.py` | `python tools/heal_pr_automator.py --page P.groovy --old "//a" --new "//b" --trace-zip trace.zip` (or `agent-qa heal-pr`) |
| **Duration-Balanced Matrix Sharder (CI/CD Load Balancing)** | `tools/matrix_sharder.py` | `python tools/matrix_sharder.py [target] --shards 4` (or `agent-qa shard`) |
| **Enterprise ALM & TMS Sync Bridge (Jira/Xray/TestRail)** | `tools/tms_sync_bridge.py` | `python tools/tms_sync_bridge.py pull PROJ-1042` / `report-bug` |
| **Zero-Pollution DB Sandbox (Ephemeral Teardown)** | `tools/db_sandbox.py` | `python tools/db_sandbox.py snapshot` / `restore` / `rollback-test` |
| **Shift-Right Traffic Replay (HAR / RUM to Test)** | `tools/traffic_session_converter.py` | `python tools/traffic_session_converter.py session.har -o test.ts` |
| **Multimodal Vision Grounding & Zero-Token Cache (SoM)** | `tools/visual_som_helper.py` | `python tools/visual_som_helper.py --image shot.png --component "Submit" --cache-lookup` |
| **Edge-Case Fuzzing & Input Sanitization Suite** | `tools/fuzz_payloads.py` | `python tools/fuzz_payloads.py --field username --type string` |
| **Starting task / Querying Page Class methods** | `tools/repo_map.py` | `python tools/repo_map.py` (Reads `tools/repo_map.txt`) |
| **Pre-Commit / Completing Task** | `tools/verify_all.py` | `python tools/verify_all.py` |
| **After creating/editing Test Script (Fake-Pass scan)**| `tools/infer_linter.py` | `python tools/infer_linter.py` |
| **After modifying Page Class (Impact Analysis)** | `tools/test_impact.py` | `python tools/test_impact.py --git-diff` |
| **When Test FAILS (Pinpoint line & error in 0.1s)** | `tools/pinpoint_failure.py` | `python tools/pinpoint_failure.py` |
| **When CLI/Gradle logs are verbose (Observation Masking)**| `tools/distill_log.py` | `python tools/distill_log.py <path_to_log>` |
| **When encountering UI error / Overlay / Stale Element**| `tools/cache_resolver.py` | `python tools/cache_resolver.py query "<error_msg>"` |
| **Before authoring test for Page/Flow** | `tools/cache_resolver.py` | `python tools/cache_resolver.py get-lessons --context "<page>"` (or `agent-qa heal get-lessons --context "<page>"`) |
| **After healing a test failure** | `tools/cache_resolver.py` | `python tools/cache_resolver.py record-lesson --context "<page>" --error "<sig>" --lesson "<summary>"` |
| **Generating test scripts from Natural Language Story** | `tools/generate_tc_from_story.py`| `python tools/generate_tc_from_story.py "<story>"` |
| **Generating E2E matrix from OpenAPI/Swagger** | `tools/generate_api_matrix.py` | `python tools/generate_api_matrix.py --spec <swagger.json>` |
| **Exporting API tests to Postman Collection v2.1** | `tools/export_postman_collection.py` | `agent-qa export-postman --spec <swagger.json> -o col.json` |
| **Generating JMeter Performance Test Plan (.jmx)** | `tools/generate_jmx_plan.py` | `agent-qa generate-jmx --spec <swagger.json> --vus 100 -o plan.jmx` |
| **Analyzing JMeter JTL & Enforcing CI/CD SLA Gate** | `tools/jtl_analyzer.py` | `agent-qa analyze-jtl results.jtl --sla-p95 500 --max-error-rate 1.0` |
| **Full-Stack APM & Server Telemetry RCA Correlator** | `tools/telemetry_correlator.py` | `agent-qa correlate-telemetry --jtl results.jtl --server-metrics srv.csv` |
| **Auditing Web Accessibility (WCAG 2.2)** | `tools/wcag_audit.py` | `python tools/wcag_audit.py <path_to_html_or_url>` |
| **0-Token Polyglot Test Transpilation** | `tools/omni_transpiler.py` | `agent-qa transpile <file> --to <target>` (Playwright TS, Python, Java, Katalon, Cypress) |
| **0-Token Repository Polyglot AST Scan** | `tools/omni_transpiler.py` | `agent-qa omni-scan [path]` (Instant inventory of Pages, Locators, Tests across languages) |
| **Autonomous Legacy Suite Migration** | `tools/cli.py` | `agent-qa migrate --src ./katalon_project --dest ./playwright_ts` |
| **Environment & Secret Decoupling Engine** | `tools/config_decoupler.py` | `agent-qa decouple-config [target] --fix` (Extracts env.default.json & .env.example) |
| **Single Portable Binary Distribution** | `scripts/package_dist.py` | `python scripts/package_dist.py --binary` (Builds standalone omni-qc.exe) |
| **Autonomous Bug Report & Jira/Allure Ticket** | `tools/bug_reporter.py` | `agent-qa report-bug --title "<title>" --error "<msg>"` |
| **API Network Mocking & Chaos Shield** | `tools/network_mock_shield.py` | `agent-qa mock-shield --preset payment_success` |
| **Smart Visual Masking (Anti-Flake)** | `tools/smart_visual_masker.py` | `agent-qa visual-mask --playwright-snippet` |
| **CI/CD Silent Self-Healing Hook & Auto-PR** | `tools/ci_healing_hook.py` | `agent-qa ci-hook --file <f> --old-loc <old> --new-loc <new>` |
| **Checking DB data leaks (Taint Analysis)** | `tools/trace_data_flow.py` | `python tools/trace_data_flow.py` |
| **Detecting Canvas / GIS Map visual regression** | `tools/visual_diff_canvas.py` | `python tools/visual_diff_canvas.py --baseline <b> --actual <a>` |
| **Canary Self-Healing Audit** | `tools/agent_canary.py` | `python tools/agent_canary.py --run` |
| **Lookup XPath Locator in cached memory** | `tools/lookup_xpath.py` | `python tools/lookup_xpath.py "<keyword>"` |
| **Lookup Test Case metadata** | `tools/lookup_tc.py` | `python tools/lookup_tc.py "<keyword_or_id>"` |
| **Linting Markdown documentation quality** | `tools/lint_ai_docs.py` | `python tools/lint_ai_docs.py` |
| **Upstream Version Check & 1-Click Self-Update** | `tools/update_sentinel.py` | `python tools/update_sentinel.py --check / --update` (or `agent-qa update` / `npx synapse-hub update`) |

---

## 2. DETAILED TOOL USAGE

### 0. `tools/update_sentinel.py` (Upstream Update & Drift Sentinel)
Checks upstream releases on NPM Registry and GitHub, displaying non-blocking update notifications when a new version is published. Supports 1-click self-updating across local git repos and global plugins.

```bash
# Check if update is available without applying
python tools/update_sentinel.py --check
# or via CLI
agent-qa update --check

# Perform 1-click self-update (pulls git, syncs memory cache, verifies DoD)
python tools/update_sentinel.py --update
# or via CLI
agent-qa update
```

### 1. `tools/generate_api_matrix.py`
- **Purpose:** Ingests OpenAPI / Swagger JSON schemas and automatically computes comprehensive E2E test matrices: Positive, Boundary Value (min/max length, special characters, XSS payloads), and Negative (invalid types, missing required fields).
- **CLI Syntax:**
  ```bash
  # Generate Markdown matrix
  python tools/generate_api_matrix.py --spec path/to/swagger.json --format md -o api_matrix.md

  # Generate JSON matrix
  python tools/generate_api_matrix.py --spec path/to/swagger.json --format json -o api_matrix.json

  # Generate sample matrix using built-in schema
  python tools/generate_api_matrix.py --sample
  ```

---

### 2. `tools/wcag_audit.py`
- **Purpose:** Automated Web Accessibility auditor checking WCAG 2.2 Level A and AA criteria (missing alt tags, unlabeled form controls, table header structure, heading hierarchy gaps H1-H6, empty action buttons).
- **CLI Syntax:**
  ```bash
  # Audit local HTML snapshot
  python tools/wcag_audit.py path/to/page.html -o wcag_report.md

  # Audit live URL directly
  python tools/wcag_audit.py https://staging.example.com/dashboard --url -o wcag_report.md
  ```

---

### 3. `tools/verify_all.py`
- **Purpose:** Supreme Definition of Done (DoD) verification gate running all 8 Quality Gates (including AST Micro-Mutation >= 80%) prior to completing tasks or git commits. Supports dual operational modes (`hub` vs `target`) and dynamic target project resolution.
- **CLI Syntax:**
  ```bash
  # Auto-detection (automatically targets CWD if inside a test project, otherwise falls back to QA Hub)
  python tools/verify_all.py

  # Target a specific test project repository (positional or --repo / --path)
  python tools/verify_all.py "D:/katalon-project"
  python tools/verify_all.py --repo "D:/katalon-project"

  # Explicit mode execution
  python tools/verify_all.py --mode hub      # QA Hub integrity validation
  python tools/verify_all.py --mode target   # Enterprise target test suite validation
  ```

---

### 4. `tools/infer_linter.py`
- **Purpose:** AST static code analyzer detecting Fake-Pass anti-patterns (test cases without assertions or containing empty try-catch blocks swallowing errors).
- **CLI Syntax:**
  ```bash
  python tools/infer_linter.py
  ```

---

### 5. `tools/test_impact.py`
- **Purpose:** Analyzes `git diff` against codebase dependency graphs to identify the exact subset of affected test cases, preventing redundant suite execution.
- **CLI Syntax:**
  ```bash
  python tools/test_impact.py --git-diff
  ```

---

### 6. `tools/pinpoint_failure.py`
- **Purpose:** Extracts failing line numbers, exception names, and stack traces from JUnit XML reports in 0.1s without opening heavy files.
- **CLI Syntax:**
  ```bash
  python tools/pinpoint_failure.py
  ```

---

### 7. `tools/distill_log.py`
- **Purpose:** Distills verbose CLI / KRE / Gradle logs by 95%, extracting only actionable exceptions, failing lines, and file pointers to prevent token degradation.
- **CLI Syntax:**
  ```bash
  python tools/distill_log.py path/to/execution.log
  ```

---

### 8. `tools/cache_resolver.py`
- **Purpose:** Queries SQLite error cache (`tools/memory_cache.db`) via cosine similarity or pattern match for 0-token instant defect resolution.
- **CLI Syntax:**
  ```bash
  python tools/cache_resolver.py query "ElementClickInterceptedException"
  python tools/cache_resolver.py add --pattern "Timeout waiting for primeNG" --fix "BasePage.waitForAngular()"
  ```

---

### 9. `tools/generate_tc_from_story.py`
- **Purpose:** Large Action Model (LAM) parser converting natural language acceptance criteria into Clean POM script scaffolds.
- **CLI Syntax:**
  ```bash
  python tools/generate_tc_from_story.py "User navigates to login, inputs valid credentials, and verifies dashboard table loaded"
  ```

---

### 10. `tools/visual_diff_canvas.py`
- **Purpose:** Pixel-level and SSIM perceptual comparison for GIS / Canvas elements lacking standard DOM locators.
- **CLI Syntax:**
  ```bash
  python tools/visual_diff_canvas.py --baseline baseline.png --actual actual.png --diff diff.png
  ```

---

### 11. `tools/analyze_project.py`
- **Purpose:** Comprehensive 5-in-1 Project Health & AST Intelligence Suite. Aggregates environment checks (`check_env`), Page Class AST mapping (`repo_map`), Static Defect Sentinel (`infer_linter`), Teardown Data Flow (`trace_data_flow`), and 8 Quality Gates (`verify_all`). Generates `reports/PROJECT_HEALTH_REPORT.md` and synchronizes all AI data context in < 1 second.
- **Trigger:** Whenever user says: "analyze project", "re-analyze project", "audit project", or during initial project onboarding.
- **CLI Syntax:**
  ```bash
  # Analyze current working directory or QA Hub
  python tools/analyze_project.py
  # Or use CLI shortcut
  agent-qa analyze

  # Analyze specific target project
  python tools/analyze_project.py "D:/katalon-project"
  python tools/analyze_project.py --repo "D:/katalon-project"
  ```


---

### 12. `tools/tms_sync_bridge.py`
- **Purpose:** Bi-directional Enterprise ALM Bridge connecting autonomous agents with Jira, Xray, and TestRail. Pulls Given-When-Then Acceptance Criteria from User Stories to seed tests, and automatically creates Bug Tickets with complete reproduction steps and screenshot attachments upon test failure.
- **CLI Syntax:**
  ```bash
  # Pull Acceptance Criteria from Jira Story
  python tools/tms_sync_bridge.py pull PROJ-1042

  # Create Bug Ticket with repro steps and failure screenshots
  python tools/tms_sync_bridge.py report-bug --project BILLING --tc-id TC-01 --summary "Payment failed" --error "Timeout" --screenshot "Screenshots/FAILED_TC-01.png"

  # Sync execution batch to Xray Test Plan
  python tools/tms_sync_bridge.py sync-run --plan-key XRAY-PLAN-1 --json
  ```

---

### 13. `tools/db_sandbox.py`
- **Purpose:** Zero-Pollution Database Sandbox and Ephemeral Teardown Engine. Takes pristine database baseline snapshots, instantly restores clean states (< 0.1s), runs tests inside transactional savepoints (automatic rollback), and audits/purges orphan test data junk.
- **CLI Syntax:**
  ```bash
  # Snapshot database before suite execution
  python tools/db_sandbox.py snapshot --id baseline

  # Restore pristine clean database after suite execution
  python tools/db_sandbox.py restore --id baseline

  # Execute SQL statements inside an isolated transaction savepoint (auto-rollback)
  python tools/db_sandbox.py rollback-test

  # Audit database for orphan test junk and purge
  python tools/db_sandbox.py audit
  ```


---

### 14. `tools/traffic_session_converter.py`
- **Purpose:** Shift-Right production traffic and user session converter. Converts recorded `.har` files or RUM network traces into executable Playwright test scripts, automatically sanitizing PII (passwords, tokens, credit cards) and eliminating static noise.
- **CLI Syntax:**
  ```bash
  # Convert HAR file into Playwright test script
  python tools/traffic_session_converter.py prod_session.har -o tests/e2e_replay.spec.ts

  # Output parsed network requests as JSON
  python tools/traffic_session_converter.py prod_session.har --json
  ```

---

### 15. `tools/visual_som_helper.py`
- **Purpose:** Multimodal Vision Grounding and Set-of-Marks (SoM) fallback engine. When standard DOM locators fail on HTML5 Canvas, GIS maps, WebGL charts, or deeply nested Shadow DOM, it autonomously detects interactive visual contours using PIL edge clustering, overlays numbered bounding box badges on screenshots, resolves target coordinates `(x, y)`, caches coordinates via 64-bit dHash in SQLite, and dispatches physical Playwright mouse clicks (`await page.mouse.click(x, y)`).
- **CLI Syntax:**
  ```bash
  # Autonomous Canvas contour detection without DOM
  python tools/visual_som_helper.py --image canvas_map.png --detect-only

  # Generate Set-of-Marks overlay and resolve target coordinates
  python tools/visual_som_helper.py --image screenshot.png --label "Execute Trade"

  # Zero-Token Visual Cache lookup (Similarity > 98%)
  python tools/visual_som_helper.py --image screenshot.png --component "TradeButton" --cache-lookup
  ```

---

### 16. `tools/api_fuzzer.py`
- **Purpose:** Autonomous runtime API fuzzer and chaos breaker. Ingests OpenAPI 3.x / Swagger 2.0 schemas, generates dynamic boundary, type-inverted, and adversarial fuzzing payloads from `tools/fuzz_payloads.py`, executes live HTTP/S requests against staging/test APIs, and evaluates three-alarm defect Oracle: HTTP 500 crashes, database stacktrace leaks, and SLA latency timeouts (> 3000ms).
- **CLI Syntax:**
  ```bash
  # Execute active fuzzing against staging API
  agent-qa fuzz-api --base-url "https://staging.api.enterprise.com" --spec swagger.json --token "JWT_SECRET"

  # Air-gapped / deterministic dry-run mode for CI/CD
  agent-qa fuzz-api --dry-run
  ```

---

### 16. `tools/omni_transpiler.py`
- **Purpose:** Universal Polyglot AST Engine & Cross-Framework Transpiler. Allows a single QA engineer to parse, inventory, and transpile test automation code across Java (Selenium), TypeScript (Playwright), Python, Groovy (Katalon Clean POM), and Cypress in 0 tokens without network calls or LLM hallucinations.
- **CLI Syntax:**
  ```bash
  # Transpile legacy Java Selenium Page Object into Playwright TypeScript
  agent-qa transpile src/test/java/pages/LoginPage.java --to playwright-ts --out src/

  # Transpile Katalon Groovy script into Selenium Java
  agent-qa transpile Keywords/pages/CheckoutPage.groovy --to selenium-java

  # 0-Token Polyglot AST Inventory of entire repository (regardless of language)
  agent-qa omni-scan .
  ```

---

### 17. `tools/bug_reporter.py`
- **Purpose:** Auto-Bug Reporter & Root Cause Analysis (RCA) Ticket Generator. Automatically distinguishes AUT bugs (server 500, JS exceptions) from test maintenance issues, distills stack traces, formats reproduction steps, and exports ready-to-paste Jira markup or GitHub Markdown.
- **CLI Syntax:**
  ```bash
  agent-qa report-bug --title "Checkout payment fails" --error "500 Internal Server Error" --format jira
  ```

---

### 18. `tools/network_mock_shield.py`
- **Purpose:** API Network Mocking & Chaos Shield Generator. Generates zero-token route interception code and chaos fault injection (Stripe/VNPAY payment success/fail, 401/403 auth, 500 server crash, network latency) for Playwright, Cypress, and Python.
- **CLI Syntax:**
  ```bash
  agent-qa mock-shield --preset payment_success --url "**/api/checkout"
  agent-qa mock-shield --preset server_crash_500 --delay 2000
  ```

---

### 19. `tools/smart_visual_masker.py`
- **Purpose:** Smart Visual Masker & Anti-Flake Engine. Eliminates 99% of false alarms in visual regression testing by disabling CSS animations, freezing SVG spinners, and masking dynamic timestamps, clocks, and avatars.
- **CLI Syntax:**
  ```bash
  agent-qa visual-mask --playwright-snippet
  agent-qa visual-mask --css
  ```

---

### 20. `tools/ci_healing_hook.py`
- **Purpose:** CI/CD Silent Self-Healing Pipeline Hook. Executes inside GitHub Actions / GitLab CI when a locator fails, applies in-place auto-heal, and generates an automated Pull Request draft with diff and confidence score.
- **CLI Syntax:**
  ```bash
  agent-qa ci-hook --file LoginPage.ts --old-loc "//button[@id='old']" --new-loc "//button[@id='new']"
  ```

---

### 21. `tools/export_postman_collection.py`
- **Purpose:** Enterprise OpenAPI/Swagger & HAR to Postman Collection v2.1.0 Exporter. Generates fully structured Postman collections with dynamic pre-request scripts, SLA latency tests, response code assertions, and autonomous bearer token / created entity ID extraction for Newman and CI/CD pipelines.
- **CLI Syntax:**
  ```bash
  # Ingest OpenAPI spec and export Postman collection + companion environment
  agent-qa export-postman --spec swagger.json -o collection.json --env-output env.json

  # Replay production HAR traffic as Postman requests
  agent-qa export-postman --har session.har -o har_collection.json

  # Generate sample collection from built-in enterprise schema
  agent-qa export-postman --sample -o sample_collection.json
  ```

---

### 22. `tools/generate_jmx_plan.py`
- **Purpose:** Apache JMeter 5.x Performance Test Plan XML (.jmx) Generator (JMeter 360° Pinnacle Suite). Ingests OpenAPI specifications, Postman Collections, or HAR recordings to output production-ready JMeter load, stress, spike, and soak test plans with HTTP Cookie & Cache Managers, CSV Data Set Config, Transaction Controllers, Pareto Traffic Shaping (`--weighted-mix`), Deep Data Correlation (CSRF regex & random dynamic selectors), JSR223 Groovy HMAC payload signers, InfluxDB live APM telemetry, PerfMon server agent monitoring, and Multi-Protocol support (HTTP, JDBC, WebSocket, gRPC, Kafka).
- **CLI Syntax:**
  ```bash
  # 1. Generate JMeter plan with Pareto traffic shaping (70% Browse, 20% Cart, 10% Checkout)
  agent-qa generate-jmx --spec swagger.json -o load_plan.jmx --weighted-mix "70:Browse,20:Cart,10:Checkout"

  # 2. Convert existing Postman collection with CSV data & Deep Correlation (CSRF + random items)
  agent-qa generate-jmx --postman collection.json -o perf_plan.jmx --csv-data users.csv --deep-correlation

  # 3. Generate multi-protocol test plans (WebSocket, gRPC, Kafka, JDBC)
  agent-qa generate-jmx --ws-sample -o websocket_plan.jmx
  agent-qa generate-jmx --grpc-sample -o grpc_plan.jmx
  agent-qa generate-jmx --kafka-sample -o kafka_plan.jmx
  agent-qa generate-jmx --jdbc-sample -o jdbc_plan.jmx

  # 4. Generate with live InfluxDB streaming & PerfMon Server Agent
  agent-qa generate-jmx --spec swagger.json -o perf_plan.jmx --influxdb-url http://influxdb:8086/write?db=jmeter --perfmon-server 192.168.1.50:4444

  # 5. Run headless JMeter CLI
  jmeter -n -t load_plan.jmx -l results.jtl -e -o ./html_report
  ```

---

### 23. `tools/jtl_analyzer.py`
- **Purpose:** Apache JMeter JTL Results Analyzer & CI/CD SLA Quality Gatekeeper. Parses `.jtl` (CSV or XML), computes statistical percentiles ($P_{50}, P_{90}, P_{95}, P_{99}$, Throughput, Error Rate), evaluates user SLA thresholds, supports server telemetry correlation (`--telemetry`), and returns deterministic exit code `0` (Pass) or `1` (Fail) to enforce quality gates in automated pipelines.
- **CLI Syntax:**
  ```bash
  # 1. Enforce CI/CD Quality Gate with P95 Latency SLA (< 500ms) and max error rate (< 1%)
  agent-qa analyze-jtl results.jtl --sla-p95 500 --max-error-rate 1.0

  # 2. Correlate with Server-Side APM Telemetry directly in Quality Gate
  agent-qa analyze-jtl results.jtl --sla-p95 500 --telemetry server_metrics.csv --markdown pr_report.md

  # 3. Dry-run sample benchmark verification
  agent-qa analyze-jtl --sample --sla-p95 500
  ```

---

### 24. `tools/telemetry_correlator.py`
- **Purpose:** Full-Stack APM & Server Telemetry Performance Correlator. Performs time-aligned Pearson correlation between Client-Side perceived response times (`.jtl`) and Server-Side infrastructure metrics (CPU, RAM, Database Connection Pool, Disk I/O). Automatically isolates bottlenecks and produces Root Cause Analysis (RCA) diagnostic reports.
- **CLI Syntax:**
  ```bash
  # Correlate client JTL latency with server infrastructure telemetry
  agent-qa correlate-telemetry --jtl results.jtl --server-metrics server_metrics.csv --markdown rca_report.md

  # Dry-run sample correlation verification
  agent-qa correlate-telemetry --sample
  ```

