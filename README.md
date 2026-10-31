# 🧠 Synapse Hub — Trung Tâm Trí Tuệ & Mạng Lưới Kỹ Năng Cho AI Agent

[🇻🇳 Tiếng Việt](README.md) | [🇬🇧 English Edition](README.en.md)

> **Bộ não trí tuệ dùng chung và mạng lưới kỹ năng tự hành, tăng cường năng lực cho các trợ lý AI (Google Antigravity, Cursor, Windsurf, Claude Code) trên mọi hệ sinh thái kiểm thử tự động.**  
> **Tác giả:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))  
> **Phiên bản Hub:** `v2.3.0` | **Quy mô:** 29 Kỹ năng chuẩn hóa, 7 Workflows, 6 Vai trò AI Swarm, 10 Quy tắc cốt lõi, 50+ Công cụ tự động, 9 Cổng kiểm định DoD.

[![npm version](https://img.shields.io/npm/v/synapse-hub.svg?style=flat-square&color=blue)](https://www.npmjs.com/package/synapse-hub)
[![node version](https://img.shields.io/badge/node-%3E%3D16.0.0-brightgreen.svg?style=flat-square)](https://nodejs.org)
[![license](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](https://github.com/TeeVee998/Synapse-Hub/blob/main/LICENSE)

---

## ⚡ 1. Khởi Động Siêu Tốc Trong 30 Giây (All-in-One 🚀)

*Không cần clone repo Hub, không cần mở Multi-root workspace phức tạp. Cấu hình dự án tự động trong 5 giây:*

Mở terminal ngay tại thư mục **dự án kiểm thử của bạn** và chạy đúng 1 lệnh:
```bash
npx synapse-hub setup
```

👉 **Đúng 1 lệnh này sẽ tự động hoàn tất toàn bộ trong 5 giây:**
1. 🧠 **Bơm thẳng vào Antigravity Global Plugin:** Triển khai vào `~/.gemini/config/plugins/synapse-hub`. Kể từ đây, **mọi dự án** mở trên Google Antigravity đều tự động sở hữu toàn bộ 29 Skills và 6 Subagents!
2. 🌐 **Triển khai Cầu nối Đa AI (Universal AI Bridges):** Tự sinh luật cho Cursor (`.cursor/rules/`), Claude Code (`CLAUDE.md`), GitHub Copilot (`.github/copilot-instructions.md`), và Windsurf (`.windsurfrules`).
3. 📋 **Sinh Hướng dẫn & Cổng Git:** Tạo file `PROJECT_AI_GUIDE.md` và cài đặt Git Hook pre-push ngăn code lỗi.
4. 💾 **Khởi tạo Bộ nhớ Ngoại tuyến:** Nạp sẵn tri thức sửa lỗi vào SQLite `~/.agent_memory/global_cache.db` (chi phí 0 token).

### Thực thi kiểm định ngay:
```bash
npx synapse-hub verify         # Kiểm tra 9 Cổng Chất Lượng DoD (Gate 0–8)
npx synapse-hub analyze        # Báo cáo sức khỏe toàn diện dự án (5-in-1 Health Report)
agent-qa export-excel          # Xuất báo cáo Test Cases sang Excel (.xlsx) chuẩn doanh nghiệp
```

---

## 💎 2. Ba Trụ Cột Đột Phá Của Synapse Hub

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

    subgraph Projects["📁 Các Dự Án Mục Tiêu (Target Projects)"]
        ProjectA["Dự án A<br/>(PROJECT_AI_GUIDE.md + Source Code)"]
        ProjectB["Dự án B<br/>(PROJECT_AI_GUIDE.md + Test Code)"]
        Other["Dự án khác..."]
    end

    ProjectA -->|Mount Workspace| ChatSession
    ProjectB -.->|Mount Workspace| ChatSession
    Other -.->|Mount Workspace| ChatSession
```

### 🧠 Trụ cột 1: Tư Duy Chiều Sâu (System-2 Reasoning & Chống Pass Ảo)
- **Xóa bỏ chế độ "Autocomplete vô thức":** Buộc AI đi qua chu trình 4 bước: *Trích xuất bất biến ➔ Giả định phản nghiệm ➔ Tự phản biện ➔ Sinh mã phòng vệ*.
- **Tự đối kháng Red-Team vs Blue-Team:** Tiêm đột biến AST (`tools/micro_mutator.py`) vào kịch bản test; bắt buộc **Điểm đột biến (Mutation Score) ≥ 80%** mới cho phép nghiệm thu task.

### ⚡ Trụ cột 2: Tiết Kiệm Token Triệt Để (Cắt Giảm 85% – 95% Chi Phí Context)
- **Lọc 95% Log thừa:** `tools/distill_log.py` nén 3.000 dòng log CLI/Gradle chỉ còn ~10 dòng chứa stacktrace cốt lõi (< 50 tokens).
- **Nén 90% AST Repo Map:** `tools/repo_map.py` nén 500+ hàm vào bản đồ < 600 tokens; AI không bao giờ phải đọc cả file 4.000 dòng gây tràn context.
- **Zero-Token SQLite Memory:** Lưu và tra cứu kinh nghiệm sửa bug qua vector cosine similarity ngoại tuyến tại `~/.agent_memory/global_cache.db` (0 token context).

### 📊 So sánh hiệu quả thực tế:

| Tiêu chí đánh giá | Cách làm thông thường (Naive Prompting) | Khi sử dụng Synapse Hub 🧠 | Phương pháp kiểm chứng |
| :--- | :---: | :---: | :--- |
| **Token tiêu thụ / lần fix bug** | 15.000 – 40.000 tokens | **300 – 800 tokens** | Đo trên micro-turn fix locator qua `distill_log.py` + `repo_map.py`. |
| **Tỷ lệ Fake-Pass (pass ảo)** | 30% – 50% | **0% (Bị chặn đứng)** | Gate 0 & 7 (`infer_linter.py`) + Gate 8 Mutation Score ≥ 80%. |
| **Bộ nhớ sửa lỗi liên phiên** | Mất sạch khi mở chat mới | **Bền vững qua SQLite Cache** | Lưu ngoại tuyến tại `~/.agent_memory/global_cache.db`. |
| **Thời gian tự sửa lỗi (MTTR)** | 5 – 15 phút thử sai | **< 1s khi cache-hit** | Truy xuất giải pháp có sẵn trong < 0.1s. |

> 📝 **Phương pháp đo & phạm vi áp dụng:** Các con số trên là **tự đánh giá nội bộ**, đo qua chính harness của Hub (`benchmarks/qa_eval/eval_runner.py` — 25 challenges chuẩn hóa; `tools/distill_log.py`; `tools/repo_map.py`) trên corpus mẫu đi kèm, **chưa được kiểm chứng độc lập bởi bên thứ ba**. Kết quả thực tế sẽ thay đổi theo dự án, stack và quy mô log/test. Hãy tái lập trên chính dự án của bạn bằng `agent-qa verify` + benchmark harness trước khi dùng các số liệu này để ra quyết định.

---

## 👥 3. Hệ Thống Multi-Agent Swarm (6 Vai Trò Chuyên Biệt)

| Vai Trò Subagent | Trách Nhiệm Cốt Lõi | Kỹ Năng Tiêu Biểu | Công Cụ Đi Kèm |
| :--- | :--- | :--- | :--- |
| **`orchestrator`** | Trưởng nhóm điều phối, bootstrap dự án, audit sức khỏe, neo state. | `agent-orchestration`, `graphify`, `adr` | `setup_project.py`, `analyze_project.py`, `repo_map.py` |
| **`live-explorer`** | Thám sát live DOM/AOM qua Playwright headless, tường lửa chống click phá hoại. | `playwright-live`, `self-healing`, `visual-diff` | `safety_firewall.py`, `browser_helpers.js` |
| **`pom-crafter`** | Kỹ sư Clean POM, kiểm tra breaking change API, sinh test từ User Story. | `clean-pom`, `lam-script`, `synthetic-data` | `generate_tc_from_story.py`, `api_drift_sentinel.py` |
| **`test-runner`** | Quản lý chạy test headless CLI, chia tải song song CI, lọc log thông minh. | `katalon-cli`, `e2e-patterns`, `flaky-sentinel` | `matrix_sharder.py`, `distill_log.py`, `pinpoint_failure.py` |
| **`failure-analyst`**| Tự động khám nghiệm tử thi lỗi, tính điểm tin cậy & tự tạo PR đối soát. | `failure-autopsy`, `self-healing-locator` | `auto_heal.py`, `heal_pr_automator.py`, `cache_resolver.py` |
| **`quality-gatekeeper`**| Gác cổng 9 Cổng Chất Lượng DoD (Gate 0–8), quét Fake-Pass, tiêm mutant. | `antigravity-sentinel`, `skillspector`, `dast` | `verify_all.py`, `infer_linter.py`, `micro_mutator.py` |

---

## 📦 4. Kho Tri Thức & Công Cụ (Bấm Vào Để Mở Rộng Tra Cứu)

<details>
<summary><b>📦 Bấm để xem: Danh Mục 29 Kỹ Năng Chuẩn Hóa (.agents/skills/)</b></summary>

| STT | Tên Kỹ Năng (Skill) | Phạm Vi Hoạt Động Cốt Lõi |
|:---:|---|---|
| 1 | `agent-orchestration-multi-agent-optimize` | Tối ưu hóa điều phối multi-agent, phân bổ tải và giám sát chi phí token. |
| 2 | `antigravity-test-sentinel` | Gác cổng Verification-First, khóa hoàn thành task nếu test chưa pass exit code 0. |
| 3 | `api-network-mocking-interception` | Chặn bắt, mock lưu lượng HTTP/GraphQL và kiểm thử độ bền mạng (Chaos/Resilience). |
| 4 | `api-spec-to-e2e-matrix` | Phân tích OpenAPI/Swagger để sinh ma trận kiểm thử tương đương, biên và lỗi. |
| 5 | `architecture-decision-records` | Soạn thảo và quản lý hồ sơ quyết định kiến trúc kỹ thuật (ADR). |
| 6 | `auth-session-and-cookie-manager` | Quản lý phiên đăng nhập, JWT tokens, storageState cho đăng nhập 0-giây. |
| 7 | `backend-load-and-stress-patterns` | Kiểm thử tải và stress backend với k6 & Locust, giám sát ngưỡng SLA P95/P99. |
| 8 | `bats-testing-patterns` | Kiểm thử tự động Shell Scripts, CI/CD pipelines, mock binary CLI và exit code. |
| 9 | `clean-pom-crafter` | Chuẩn hóa Clean Page Object Model, Flat Architecture, Dynamic `uniqueCode`. |
| 10 | `code-refactoring-refactor-clean` | Tái cấu trúc code chuyên sâu, khử code smells, nợ kỹ thuật và chuẩn SOLID. |
| 11 | `db-state-verifier-and-seeder` | Kiểm tra trạng thái DB trực tiếp (PostgreSQL, MySQL, MongoDB, Redis) và seed fixture. |
| 12 | `e2e-testing-patterns` | Kiến trúc E2E đa trình duyệt (Playwright/Cypress), Typed POM, sharding song song. |
| 13 | `failure-autopsy-and-healing` | Khám nghiệm tử thi lỗi cấp vĩ mô từ JUnit XML, Allure report và ảnh chụp lỗi. |
| 14 | `file-and-report-validator` | Kiểm định nội dung file tải về/tải lên (Excel .xlsx, CSV stream, PDF text/layout). |
| 15 | `flaky-test-sentinel-and-quarantine` | Phát hiện, chấm điểm và cô lập kiểm thử chập chờn (flaky test) vào vùng cách ly. |
| 16 | `github-actions-templates` | Mẫu pipeline CI/CD GitHub Actions chuẩn sản xuất và sharded testing. |
| 17 | `graphify-impact-analyzer` | Phân tích đồ thị tri thức AST Knowledge Graph và khoanh vùng ảnh hưởng thay đổi. |
| 18 | `katalon-cli-runner` | Điều phối thực thi headless KRE CLI, Community mode và dọn dẹp zombie driver. |
| 19 | `lam-script-generator` | Large Action Model, chuyển đổi User Story sang 100% test script không token replay. |
| 20 | `playwright-live-interaction` | Thám sát trực tiếp live DOM/AOM qua Playwright MCP, kiểm tra hit-rate < 200ms. |
| 21 | `security-dast-sentinel` | Kiểm thử bảo mật động DAST, rà soát OWASP Top 10, HTTP Headers, BOLA/IDOR. |
| 22 | `self-healing-locator` | Tự phục hồi locator vi mô bằng cây Semantic Accessibility (AOM), Role > Label > TestId. |
| 23 | `synthetic-test-data-generator` | Tự động sinh dữ liệu kiểm thử biên (BVT), chống SQLi/XSS, đa ngôn ngữ, tọa độ GIS. |
| 24 | `token-and-context-optimizer` | Tối ưu token, lọc log rác, chống suy thoái ngữ cảnh (Lost-in-the-Middle) và scratchpad đĩa. |
| 25 | `visual-regression-sentinel` | So sánh giao diện mức pixel và SSIM, hỗ trợ dynamic masking chống flaky test. |
| 26 | `wcag-audit-patterns` | Kiểm toán tiếp cận web WCAG 2.2 Level A/AA tự động qua AST và `@axe-core`. |
| 27 | `web-vitals-and-performance-profiler` | Đo lường Core Web Vitals (LCP, CLS, TTFB) và giám sát API endpoint chậm qua CDP. |
| 28 | `skillspector-security-guard` | Kiểm toán bảo mật AI Agent skills & MCP configs với 71 vector lỗ hổng (Prompt Injection, Data Exfiltration, Privilege Escalation) theo chuẩn NVIDIA SkillSpector. |
| 29 | `rbt-manual-testing` | Quy trình 6 bước AI-RBT sinh Test Case thủ công, ma trận rủi ro P × I, bảng Ambiguity Log, ma trận 12 cột, checklist 15 loại input field và kịch bản phi chức năng (Double-Submit, Race Conditions). |

</details>

<details>
<summary><b>📋 Bấm để xem: 7 Workflows Thực Chiến (.agents/workflows/)</b></summary>

| Workflow | Mục Đích Nghiệp Vụ Cốt Lõi |
| :--- | :--- |
| **`generate_manual_testcases_rbt.md`** | Phân tích rủi ro P × I, giải quyết câu hỏi mập mờ (Ambiguity Q&A), và sinh ma trận test case 12 cột. |
| **`generate_testcases_from_requirements.md`** | Chuyển đổi trực tiếp tài liệu đặc tả (BRD, SRS, User Stories) thành bộ kiểm thử chấp nhận (Acceptance Tests). |
| **`generate_cross_module_test_plan.md`** | Lập kế hoạch kiểm thử luồng nghiệp vụ E2E xuyên suốt nhiều module (Cart ➔ Checkout ➔ Payment ➔ Warehouse). |
| **`generate_combinatorial_test_data.md`** | Sinh tập dữ liệu kiểm thử tổ hợp All-Pairs / Pairwise bao phủ tối đa trường hợp biên với số ca test tối thiểu. |
| **`generate_requirements_from_website.md`** | Tự động thám sát Live Web bằng Playwright headless để trích xuất ngược đặc tả nghiệp vụ (Reverse-Engineering). |
| **`analyze_requirement_document.md`** | Quét phát hiện mâu thuẫn logic, khoảng trống nghiệp vụ và các phát biểu mơ hồ trong tài liệu PRD. |
| **`export_testcases_excel.md`** | Xuất bảng Test Case từ Markdown sang file Excel (.xlsx) chuẩn doanh nghiệp với màu sắc trực quan qua OpenPyXL. |

</details>

<details>
<summary><b>📜 Bấm để xem: 10 Quy Tắc Cốt Lõi (.agents/rules/)</b></summary>

1. **`context-engineering.md`**: Giao thức lọc log thừa (Observation Masking), khai báo lười (Lazy Loading) và tối ưu hóa KV-Cache.
2. **`git-push-protocol.md`**: Giao thức Git Push chuẩn hóa cho dự án mục tiêu (Clean SCM by Architecture, loại bỏ hoàn toàn nhu cầu dual-remote/smart-push nhờ tách repo độc lập).
3. **`graphify.md`**: Điều hướng đồ thị tri thức mã nguồn AST thay vì đọc toàn văn mã nguồn lớn.
4. **`lessons-learned.md`**: Danh sách bài học kinh nghiệm và anti-patterns (giới hạn cứng < 40 dòng).
5. **`mandatory-playwright-live.md`**: Quy chuẩn chạy headless Full HD 1920x1080 và khảo sát live DOM trước khi codify.
6. **`skill-precedence.md`**: Thứ tự ưu tiên kỹ năng cục bộ, chống xung đột trigger với plugin bên ngoài.
7. **`systematic-debugging.md`**: Kỷ luật điều tra lỗi có căn cứ, cấm đoán mò và verify-first (9 Quality Gates DoD).
8. **`author-integrity-guard.md`**: Bảo toàn thông báo bản quyền tác giả theo giấy phép MIT và phòng chống đạo văn.
9. **`mobile_appium_rules.md`**: Quy tắc tự động hóa kiểm thử Native Mobile (Appium, Screen Object Model, chiến lược Locator tối ưu cho iOS/Android, smart wait và xử lý lifecycle).
10. **`performance_testing_rules.md`**: Bất biến an toàn kiểm thử tải và hiệu năng (k6/JMeter/Locust, Approval Gate, Hard Caps, Kill-Switch `abortOnFail`, Open/Closed workload modeling, cô lập bên thứ 3 và Truth Anchor).

</details>

<details>
<summary><b>🛠️ Bấm để xem: Sổ Tay 50+ Công Cụ Tự Động Hóa (tools/)</b></summary>

Chi tiết đầy đủ xem tại [tools/TOOLS_RUNBOOK.md](tools/TOOLS_RUNBOOK.md):

- `tools/verify_all.py`: Cổng thẩm định 9 Gates DoD (Gate 0–8: UTF-8, No XPaths, UniqueCode, Clean POM, AST Mutation).
- `tools/md_to_xlsx.py` (`agent-qa export-excel`): Xuất bảng Test Case từ Markdown sang file Excel (.xlsx) chuyên nghiệp (định dạng header doanh nghiệp, frozen panes, auto-fit cột, huy hiệu màu P1-P4).
- `tools/generate_jmx_plan.py`: Sinh kịch bản Apache JMeter 5.x (.jmx) đa giao thức (HTTP, JDBC, WS, gRPC, Kafka) kèm Traffic Shaping Pareto.
- `tools/jtl_analyzer.py`: Phân tích kết quả JTL, kiểm soát SLA percentiles (P90, P95, P99) và làm Quality Gate CI/CD.
- `tools/telemetry_correlator.py`: Phân tích tương quan Pearson giữa Client Latency và Server APM (CPU, RAM, DB Pool).
- `tools/export_postman_collection.py`: Xuất Postman Collection v2.1 với AJV JSON Schema, DDT, và Zero-Input synthesis.
- `tools/newman_analyzer.py`: Phân tích kết quả Newman, triage lỗi assertion và làm Quality Gate cho API.
- `tools/api_fuzzer.py`: Autonomous API Fuzzer phát hiện lỗi HTTP 500, rò rỉ stacktrace DB và vi phạm SLA độ trễ.
- `tools/api_drift_sentinel.py`: Bắt breaking change giữa các phiên bản OpenAPI / Swagger specifications.
- `tools/auto_heal.py`: Tự phục hồi locator gãy dựa trên AOM diffing mà không cần chạy lại toàn bộ test suite.
- `tools/flaky_detector.py`: Phát hiện kiểm thử chập chờn (Flaky tests) và quản lý vòng đời cách ly Quarantine.
- `tools/skillspector.py`: Quét kiểm toán an ninh AI Agent Skills & MCP (71 vectors theo chuẩn NVIDIA SkillSpector).
- `tools/omni_transpiler.py`: Chuyển đổi mã kiểm thử 0-token đa ngôn ngữ (Playwright TS/Python, Java, Groovy, Cypress).
- `tools/infer_linter.py`: Phân tích tĩnh AST phát hiện fake-pass (0 assertion) và khối try-catch nuốt lỗi.
- `tools/test_impact.py`: Phân tích git diff và khoanh vùng chính xác test cases bị ảnh hưởng.
- `tools/cache_resolver.py`: Quản lý bộ nhớ đệm lỗi SQLite trung tâm (`~/.agent_memory/global_cache.db`).
- `tools/distill_log.py`: Lọc bỏ 95% log thừa từ CLI/Gradle/KRE, giữ lại stacktrace và file pointer.
- `tools/agent_canary.py`: Hệ thống tiêm 8 vector lỗi tự động đánh giá sức phục hồi của Agent (MTTR).
- `tools/repo_map.py`: Trích xuất bản đồ cấu trúc hàm và Page Class siêu nén (~500 tokens).
- `tools/visual_diff_canvas.py`: So sánh pixel/SSIM cho màn hình GIS/Canvas không có DOM.
- `tools/wcag_audit.py`: Quét kiểm toán tự động các tiêu chí tiếp cận WCAG 2.2 Level A/AA.
- `tools/generate_api_matrix.py`: Tự động sinh ma trận kiểm thử Positive/Boundary/Negative từ Swagger.
- `tools/generate_tc_from_story.py`: Large Action Model parser sinh khung Clean POM từ User Story.
- `tools/trace_data_flow.py`: Kiểm tra luồng dữ liệu kiểm thử, phát hiện rác dữ liệu DB (Orphan Data).
- `scripts/install.ps1` & `scripts/setup.sh`: Script cài đặt 1-click tự động khởi tạo môi trường Hub.
- `scripts/lint_skills.ps1`: Linter kiểm tra tính toàn vẹn 30 skills và metadata manifest.
- `pyproject.toml` & `tools/cli.py`: Đóng gói chuẩn PEP 621 cho lệnh CLI toàn cầu `agent-qa`.

</details>

<details>
<summary><b>🤝 Bấm để xem: Nguồn Cảm Hứng & Lời Cảm Ơn (Acknowledgments)</b></summary>

| Dự án & Tác giả | Nguồn cảm hứng & Đóng góp kiến trúc trong Synapse Hub |
| :--- | :--- |
| **[NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector)** *(NVIDIA AI Security Team)* | Động cơ kiểm toán an ninh kỹ năng AI Agent & MCP (71 vectors lỗ hổng, Prohibition Context Engine). |
| **[muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)** | Nguyên lý Context Engineering, Observation Masking và kỹ thuật tối ưu hóa sự chú ý của LLM. |
| **[alexgreensh/token-optimizer](https://github.com/alexgreensh/token-optimizer)** | Cơ chế cô đọng log CLI/Gradle (95% distillation) và tối ưu hóa KV-Cache. |
| **[obra/superpowers](https://github.com/obra/superpowers)** *(Jesse Vincent)* | Kỷ luật gỡ lỗi dựa trên bằng chứng (Systematic Debugging), Cognitive Forcing và cơ chế Red-Team vs Blue-Team. |
| **[Aider-AI/aider](https://github.com/Aider-AI/aider)** *(Paul Gauthier)* | Kỹ thuật trích xuất AST bản đồ mã nguồn thu gọn (`tools/repo_map.py`) dưới 600 tokens. |
| **[lavague-ai/LaVague](https://github.com/lavague-ai/LaVague)** | Mô hình Large Action Model (LAM), tự động biên dịch User Story thành kịch bản kiểm thử Clean POM. |
| **[facebook/infer](https://github.com/facebook/infer)** *(Meta Infer)* | Linter phân tích tĩnh AST (`tools/infer_linter.py`) phát hiện test giả lập (Fake-Pass) và try-catch nuốt lỗi. |
| **[microsoft/playwright](https://github.com/microsoft/playwright)** | Tương tác live DOM/AOM sub-200ms, điều hướng headless và mô phỏng network resilience. |
| **[dequelabs/axe-core](https://github.com/dequelabs/axe-core)** | Quy chuẩn kiểm toán tự động các tiêu chí khả năng tiếp cận WCAG 2.2 Level A/AA. |
| **[bats-core/bats-core](https://github.com/bats-core/bats-core)** | Chuẩn kiểm thử tự động Bash Automated Testing System cho kịch bản shell/CLI. |
| **[npryce/adr-tools](https://github.com/npryce/adr-tools)** | Quy chuẩn ghi nhận và lưu vết quyết định kiến trúc phần mềm (ADRs). |

</details>

---

## 📚 5. Tài Liệu Kỹ Thuật Mở Rộng & CLI Package (docs/)

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Kiến trúc Hub/Spoke, mô hình 4 tầng kỹ năng, và ma trận phối hợp 6 Subagent Swarm.
2. **[docs/TOKEN_QUOTA_PLAYBOOK.md](docs/TOKEN_QUOTA_PLAYBOOK.md)**: Chiến lược phân tầng mô hình (Claude Sonnet vs Gemini Pro vs Gemini Flash), tối ưu chi phí và điều hướng theo hạn mức API quota.
3. **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Quy chuẩn đóng góp, nguyên tắc sáng tạo skill mới và quy trình kiểm định toàn vẹn.
4. **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)**: Cẩm nang tra cứu toàn bộ tham số lệnh của công cụ dòng lệnh `agent-qa`.

### Cài đặt nhanh CLI Package:
```bash
pip install -e .
agent-qa --help
agent-qa verify
agent-qa export-excel
```

---

## 📄 6. Bản Quyền & Điều Khoản Sử Dụng (License & Attribution)

Dự án được phân phối chính thức dưới giấy phép **[MIT License](LICENSE)**.

**Quyền sở hữu tác giả & Xuất xứ (Provenance):**
- **Tác giả & Nhà sáng lập:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))
- **Mã nguồn gốc:** [https://github.com/TeeVee998/Synapse-Hub](https://github.com/TeeVee998/Synapse-Hub)
- **Bản quyền:** Copyright © 2026 Thế Vị (@TeeVee998). Phân phối theo giấy phép MIT.

> ⚖️ **Điều khoản phân phối theo giấy phép MIT:** Bạn được toàn quyền sử dụng, sao chép, sửa đổi, hợp nhất, xuất bản và phân phối mã nguồn này cho bất kỳ mục đích cá nhân hay thương mại nào, **VỚI ĐIỀU KIỆN** thông báo bản quyền gốc ghi nhận tác giả **Thế Vị (@TeeVee998)** cùng điều khoản cấp phép này phải được giữ nguyên vẹn trong toàn bộ bản sao hoặc các phần quan trọng của phần mềm.
