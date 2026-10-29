# 🧠 AI Agent Skills & Intelligence Hub

> **Kho lưu trữ trung tâm các Kỹ năng (Skills), Quy tắc (Rules), Công cụ (Tools) và Quy trình tự động hóa (Workflows) cho Trợ lý AI (Google Antigravity / Cursor / Windsurf / Claude Code).**  
> **Phiên bản Hub:** `v2.0.0` (Semantic Versioning) | **Chỉ số toàn vẹn:** 27 Skills, 6 Agent Swarm Roles, 7 Core Rules, 20+ Python Tools.

---

## 🌟 1. Tổng quan & Mục đích Kiến trúc

Repository này đóng vai trò là **"Bộ não dùng chung" (Shared Intelligence Core)**, tách biệt hoàn toàn khỏi mã nguồn của từng dự án cụ thể.

```mermaid
flowchart TD
    subgraph Hub["🧠 agent-skills (Intelligence Core v2.0.0)"]
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

### Cách A: Sử dụng tức thì qua NPM / npx (Khuyên dùng cho Web, Node & Playwright)
Tại thư mục bất kỳ của dự án đích, bạn có thể thực thi ngay mà không cần clone hay cài đặt trước:
```bash
# 1-Click Bootstrap dự án (tự động sinh PROJECT_AI_GUIDE.md, cài pre-push hook, trích xuất AST map)
npx agent-skills setup

# Chạy kiểm tra 8 Quality Gates DoD
npx agent-skills verify

# Đánh giá sức khỏe dự án toàn diện (5-in-1 Project Health Report)
npx agent-skills analyze

# Cài đặt cố định vào devDependencies của dự án mục tiêu
npm install -D agent-skills
```

### Cách B: Mở phiên làm việc đa thư mục (Multi-Root Workspace)
Trong IDE (Google Antigravity / VS Code / Cursor):
1. Mở thư mục dự án mục tiêu của bạn.
2. Thêm thư mục `agent-skills` vào Workspace (`File` -> `Add Folder to Workspace...`).

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
