# 🧠 Synapse Hub — Trung Tâm Trí Tuệ & Mạng Lưới Kỹ Năng Cho AI Agent

[🇻🇳 Tiếng Việt](#-synapse-hub--trung-tâm-trí-tuệ--mạng-lưới-kỹ-năng-cho-ai-agent) | [🇬🇧 English Edition](#-english-edition)

> **Bộ não trí tuệ dùng chung và mạng lưới kỹ năng tự hành, tăng cường năng lực cho các trợ lý AI (Google Antigravity, Cursor, Windsurf, Claude Code) trên mọi hệ sinh thái kiểm thử tự động.**  
> **Tác giả:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))  
> **Phiên bản Hub:** `v2.0.0` | **Quy mô:** 27 Kỹ năng chuẩn hóa, 6 Vai trò AI Swarm, 7 Quy tắc cốt lõi, 20+ Công cụ tự động.

---

## 🌟 1. Tổng quan & Mục đích Kiến trúc

**Synapse Hub** là tầng trí tuệ đa tác tử tách rời (**Decoupled Shared Intelligence Core**), đóng vai trò như một **"Bộ não dùng chung"**, tách biệt hoàn toàn khỏi mã nguồn của từng dự án cụ thể. Dự án trang bị cho AI agents các vai trò bầy đàn chuyên biệt (Multi-Agent Swarm), quy trình tự chữa lành (Self-Healing), khả năng thấu hiểu mã nguồn cấp độ AST và các cổng chất lượng nghiêm ngặt (Quality Gates)—cho phép tự động hóa kiểm thử chuẩn xác tuyệt đối trên mọi codebase mà không làm bẩn repository mục tiêu.

```mermaid
flowchart TD
    subgraph Hub["🧠 Synapse Hub (Intelligence Core v2.0.0)"]
        Skills[".agents/skills/ (27 Skills)"]
        Agents[".agents/agents/ (6 Specialized Roles)"]
        Rules[".agents/rules/ (7 Core Rules)"]
        Tools["tools/ (20+ Universal Python Tools)"]
        Workflows[".agents/workflows/"]
    end

    subgraph ChatSession["💬 AI Agent Workspace / Chat Session"]
        Hub -->|Mount/Add Workspace| ChatSession
    end

    subgraph Projects["📁 Các Dự Án Mục Tiêu (Target Projects)"]
        ProjectA["Dự án A<br/>(PROJECT_AI_GUIDE.md + Source Code)"]
        ProjectB["Dự án B<br/>(PROJECT_AI_GUIDE.md + Test Code)"]
        ProjectC["Dự án C<br/>(PROJECT_AI_GUIDE.md + App Code)"]
        Other["Dự án khác..."]
    end

    ProjectA -->|Mount Workspace| ChatSession
    ProjectB -.->|Mount Workspace| ChatSession
    ProjectC -.->|Mount Workspace| ChatSession
    Other -.->|Mount Workspace| ChatSession
```

### Lợi ích cốt lõi:
1. **Dùng chung đa dự án (Cross-Project Reusability):** Một lần phát triển skill hay tối ưu tool có thể áp dụng ngay cho bất kỳ dự án Web/API nào (React, Angular, Vue, Next.js, Java, Python).
2. **Bảo mật mã nguồn công ty (Privacy & Clean SCM):** Repository dự án hoàn toàn sạch sẽ, không chứa prompt hay AI skill cá nhân.
3. **Quản lý tập trung (Single Source of Truth):** Dễ dàng nâng cấp, thêm skill mới, đồng bộ Global Memory Cache tại một nơi duy nhất.
4. **Nhẹ & Tinh gọn:** Dự án mục tiêu chỉ cần đúng **1 file duy nhất** hướng dẫn AI (`PROJECT_AI_GUIDE.md`).

---

## 🚀 2. Cách Sử Dụng (NPM / npx & Workspace Mount)

[![npm version](https://img.shields.io/npm/v/synapse-hub.svg?style=flat-square&color=blue)](https://www.npmjs.com/package/synapse-hub)
[![npm downloads](https://img.shields.io/npm/dm/synapse-hub.svg?style=flat-square)](https://www.npmjs.com/package/synapse-hub)
[![license](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](https://github.com/TeeVee998/Synapse-Hub/blob/main/package.json)

### Cách A: Sử dụng tức thì qua NPM Registry (Khuyên dùng)
Gói chính thức đã được phát hành toàn cầu tại **[npmjs.com/package/synapse-hub](https://www.npmjs.com/package/synapse-hub)**. Bạn có thể sử dụng ngay mà không cần clone mã nguồn:

#### 1. Thực thi tức thì không cần cài đặt (`npx`):
Tại thư mục gốc của bất kỳ dự án nào, thực thi trực tiếp:
```bash
# Khởi tạo tự động 1-Click (sinh PROJECT_AI_GUIDE.md, cài pre-push hook, trích xuất AST repo map)
npx synapse-hub setup

# Chạy kiểm định 8 Cổng Chất Lượng (DoD Quality Gates)
npx synapse-hub verify

# Đánh giá sức khỏe toàn diện dự án (5-in-1 Project Health Report)
npx synapse-hub analyze

# Quét phát hiện mã giả, assertion rỗng (Fake-Pass AST Sentinel)
npx synapse-hub lint
```
> 💡 **Mẹo:** Bạn cũng có thể dùng lệnh gọi rút gọn: `npx synapse setup` hoặc `npx synapse verify`.

#### 2. Cài đặt cố định vào dự án (DevDependency):
```bash
npm install -D synapse-hub
```
Sau đó có thể khai báo vào `scripts` trong file `package.json` của dự án mục tiêu:
```json
"scripts": {
  "qa:verify": "synapse-hub verify",
  "qa:analyze": "synapse-hub analyze"
}
```

#### 3. Cài đặt toàn cục (Global CLI):
Để sử dụng công cụ ở bất cứ đâu trên máy tính:
```bash
npm install -g synapse-hub

# Sử dụng trực tiếp:
synapse-hub verify
synapse setup
```

### Cách B: Mở phiên làm việc đa thư mục (Multi-Root Workspace)
Trong IDE (Google Antigravity / VS Code / Cursor):
1. Mở thư mục dự án mục tiêu của bạn.
2. Thêm thư mục `Synapse-Hub` vào Workspace (`File` -> `Add Folder to Workspace...`).

### Bước 2: Khởi tạo hướng dẫn dự án (`PROJECT_AI_GUIDE.md`)
Copy file mẫu từ `templates/PROJECT_AI_GUIDE_TEMPLATE.md` vào thư mục gốc của dự án mục tiêu, đổi tên thành `PROJECT_AI_GUIDE.md` và điền thông tin cụ thể:
- URL môi trường test/staging.
- Tài khoản và cơ chế đăng nhập.
- Cấu trúc thư mục mã nguồn.
- Lệnh chạy test headless và công nghệ sử dụng.
- **Dữ liệu tra cứu nhanh:** Khai báo đường dẫn `testcases.json` và `selectors.json` (hoặc đặt biến môi trường `TC_DATA_FILE` / `XPATH_DATA_FILE`) để công cụ `tools/lookup_tc.py` và `tools/lookup_xpath.py` nạp đúng dữ liệu của dự án.

### Bước 3: Cài đặt tự động (One-Click Bootstrap)
Chạy script cài đặt môi trường và phụ thuộc:
```powershell
# Windows PowerShell
./scripts/install.ps1

# Linux / macOS
./scripts/setup.sh
```
Script bootstrap sẽ tự động thiết lập `.venv`, cài dependencies, chạy lint kiểm tra 30 skills, và **khởi tạo nạp seed giải pháp ban đầu** cho SQLite Central Agent Memory (`~/.agent_memory/global_cache.db`).

> 💡 **Khởi tạo SQLite Memory trên CI/CD & Docker sạch:**  
> Trên agent runner CI hoặc container Docker mới tinh, chạy lệnh sau để cấp quyền và khởi tạo bộ nhớ 0-token:
> ```bash
> agent-qa heal init
> # hoặc chạy trực tiếp:
> python tools/cache_resolver.py init
> ```

---

## 👥 3. Hệ Thống Multi-Agent Swarm (6 Vai Trò Chuyên Biệt)

Hub phân chia năng lực rõ ràng cho 6 vai trò Agent, mỗi Agent được gán sẵn các Skills và Tools tương ứng:

| Vai Trò Agent | Trách Nhiệm Cốt Lõi | Skills Được Gán | Tools Đi Kèm |
| :--- | :--- | :--- | :--- |
| **`orchestrator`** | Trưởng nhóm điều phối, bootstrap dự án, audit sức khỏe, neo state. | `agent-orchestration-multi-agent-optimize`, `graphify-impact-analyzer`, `architecture-decision-records` | `tools/setup_project.py`, `tools/analyze_project.py`, `tools/project_state.py`, `tools/repo_map.py`, `tools/test_impact.py`, `tools/mcp_server.py` |
| **`live-explorer`** | Thám sát live DOM/AOM qua Playwright, chặn click phá hoại. | `playwright-live-interaction`, `self-healing-locator`, `visual-regression-sentinel`, `auth-session-and-cookie-manager` | `tools/safety_firewall.py`, `tools/lookup_xpath.py`, `tools/visual_diff_canvas.py`, `tools/browser_helpers.js` |
| **`pom-crafter`** | Kỹ sư Clean POM, kiểm tra API drift, sinh test từ User Story. | `clean-pom-crafter`, `lam-script-generator`, `synthetic-test-data-generator`, `api-spec-to-e2e-matrix`, `file-and-report-validator`, `db-state-verifier-and-seeder` | `tools/generate_tc_from_story.py`, `tools/generate_api_matrix.py`, `tools/api_drift_sentinel.py`, `tools/repo_map.py` |
| **`test-runner`** | Quản lý chạy test headless CLI, chia tải thời gian chạy trên CI. | `katalon-cli-runner`, `e2e-testing-patterns`, `bats-testing-patterns`, `auth-session-and-cookie-manager`, `flaky-test-sentinel-and-quarantine` | `tools/matrix_sharder.py`, `tools/distill_log.py`, `tools/pinpoint_failure.py`, `tools/flaky_detector.py` |
| **`failure-analyst`**| Tự động chẩn đoán lỗi, tính điểm tin cậy & tự tạo PR đối soát. | `failure-autopsy-and-healing`, `self-healing-locator`, `file-and-report-validator` | `tools/auto_heal.py`, `tools/heal_pr_automator.py`, `tools/pinpoint_failure.py`, `tools/cache_resolver.py` |
| **`quality-gatekeeper`**| Gác cổng chất lượng 7 Gates DoD, quét Fake-Pass, bơm mutant. | `antigravity-test-sentinel`, `code-refactoring-refactor-clean`, `wcag-audit-patterns`, `web-vitals-and-performance-profiler`, `db-state-verifier-and-seeder`, `security-dast-sentinel` | `tools/verify_all.py`, `tools/infer_linter.py`, `tools/micro_mutator.py`, `tools/trace_data_flow.py`, `tools/wcag_audit.py`, `tools/lint_ai_docs.py` |

---

## 📦 4. Danh Mục 27 Kỹ Năng Chuẩn Hóa (.agents/skills/)

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

---

## 📜 5. Danh Mục 7 Quy Tắc Cốt Lõi (.agents/rules/)

1. **`context-engineering.md`**: Giao thức lọc log thừa (Observation Masking), khai báo lười (Lazy Loading) và tối ưu hóa KV-Cache.
2. **`git-push-protocol.md`**: Giao thức Git Push chuẩn hóa cho dự án mục tiêu (Clean SCM by Architecture, loại bỏ hoàn toàn nhu cầu dual-remote/smart-push nhờ tách repo độc lập).
3. **`graphify.md`**: Điều hướng đồ thị tri thức mã nguồn AST thay vì đọc toàn văn mã nguồn lớn.
4. **`lessons-learned.md`**: Danh sách bài học kinh nghiệm và anti-patterns (giới hạn cứng < 40 dòng).
5. **`mandatory-playwright-live.md`**: Quy chuẩn chạy headless Full HD 1920x1080 và khảo sát live DOM trước khi codify.
6. **`skill-precedence.md`**: Thứ tự ưu tiên kỹ năng cục bộ, chống xung đột trigger với plugin bên ngoài.
7. **`systematic-debugging.md`**: Kỷ luật điều tra lỗi có căn cứ, cấm đoán mò và verify-first (7 Quality Gates).

---

## 🛠️ 6. Sổ Tay Công Cụ Tự Động Hóa (tools/ & scripts/)

Chi tiết đầy đủ xem tại [tools/TOOLS_RUNBOOK.md](tools/TOOLS_RUNBOOK.md):

- `tools/verify_all.py`: Cổng thẩm định 7 Gates DoD (UTF-8, No XPaths, UniqueCode, Clean POM).
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

---

## 📚 7. Tài Liệu Kỹ Thuật Mở Rộng & CLI Package (docs/)

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Kiến trúc Hub/Spoke, mô hình 4 tầng kỹ năng, và ma trận phối hợp 6 Subagent Swarm.
2. **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Quy chuẩn đóng góp, nguyên tắc sáng tạo skill mới và quy trình kiểm định toàn vẹn.
3. **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)**: Cẩm nang tra cứu toàn bộ tham số lệnh của công cụ dòng lệnh `agent-qa`.

### Cài đặt nhanh CLI Package:
```bash
pip install -e .
agent-qa --help
agent-qa verify
agent-qa lint
```

---

# 🌐 English Edition

# 🧠 Synapse Hub — AI Agent Intelligence Core & Skill Network

> **The shared intelligence core and autonomous skill hub empowering AI coding assistants (Google Antigravity / Cursor / Windsurf / Claude Code) across automated testing suites.**  
> **Author:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))  
> **Hub Version:** `v2.0.0` (Semantic Versioning) | **Integrity Index:** 27 Skills, 6 Agent Swarm Roles, 7 Core Rules, 20+ Python Tools.

---

## 🌟 1. Overview & Architectural Purpose

**Synapse Hub** serves as a **Decoupled Shared Intelligence Core**, acting as an external neural brain completely isolated from target projects' codebases. It equips AI agents with specialized swarm roles, self-healing execution protocols, AST-level code intelligence, and strict Quality Gates—enabling zero-leakage, truth-anchored test automation across any polyglot codebase without polluting target repositories.

```mermaid
flowchart TD
    subgraph Hub["🧠 Synapse Hub (Intelligence Core v2.0.0)"]
        Skills[".agents/skills/ (27 Skills)"]
        Agents[".agents/agents/ (6 Specialized Roles)"]
        Rules[".agents/rules/ (7 Core Rules)"]
        Tools["tools/ (20+ Universal Python Tools)"]
        Workflows[".agents/workflows/"]
    end

    subgraph ChatSession["💬 AI Agent Workspace / Chat Session"]
        Hub -->|Mount/Add Workspace| ChatSession
    end

    subgraph Projects["📁 Target Projects"]
        ProjectA["Project A<br/>(PROJECT_AI_GUIDE.md + Source Code)"]
        ProjectB["Project B<br/>(PROJECT_AI_GUIDE.md + Test Code)"]
        ProjectC["Project C<br/>(PROJECT_AI_GUIDE.md + App Code)"]
        Other["Other Projects..."]
    end

    ProjectA -->|Mount Workspace| ChatSession
    ProjectB -.->|Mount Workspace| ChatSession
    ProjectC -.->|Mount Workspace| ChatSession
    Other -.->|Mount Workspace| ChatSession
```

### Core Architectural Benefits:
1. **Cross-Project Reusability:** Develop skills and tools once; reuse universally across any Web/API stack (React, Angular, Vue, Next.js, Java, Python).
2. **Target Repository Privacy & Clean SCM:** Target project repos remain 100% clean—zero personal AI prompts or agent skills polluting production Git history.
3. **Single Source of Truth:** Manage, upgrade, add new skills, and synchronize Global Memory Cache in one centralized hub.
4. **Lean & Lightweight Integration:** Target projects require only **a single markdown guide** (`PROJECT_AI_GUIDE.md`).

---

## 🚀 2. Getting Started & Usage (NPM / npx & Workspace Mount)

[![npm version](https://img.shields.io/npm/v/synapse-hub.svg?style=flat-square&color=blue)](https://www.npmjs.com/package/synapse-hub)
[![npm downloads](https://img.shields.io/npm/dm/synapse-hub.svg?style=flat-square)](https://www.npmjs.com/package/synapse-hub)
[![license](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](https://github.com/TeeVee998/Synapse-Hub/blob/main/package.json)

### Method A: Instant Execution via NPM Registry (Recommended)
The package is officially published at **[npmjs.com/package/synapse-hub](https://www.npmjs.com/package/synapse-hub)**. Execute directly without cloning:

#### 1. Zero-Install Execution (`npx`):
Run from any target project directory:
```bash
# 1-Click Project Bootstrap (generates PROJECT_AI_GUIDE.md, installs pre-push hook, extracts AST repo map)
npx synapse-hub setup

# Run 8 Quality Gates DoD Verification
npx synapse-hub verify

# Comprehensive 5-in-1 Project Health Audit
npx synapse-hub analyze

# Static Defect & Fake-Pass Sentinel scan
npx synapse-hub lint
```
> 💡 **Tip:** You can also use the shorthand alias: `npx synapse setup` or `npx synapse verify`.

#### 2. Project-Local Installation (DevDependency):
```bash
npm install -D synapse-hub
```
Configure custom lifecycle scripts in your target project's `package.json`:
```json
"scripts": {
  "qa:verify": "synapse-hub verify",
  "qa:analyze": "synapse-hub analyze"
}
```

#### 3. Global CLI Installation:
To use `synapse-hub` anywhere on your terminal:
```bash
npm install -g synapse-hub

# Direct invocation:
synapse-hub verify
synapse setup
```

### Method B: Multi-Root Workspace Mounting
Within your AI IDE (Google Antigravity / VS Code / Cursor):
1. Open your target project folder.
2. Add the `Synapse-Hub` directory to your workspace (`File` -> `Add Folder to Workspace...`).

### Step 2: Initialize Project AI Guide (`PROJECT_AI_GUIDE.md`)
Copy `templates/PROJECT_AI_GUIDE_TEMPLATE.md` to target project root, rename to `PROJECT_AI_GUIDE.md`, and configure:
- Test/staging environment URLs.
- Credentials and authentication strategies.
- Source code directory structure.
- Headless execution commands and technology stack.
- **Fast-Lookup Registers:** Point `testcases.json` and `selectors.json` (or set `TC_DATA_FILE` / `XPATH_DATA_FILE` env vars) for instant zero-token query via `tools/lookup_tc.py` and `tools/lookup_xpath.py`.

### Step 3: One-Click Environment Bootstrap
Execute the automated bootstrap script:
```powershell
# Windows PowerShell
./scripts/install.ps1

# Linux / macOS
./scripts/setup.sh
```
The bootstrap script automatically configures `.venv`, installs dependencies, lints skills, and seeds initial solutions into the Central SQLite Agent Memory (`~/.agent_memory/global_cache.db`).

> 💡 **Initializing SQLite Memory on Clean CI/CD & Docker:**  
> In fresh CI runners or Docker containers, initialize zero-token memory cache via:
> ```bash
> agent-qa heal init
> # or run directly:
> python tools/cache_resolver.py init
> ```

---

## 👥 3. Multi-Agent Swarm System (6 Specialized Roles)

Synapse Hub clearly partitions capabilities across 6 specialized AI roles, pre-configured with dedicated skills and tools:

| Agent Role | Core Responsibility | Assigned Skills | Included Tools |
| :--- | :--- | :--- | :--- |
| **`orchestrator`** | Lead coordinator, project bootstrapping, health auditing, state anchoring. | `agent-orchestration-multi-agent-optimize`, `graphify-impact-analyzer`, `architecture-decision-records` | `tools/setup_project.py`, `tools/analyze_project.py`, `tools/project_state.py`, `tools/repo_map.py`, `tools/test_impact.py`, `tools/mcp_server.py` |
| **`live-explorer`** | Live DOM/AOM probing via Playwright MCP, destructive click firewall. | `playwright-live-interaction`, `self-healing-locator`, `visual-regression-sentinel`, `auth-session-and-cookie-manager` | `tools/safety_firewall.py`, `tools/lookup_xpath.py`, `tools/visual_diff_canvas.py`, `tools/browser_helpers.js` |
| **`pom-crafter`** | Clean POM engineer, API drift detection, User Story to test generation. | `clean-pom-crafter`, `lam-script-generator`, `synthetic-test-data-generator`, `api-spec-to-e2e-matrix`, `file-and-report-validator`, `db-state-verifier-and-seeder` | `tools/generate_tc_from_story.py`, `tools/generate_api_matrix.py`, `tools/api_drift_sentinel.py`, `tools/repo_map.py` |
| **`test-runner`** | Headless CLI suite manager, CI parallel sharding and log distillation. | `katalon-cli-runner`, `e2e-testing-patterns`, `bats-testing-patterns`, `auth-session-and-cookie-manager`, `flaky-test-sentinel-and-quarantine` | `tools/matrix_sharder.py`, `tools/distill_log.py`, `tools/pinpoint_failure.py`, `tools/flaky_detector.py` |
| **`failure-analyst`**| Automated closed-loop failure triage, MTTR scoring, self-healing PR drafting. | `failure-autopsy-and-healing`, `self-healing-locator`, `file-and-report-validator` | `tools/auto_heal.py`, `tools/heal_pr_automator.py`, `tools/pinpoint_failure.py`, `tools/cache_resolver.py` |
| **`quality-gatekeeper`**| Enforces 8 Quality Gates DoD, scans fake passes, runs AST mutation testing. | `antigravity-test-sentinel`, `code-refactoring-refactor-clean`, `wcag-audit-patterns`, `web-vitals-and-performance-profiler`, `db-state-verifier-and-seeder`, `security-dast-sentinel` | `tools/verify_all.py`, `tools/infer_linter.py`, `tools/micro_mutator.py`, `tools/trace_data_flow.py`, `tools/wcag_audit.py`, `tools/lint_ai_docs.py` |

---

## 📦 4. Standardized 27 Skills Catalog (.agents/skills/)

| # | Skill Name | Core Operational Scope |
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

---

## 📜 5. 7 Core Rules Catalog (.agents/rules/)

1. **`context-engineering.md`**: Observation masking, lazy progressive disclosure, and KV-cache optimization.
2. **`git-push-protocol.md`**: Clean git push protocol (decoupled architecture guarantees zero AI leakage).
3. **`graphify.md`**: Navigating the AST knowledge graph over reading entire large source files.
4. **`lessons-learned.md`**: Episodic anti-pattern blacklist (strictly capped under 40 lines).
5. **`mandatory-playwright-live.md`**: Mandatory headless Full HD 1920x1080 and live DOM probing before codifying.
6. **`skill-precedence.md`**: Tier-1 local skill precedence resolving external plugin collisions.
7. **`systematic-debugging.md`**: Evidence-first debugging discipline; zero guessing; 8 Quality Gates DoD.

---

## 🛠️ 6. Automated Tools Runbook (tools/ & scripts/)

For full details, refer to [tools/TOOLS_RUNBOOK.md](tools/TOOLS_RUNBOOK.md):

- `tools/verify_all.py`: 8 Quality Gates DoD verification (UTF-8, No XPaths, UniqueCode, Clean POM).
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
- `scripts/lint_skills.ps1`: Linter verifying skill integrity and metadata manifest.
- `pyproject.toml` & `tools/cli.py`: PEP 621 packaging for the global `agent-qa` CLI.

---

## 📚 7. Extended Technical Documentation & CLI Package (docs/)

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Hub/Spoke architecture, 4-tier skill model, and 6-agent swarm coordination.
2. **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Contribution standards, new skill authoring principles, and verification pipelines.
3. **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)**: Comprehensive command-line reference for the `agent-qa` CLI.

### Quick CLI Installation:
```bash
pip install -e .
agent-qa --help
agent-qa verify
agent-qa lint
```
