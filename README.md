# 🧠 Synapse Hub — Trung Tâm Trí Tuệ & Mạng Lưới Kỹ Năng Cho AI Agent

[🇻🇳 Tiếng Việt](#-synapse-hub--trung-tâm-trí-tuệ--mạng-lưới-kỹ-năng-cho-ai-agent) | [🇬🇧 English Edition](#-english-edition)

> **Bộ não trí tuệ dùng chung và mạng lưới kỹ năng tự hành, tăng cường năng lực cho các trợ lý AI (Google Antigravity, Cursor, Windsurf, Claude Code) trên mọi hệ sinh thái kiểm thử tự động.**  
> **Tác giả:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))  
> **Phiên bản Hub:** `v2.3.0` | **Quy mô:** 29 Kỹ năng chuẩn hóa, 7 Workflows thực chiến, 6 Vai trò AI Swarm, 10 Quy tắc cốt lõi, 50+ Công cụ tự động.

---

### 🚫 Phạm Vi Hoạt Động & Những Gì Dự Án KHÔNG Làm (Non-Goals)

Để duy trì kiến trúc tinh gọn và chuyên sâu cho Quality Engineering, Synapse Hub xác định rõ ranh giới kiến trúc:
- **KHÔNG phải là Test Runner thay thế:** Synapse Hub không tự phát minh test runner mới; dự án tận dụng và điều phối các runner tiêu chuẩn công nghiệp (Playwright, Pytest, Katalon/Gradle, Newman, JMeter).
- **KHÔNG can thiệp mã nguồn ứng dụng (AUT Production Code):** Hub chỉ tập trung vào mã kiểm thử, Page Object, bộ lọc log, dữ liệu tổng hợp và cổng chất lượng.
- **KHÔNG lưu trữ thông tin nhạy cảm tập trung:** Toàn bộ session, cookies, mật khẩu phải được quản trị qua biến môi trường hoặc file cục bộ được gitignore (`.auth/*.json`), không bao giờ đồng bộ lên remote.
- **KHÔNG ép buộc công nghệ cố định:** Thiết kế theo mô hình tách rời (Decoupled Hub & Spoke), hỗ trợ linh hoạt đa ngôn ngữ (TypeScript, Python, Java, Groovy) qua Universal Intermediate Representation (IR).

---

## 🌟 1. Tổng quan & Mục đích Kiến trúc

**Synapse Hub** là tầng trí tuệ đa tác tử tách rời (**Decoupled Shared Intelligence Core**), đóng vai trò như một **"Bộ não dùng chung"**, tách biệt hoàn toàn khỏi mã nguồn của từng dự án cụ thể. Dự án trang bị cho AI agents đội ngũ Sub-Agent QC chuyên biệt (Multi-Agent Swarm), quy trình tự chữa lành (Self-Healing), khả năng thấu hiểu mã nguồn cấp độ AST và các cổng chất lượng nghiêm ngặt (Quality Gates)—cho phép tự động hóa kiểm thử chuẩn xác tuyệt đối trên mọi codebase mà không làm bẩn repository mục tiêu.

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
        ProjectC["Dự án C<br/>(PROJECT_AI_GUIDE.md + App Code)"]
        Other["Dự án khác..."]
    end

    ProjectA -->|Mount Workspace| ChatSession
    ProjectB -.->|Mount Workspace| ChatSession
    ProjectC -.->|Mount Workspace| ChatSession
    Other -.->|Mount Workspace| ChatSession
```

### 💎 Lợi Ích Đột Phá Khi Sử Dụng Synapse Hub:

#### 1. 🧠 Khả Năng Suy Nghĩ Có Chiều Sâu (System-2 Reasoning & Cognitive Forcing)
* **Xóa bỏ chế độ "Autocomplete vô thức":** Khi đối mặt với lỗi kiểm thử hoặc yêu cầu viết test mới, AI không tự tiện sinh code ngẫu nhiên theo trực giác mà bị **ép buộc đi qua quy trình tư duy 4 bước (Cognitive Forcing Pipeline)**:
  1. *Trích xuất bất biến (Invariants):* Điều gì bắt buộc không bao giờ được phép xảy ra?
  2. *Giả định phản nghiệm (Popper Falsification):* Đặt ra 3 kịch bản lập trình viên làm hàm chạy sai nhưng test ngây ngô vẫn pass (False Negatives).
  3. *Tự phản biện (Self-Debate):* Tự chứng minh tại sao assertion chuẩn bị viết sẽ bắt chết cả 3 kịch bản lỗi trên.
  4. *Sinh code phòng vệ:* Chỉ xuất mã khi đã vượt qua 3 tầng lập luận.
* **Tự đối kháng Red-Team vs Blue-Team:** Tự động tiêm đột biến AST (`tools/micro_mutator.py`) vào code kiểm thử để kiểm tra xem test suite có thực sự bắt được bug thật hay không. Bắt buộc **Điểm đột biến (Mutation Score) $\ge 80\%$** mới cho phép hoàn thành tác vụ.

#### 2. ⚡ Siêu Tiết Kiệm Token (Cắt Giảm 85% – 95% Chi Phí Context)
* **Log Distillation (Giảm 95% token log):** Công cụ `tools/distill_log.py` tự động lọc sạch 95% log rác dài lê thê của CLI/Gradle/Playwright, chỉ giữ lại đúng ~10 dòng chứa dòng lỗi và exception (< 50 tokens) thay vì ném 3.000 dòng log làm loãng context.
* **AST Repo Mapping (Giảm 90% token đọc file):** Công cụ `tools/repo_map.py` nén 500+ method signatures vào đúng một bản đồ tóm tắt < 600 tokens. AI nắm toàn bộ hàm và class mà **không bao giờ phải mở đọc cả file 4.000 dòng** gây nổ context window ("Context Window Blowout").
* **Compact AOM (Giảm 90% token HTML):** Không bao giờ dump cả trang HTML DOM 50.000 dòng vào prompt; công cụ trích xuất cây Accessibility Object Model (AOM) tương tác dưới 500 tokens.
* **Zero-Token SQLite Memory Cache:** Ghi nhận và tra cứu kinh nghiệm sửa bug qua cơ sở dữ liệu SQLite ngoại tuyến (`~/.agent_memory/global_cache.db`) bằng thuật toán vector cosine similarity với chi phí **0 token context**.
* **Chống suy thoái ngữ cảnh ("Context Rot" & "Lost-in-the-Middle"):** Đảm bảo AI luôn duy trì sự minh mẫn, không bao giờ bị ảo giác hay quên logic nghiệp vụ ngay cả trong các phiên làm việc dài trên 100.000 tokens.

#### 3. 📊 So Sánh Hiệu Năng Thực Tế:

| Tiêu chí đánh giá | Cách làm thông thường (Naive AI Prompting) | Khi sử dụng Synapse Hub 🧠 | Phương pháp & Bằng chứng kiểm chứng |
| :--- | :---: | :---: | :--- |
| **Token tiêu thụ / mỗi lần fix lỗi** | 15.000 – 40.000 tokens *(đọc cả file lớn, dump cả log)* | **300 – 800 tokens** | Đo trên micro-turn fix locator: `tools/distill_log.py` giảm 95% log + `tools/repo_map.py` nén AST signatures < 600 tokens (chưa gồm ~7k token system prefix ban đầu). |
| **Tỷ lệ Fake-Pass (Test pass ảo, 0 assert)** | 30% – 50% *(AI có xu hướng nuốt lỗi để báo PASS)* | **Chặn đứng ở Gates** | Gate 0 & Gate 7 (`tools/infer_linter.py`) quét AST bắt nuốt exception và script thiếu assert; Gate 8 (`tools/micro_mutator.py`) yêu cầu Mutation Score $\ge 80\%$. |
| **Trí nhớ sửa lỗi xuyên phiên (Cross-Session)** | Quên sạch ngay khi mở tab chat mới | **Bền vững qua SQLite Central Cache** | Lưu và tra cứu giải pháp qua SQLite vector cosine tại `~/.agent_memory/global_cache.db` (lệnh: `python tools/cache_resolver.py query "<error>"`). |
| **Hiện tượng quên ngữ cảnh (Context Rot)** | Xảy ra nhanh chóng sau 40k – 60k tokens | **Giảm thiểu rõ rệt** | Phân tầng thông tin 3 cấp: repo_map (Tier 1) ➔ dependency graph (Tier 2) ➔ micro-read 20-50 dòng (Tier 3). |
| **Thời gian tự phục hồi lỗi (MTTR)** | 5 – 15 phút mò mẫm thử nghiệm | **Tức thì khi cache hit (< 1s)** | Khi lỗi đã có trong SQLite cache, `cache_resolver.py` giải quyết trong < 0.1s thay vì lặp prompt tìm kiếm. |

*(Lưu ý: 300–800 token là chi phí ngữ cảnh động của từng lượt sửa lỗi vi mô (micro-turn payload) nhờ repo_map và distill_log; chưa tính chi phí nạp hệ thống/rules ban đầu của IDE ~7.000 tokens).*

---

## 🚀 2. Hướng Dẫn Bắt Đầu & Tích Hợp (3 Cách Dùng)

[![npm version](https://img.shields.io/npm/v/synapse-hub.svg?style=flat-square&color=blue)](https://www.npmjs.com/package/synapse-hub)
[![node version](https://img.shields.io/badge/node-%3E%3D16.0.0-brightgreen.svg?style=flat-square)](https://nodejs.org)
[![license](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](https://github.com/TeeVee998/Synapse-Hub/blob/main/LICENSE)

---

### ⚡ Khởi Động Siêu Tốc: Đúng 1 Lệnh Duy Nhất Với NPX (All-in-One 🚀)
*Tất cả trong một: **KHÔNG CẦN clone repo Hub**, **KHÔNG CẦN mở Multi-root workspace**, tự động cấu hình dự án **VÀ tự động bơm thẳng vào Antigravity Global Plugin**.*

Mở terminal ngay tại thư mục **dự án kiểm thử của bạn** và chạy đúng 1 dòng:
```bash
npx synapse-hub setup
```
👉 **Đúng 1 lệnh này sẽ tự động hoàn tất toàn bộ trong 5 giây:**
1. 🧠 **Tự động bơm vào Antigravity Global Plugin:** Triển khai Synapse-Hub vào `~/.gemini/config/plugins/synapse-hub`. Kể từ giây phút này, **mọi dự án** mở trên Google Antigravity đều tự động sở hữu toàn bộ 28 Skills và 6 Subagents mà không cần cấu hình thêm!
2. 🌐 **Triển Khai Cầu Nối Đa IDE & AI (Universal AI Bridges):** Tự động sinh file cấu hình và quy chuẩn cho mọi trợ lý AI khác nhau ngay trong dự án của bạn:
   - 🖱️ **Cursor:** `.cursor/rules/synapse-qa.mdc` (Tự động kích hoạt khi mở file trong Cursor)
   - 🤖 **Claude Code:** `CLAUDE.md` (Hướng dẫn quy chuẩn QA, commands và Clean POM)
   - 🐙 **GitHub Copilot:** `.github/copilot-instructions.md` (Chỉ dẫn hệ thống cho VS Code / JetBrains Copilot)
   - 🏄 **Windsurf (Cascade):** `.windsurfrules` (Nguyên tắc kiểm thử bắt buộc)
   *(Mọi thành viên dù dùng Antigravity, Cursor, Claude Code, Copilot hay Windsurf đều chung 1 chuẩn Clean POM, 1 nguyên tắc Truth Anchor chống pass ảo, và 9 Cổng Kiểm Định DoD (Gate 0–8)!)*
3. 🔍 **Nhận diện Framework:** Tự động phát hiện Playwright TypeScript/JS, Katalon Studio Groovy, Cypress, hoặc Pytest.
4. 📋 **Sinh Hướng Dẫn Nghiệp Vụ:** Tạo file `PROJECT_AI_GUIDE.md` ngay trong dự án của bạn để AI hiểu sâu kiến trúc và quy chuẩn code.
5. 🛡️ **Cài Đặt Cổng Gác Git (Pre-Push Hook):** Tự cài `.git/hooks/pre-push` gọi `npx synapse-hub verify` để chặn đứng mã lỗi và lộ mật khẩu trước khi push.
6. 💾 **Khởi Tạo Bộ Nhớ Kinh Nghiệm (SQLite Cache):** Khởi tạo và nạp giải pháp sửa lỗi UI vào `~/.agent_memory/global_cache.db` (chi phí 0 token).
7. 🗺️ **Quét AST & Xuất Bản Đồ Hàm:** Tự động phân tích codebase và trích xuất `repo_map.txt` cô đọng.

Sau đó, bạn có thể thực thi kiểm định bất cứ lúc nào:
```bash
# Kiểm định 9 Cổng Chất Lượng (DoD Quality Gates Gate 0–8)
npx synapse-hub verify

# Đánh giá sức khỏe toàn diện dự án (5-in-1 Project Health Report)
npx synapse-hub analyze

# Quét phát hiện mã giả, assertion rỗng (Fake-Pass AST Sentinel)
npx synapse-hub lint
```

---

### 🥈 Cách 2: Tối Ưu Cho Antigravity — Cài Đặt 1 Lần Thành "Global Plugin"
*Cài đặt 1 lần duy nhất: Kể từ đó **BẤT KỲ DỰ ÁN NÀO** mở trên Google Antigravity cũng tự động có sẵn toàn bộ 28 Skills và 6 Subagents mà không cần cấu hình thêm.*

#### Bước cài đặt 1-Click:
```powershell
# Trên Windows PowerShell:
./scripts/install_global_plugin.ps1

# Trên macOS / Linux:
./scripts/install_global_plugin.sh
```

*(Hoặc nếu chưa clone repo, chỉ cần clone thẳng vào thư mục plugin của Antigravity):*
```bash
git clone https://github.com/TeeVee998/Synapse-Hub.git "$HOME/.gemini/config/plugins/synapse-hub"
```

**Sau khi cài đặt:**
- Mở Google Antigravity lên, bạn sẽ thấy `synapse-hub` xuất hiện trong danh mục Plugins toàn cục.
- Mở bất kỳ thư mục dự án nào, AI Agent cũng tự động nắm bắt toàn bộ năng lực kiểm thử của Synapse-Hub!

---

### 🥉 Cách 3: Truyền Thống — Mở Multi-Root Workspace trong IDE
*Dành cho Core Developers muốn chỉnh sửa, mở rộng hoặc đóng góp phát triển thêm Skills/Tools cho Synapse-Hub.*

1. Mở IDE (Google Antigravity / Cursor / VS Code).
2. Mở thư mục dự án mục tiêu của bạn (`File -> Open Folder`).
3. Thêm thư mục `Synapse-Hub` vào Workspace (`File -> Add Folder to Workspace...`).
4. Chạy script bootstrap môi trường nội bộ:
```powershell
# Windows PowerShell
./scripts/install.ps1

# Linux / macOS
./scripts/setup.sh
```

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
| **`quality-gatekeeper`**| Gác cổng chất lượng 9 Gates DoD (Gate 0–8), quét Fake-Pass, bơm mutant. | `antigravity-test-sentinel`, `code-refactoring-refactor-clean`, `wcag-audit-patterns`, `web-vitals-and-performance-profiler`, `db-state-verifier-and-seeder`, `security-dast-sentinel`, `skillspector-security-guard` | `tools/verify_all.py`, `tools/infer_linter.py`, `tools/micro_mutator.py`, `tools/trace_data_flow.py`, `tools/wcag_audit.py`, `tools/lint_ai_docs.py`, `tools/skillspector.py` |

---

## 📦 4. Danh Mục 29 Kỹ Năng Chuẩn Hóa (.agents/skills/)

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
| 29 | `rbt-manual-testing` | Quy trình 6 bước AI-RBT sinh Test Case thủ công, ma trận rủi ro $P \times I$, bảng Ambiguity Log, ma trận 12 cột, checklist 15 loại input field và kịch bản phi chức năng (Double-Submit, Race Conditions). |

---

## 📜 5. Danh Mục 10 Quy Tắc Cốt Lõi (.agents/rules/)

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

---

## 📋 6. Hệ Thống 7 Workflows Thực Chiến (.agents/workflows/)

Synapse Hub cung cấp 7 quy trình làm việc chuẩn hóa dưới dạng các câu lệnh trực quan (Slash Commands / Prompts):

| Workflow | Mục Đích Nghiệp Vụ Cốt Lõi |
| :--- | :--- |
| **`generate_manual_testcases_rbt.md`** | Phân tích rủi ro $P \times I$, giải quyết câu hỏi mập mờ (Ambiguity Q&A), và sinh ma trận test case 12 cột. |
| **`generate_testcases_from_requirements.md`** | Chuyển đổi trực tiếp tài liệu đặc tả (BRD, SRS, User Stories) thành bộ kiểm thử chấp nhận (Acceptance Tests). |
| **`generate_cross_module_test_plan.md`** | Lập kế hoạch kiểm thử luồng nghiệp vụ E2E xuyên suốt nhiều module (Cart ➔ Checkout ➔ Payment ➔ Warehouse). |
| **`generate_combinatorial_test_data.md`** | Sinh tập dữ liệu kiểm thử tổ hợp All-Pairs / Pairwise bao phủ tối đa trường hợp biên với số ca test tối thiểu. |
| **`generate_requirements_from_website.md`** | Tự động thám sát Live Web bằng Playwright headless để trích xuất ngược đặc tả nghiệp vụ (Reverse-Engineering). |
| **`analyze_requirement_document.md`** | Quét phát hiện mâu thuẫn logic, khoảng trống nghiệp vụ và các phát biểu mơ hồ trong tài liệu PRD. |
| **`export_testcases_excel.md`** | Xuất bảng Test Case từ Markdown sang file Excel (.xlsx) chuẩn doanh nghiệp với màu sắc trực quan qua OpenPyXL. |

---

## 🧪 7. Kho Dữ Liệu Thực Hành Mẫu (examples/practices/)

Tập hợp các tài liệu đặc tả và bộ test cases mẫu từ các hệ thống thực tế dùng làm điểm tựa chuẩn hóa (Golden Benchmarks) và học Few-Shot:

- **`requirements/crm/`**: Đặc tả chức năng hệ thống CRM (Đăng nhập, Quản lý Khách hàng, Dự án, Hợp đồng, Công việc).
- **`requirements/ecommerce/`**: Quy chuẩn quản lý Danh mục sản phẩm (Categories) và Thương hiệu (Brands).
- **`requirements/jira/`**: Dữ liệu xuất mẫu từ Jira Kanban Epic/Stories (`KAN-1` đến `KAN-6`) kèm ảnh chụp UI mẫu.
- **`testcases/crm/` & `testcases/api/`**: Bộ Test Case UI và REST API mẫu (User Management, Book Management) chuẩn AI-RBT.

---

## 🛠️ 8. Sổ Tay 50+ Công Cụ Tự Động Hóa Chuyên Biệt (tools/ & scripts/)

Chi tiết đầy đủ xem tại [tools/TOOLS_RUNBOOK.md](tools/TOOLS_RUNBOOK.md):

- `tools/verify_all.py`: Cổng thẩm định 9 Gates DoD (Gate 0–8: UTF-8, No XPaths, UniqueCode, Clean POM, AST Mutation).
- `tools/md_to_xlsx.py` (`agent-qa export-excel`): Xuất bảng Test Case từ Markdown sang file Excel (.xlsx) chuyên nghiệp (định dạng header doanh nghiệp, frozen panes, auto-fit cột, huy hiệu màu P1-P4).
- `tools/generate_jmx_plan.py`: Sinh kịch bản Apache JMeter 5.x (.jmx) đa giao thức (HTTP, JDBC, WS, gRPC, Kafka) kèm Traffic Shaping Pareto.
- `tools/jtl_analyzer.py`: Phân tích kết quả JTL, kiểm soát SLA percentiles ($P_{90}, P_{95}, P_{99}$) và làm Quality Gate CI/CD.
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
- `scripts/lint_skills.ps1`: Linter kiểm tra tính toàn vẹn 29 skills và metadata manifest.
- `pyproject.toml` & `tools/cli.py`: Đóng gói chuẩn PEP 621 cho lệnh CLI toàn cầu `agent-qa`.

---

## 📚 9. Tài Liệu Kỹ Thuật Mở Rộng & CLI Package (docs/)

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Kiến trúc Hub/Spoke, mô hình 4 tầng kỹ năng, và ma trận phối hợp 6 Subagent Swarm.
2. **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Quy chuẩn đóng góp, nguyên tắc sáng tạo skill mới và quy trình kiểm định toàn vẹn.
3. **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)**: Cẩm nang tra cứu toàn bộ tham số lệnh của công cụ dòng lệnh `agent-qa`.
4. **[docs/TOKEN_QUOTA_PLAYBOOK.md](docs/TOKEN_QUOTA_PLAYBOOK.md)**: Chiến lược phân tầng mô hình (Claude Sonnet vs Gemini Pro vs Gemini Flash), tối ưu chi phí và điều hướng theo hạn mức API quota.

### Cài đặt nhanh CLI Package:
```bash
pip install -e .
agent-qa --help
agent-qa verify
agent-qa lint
agent-qa export-excel
```

---

## 🤝 10. Nguồn Cảm Hứng & Lời Cảm Ơn (Acknowledgments & Inspirations)

Dự án **Synapse Hub** được tổng hợp, kế thừa và phát triển dựa trên tinh thần mã nguồn mở và những ý tưởng đột phá từ các kho lưu trữ xuất sắc của cộng đồng kỹ nghệ phần mềm & AI:

| Dự án & Tác giả | Nguồn cảm hứng & Đóng góp kiến trúc trong Synapse Hub |
| :--- | :--- |
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

---

## 📄 11. Bản Quyền & Điều Khoản Sử Dụng (License & Attribution)

Dự án được phân phối chính thức dưới giấy phép **[MIT License](LICENSE)**.

**Quyền sở hữu tác giả & Xuất xứ (Provenance):**
- **Tác giả & Nhà sáng lập:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))
- **Mã nguồn gốc:** [https://github.com/TeeVee998/Synapse-Hub](https://github.com/TeeVee998/Synapse-Hub)
- **Bản quyền:** Copyright © 2026 Thế Vị (@TeeVee998). Phân phối theo giấy phép MIT.

> ⚖️ **Điều khoản phân phối theo giấy phép MIT:** Bạn được toàn quyền sử dụng, sao chép, sửa đổi, hợp nhất, xuất bản và phân phối mã nguồn này cho bất kỳ mục đích cá nhân hay thương mại nào, **VỚI ĐIỀU KIỆN** thông báo bản quyền gốc ghi nhận tác giả **Thế Vị (@TeeVee998)** cùng điều khoản cấp phép này phải được giữ nguyên vẹn trong toàn bộ bản sao hoặc các phần quan trọng của phần mềm.

---

# 🌐 English Edition

# 🧠 Synapse Hub — AI Agent Intelligence Core & Skill Network

> **The shared intelligence core and autonomous skill hub empowering AI coding assistants (Google Antigravity / Cursor / Windsurf / Claude Code) across automated testing suites.**  
> **Author:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))  
> **Hub Version:** `v2.3.0` (Semantic Versioning) | **Integrity Index:** 29 Skills, 7 Production Workflows, 6 Agent Swarm Roles, 10 Core Rules, 50+ Specialized Python Tools, 9 Quality Gates.

---

### 🚫 Project Scope & Explicit Non-Goals

To maintain a lightweight and focused architecture for Quality Engineering, Synapse Hub defines clear boundaries:
- **NOT an Alternative Test Runner:** Synapse Hub does not reinvent test runners; it orchestrates and supercharges industry-standard runners (Playwright, Pytest, Katalon/Gradle, Newman, JMeter).
- **Zero Modifications to AUT Production Code:** Synapse Hub operates strictly on test code, page objects, log filters, synthetic test data, and quality gates.
- **Zero Centralized Secret Storage:** All sessions, cookies, and tokens are stored in environment variables or gitignored local files (`.auth/*.json`), never committed to remote repositories.
- **Framework & Vendor Agnostic:** Adheres to a decoupled Hub-and-Spoke topology, accommodating polyglot stacks (TypeScript, Python, Java, Groovy) via Universal Intermediate Representation (IR).

---

## 🌟 1. Overview & Architectural Purpose

**Synapse Hub** serves as a **Decoupled Shared Intelligence Core**, acting as an external neural brain completely isolated from target projects' codebases. It equips AI agents with specialized swarm roles, self-healing execution protocols, AST-level code intelligence, and strict Quality Gates—enabling zero-leakage, truth-anchored test automation across any polyglot codebase without polluting target repositories.

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
        ProjectC["Project C<br/>(PROJECT_AI_GUIDE.md + App Code)"]
        Other["Other Projects..."]
    end

    ProjectA -->|Mount Workspace| ChatSession
    ProjectB -.->|Mount Workspace| ChatSession
    ProjectC -.->|Mount Workspace| ChatSession
    Other -.->|Mount Workspace| ChatSession
```

### 💎 Breakthrough Architectural Benefits:

#### 1. 🧠 Deep System-2 Reasoning & Cognitive Forcing
* **Eliminates "Unconscious Autocomplete":** When diagnosing failures or generating tests, the AI agent is strictly barred from speculative guesswork and **forced through a 4-step System-2 reasoning pipeline**:
  1. *Boundary & Invariant Extraction:* What must never happen under any circumstance?
  2. *Popper Falsification Hypotheses:* Formulate 3 distinct code mutation scenarios where a naive test passes while the software is broken (False Negatives).
  3. *Self-Debate:* Formulate concrete proof showing why the prospective assertion will definitively catch all 3 defect vectors.
  4. *Defensive Code Synthesis:* Emit code only after passing all 3 analytical gates.
* **Adversarial Red-Team vs. Blue-Team Self-Play:** Automatically injects AST micro-mutants (`tools/micro_mutator.py`) into test suites to verify fault detection power, requiring **Mutation Score $\ge 80\%$** before task approval.

#### 2. ⚡ Radical Token Optimization (85% – 95% Context Cost Reduction)
* **Log Distillation (95% Token Savings):** `tools/distill_log.py` automatically purges 95% of verbose CLI/Gradle/Playwright stdout, preserving only ~10 lines of root-cause exceptions and pointers (< 50 tokens) instead of dumping 3,000 noise lines.
* **AST Repo Mapping (90% Code Reading Savings):** `tools/repo_map.py` compresses 500+ method signatures into a clean AST map (< 600 tokens). Agents discover classes and helpers without ever reading 4,000-line source files (preventing "Context Window Blowouts").
* **Compact AOM (90% HTML Savings):** Replaces raw 50,000-line HTML DOM dumps with compact Accessible Object Model (AOM) subtrees (< 500 tokens).
* **Zero-Token Episodic SQLite Memory:** Errors and healing patches are recorded and resolved offline in `~/.agent_memory/global_cache.db` via cosine similarity at **0 context tokens**.
* **Anti-Degradation ("Context Rot" & "Lost-in-the-Middle"):** Preserves model reasoning sharpness and prevents hallucinations even during long sessions exceeding 100,000 tokens.

#### 3. 📊 Quantitative Performance Benchmark:

| Evaluation Metric | Naive AI Coding Prompting | With Synapse Hub 🧠 | Empirical Verification Method |
| :--- | :---: | :---: | :--- |
| **Tokens Consumed per Bug Fix** | 15,000 – 40,000 tokens *(dumps entire classes & logs)* | **300 – 800 tokens** | Measured per micro-turn locator fix via `distill_log.py` (95% log compression) + `repo_map.py` (< 600 token signatures). Excludes ~7k tokens one-time system prompt prefix. |
| **Fake-Pass Rate (0 asserts, false passes)** | 30% – 50% *(LLMs tend to relax asserts)* | **Enforced by Quality Gates** | Gate 0 & Gate 7 (`infer_linter.py`) block swallowed exceptions and missing asserts; Gate 8 (`micro_mutator.py`) enforces Mutation Score $\ge 80\%$. |
| **Cross-Session Fix Memory** | 100% forgotten upon new chat session | **Persistent via SQLite Central Cache** | Persisted and queried offline via SQLite vector cosine in `~/.agent_memory/global_cache.db` (CLI: `python tools/cache_resolver.py query "<error>"`). |
| **Context Rot / Lost-in-the-Middle** | High degradation after 40k – 60k tokens | **Significantly Mitigated** | 3-tier Progressive Disclosure: repo_map (Tier 1) ➔ dependency graph (Tier 2) ➔ micro-read 20-50 lines (Tier 3). |
| **Mean Time-to-Heal (MTTR)** | 5 – 15 minutes of trial-and-error | **Sub-second on cache hits** | Pre-cached failure vectors resolve deterministically in < 0.1s without repetitive trial-and-error prompt iterations. |

*(Note: 300–800 tokens represents the dynamic micro-turn execution payload achieved via repo_map and distill_log, excluding the one-time IDE system rules prefix overhead of ~7,000 tokens).*

---

## 🚀 2. Getting Started & Integration (3 Approaches)

[![npm version](https://img.shields.io/npm/v/synapse-hub.svg?style=flat-square&color=blue)](https://www.npmjs.com/package/synapse-hub)
[![node version](https://img.shields.io/badge/node-%3E%3D16.0.0-brightgreen.svg?style=flat-square)](https://nodejs.org)
[![license](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](https://github.com/TeeVee998/Synapse-Hub/blob/main/LICENSE)

---

### ⚡ Instant All-in-One Setup: Single NPX Command (Zero-Clone 🚀)
*All-in-one execution: **NO git cloning**, **NO multi-root workspace setup**, configures the target project **AND automatically injects into Antigravity Global Plugin**.*

Run directly from your **target automation project root**:
```bash
npx synapse-hub setup
```
👉 **This single command automatically completes everything in 5 seconds:**
1. 🧠 **Injects Antigravity Global Plugin:** Deploys Synapse-Hub into `~/.gemini/config/plugins/synapse-hub`. From this moment on, **ALL projects** opened in Google Antigravity automatically inherit all 28 Skills and 6 Subagent profiles!
2. 🌐 **Universal AI Bridges Deployment:** Automatically generates tailored configuration rules for all leading AI IDEs and assistants:
   - 🖱️ **Cursor:** `.cursor/rules/synapse-qa.mdc`
   - 🤖 **Claude Code:** `CLAUDE.md`
   - 🐙 **GitHub Copilot:** `.github/copilot-instructions.md`
   - 🏄 **Windsurf (Cascade):** `.windsurfrules`
   *(Empowers team members across Antigravity, Cursor, Claude Code, Copilot, or Windsurf to enforce the exact same Clean POM architecture, Truth Anchor, and 9 Quality Gates DoD (Gate 0–8)!)*
3. 🔍 **Tech Stack Detection:** Auto-detects Playwright TypeScript/JS, Katalon Groovy, Cypress, or Pytest.
4. 📋 **Project AI Guide Synthesis:** Generates `PROJECT_AI_GUIDE.md` so AI assistants strictly adhere to project workflows.
5. 🛡️ **Zero-Leakage Git Pre-Push Hook:** Installs `.git/hooks/pre-push` invoking `npx synapse-hub verify` before any git push.
6. 💾 **Central Agent Memory Initialization:** Seeds offline SQLite healing memory at `~/.agent_memory/global_cache.db` (0 token cost).
7. 🗺️ **AST Architecture Mapping:** Scans project methods and exports condensed context map (`repo_map.txt`).

Run verification anytime:
```bash
# Run 9 Quality Gates DoD Verification (Gate 0–8)
npx synapse-hub verify

# Comprehensive 5-in-1 Project Health Audit
npx synapse-hub analyze

# Static Defect & Fake-Pass Sentinel scan
npx synapse-hub lint
```

---

### 🥈 Method 2: Antigravity-Native — Install Once as Global Plugin
*Install once: From that moment onward, **ANY project** opened in Google Antigravity automatically inherits all 28 Skills and 6 Subagent Swarm profiles.*

#### 1-Click Plugin Installation:
```powershell
# On Windows PowerShell:
./scripts/install_global_plugin.ps1

# On macOS / Linux:
./scripts/install_global_plugin.sh
```

*(Or clone directly into Antigravity's Global Plugins folder):*
```bash
git clone https://github.com/TeeVee998/Synapse-Hub.git "$HOME/.gemini/config/plugins/synapse-hub"
```

**Result:**
- Google Antigravity registers `synapse-hub` globally.
- Every workspace session automatically loads the complete QA intelligence core without manual workspace mounts!

---

### 🥉 Method 3: Multi-Root Workspace Mounting
*For Core Developers looking to extend, customize, or contribute new Skills and Tools directly to Synapse-Hub.*

1. Open your AI IDE (Google Antigravity / Cursor / VS Code).
2. Open your target test project (`File -> Open Folder`).
3. Add `Synapse-Hub` to your workspace (`File -> Add Folder to Workspace...`).
4. Run the local environment bootstrap script:
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
| **`quality-gatekeeper`**| Enforces 9 Quality Gates DoD (Gate 0–8), scans fake passes, runs AST mutation testing. | `antigravity-test-sentinel`, `code-refactoring-refactor-clean`, `wcag-audit-patterns`, `web-vitals-and-performance-profiler`, `db-state-verifier-and-seeder`, `security-dast-sentinel`, `skillspector-security-guard` | `tools/verify_all.py`, `tools/infer_linter.py`, `tools/micro_mutator.py`, `tools/trace_data_flow.py`, `tools/wcag_audit.py`, `tools/lint_ai_docs.py`, `tools/skillspector.py` |

---

## 📦 4. Standardized 29 Skills Catalog (.agents/skills/)

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
| 28 | `skillspector-security-guard` | AI agent skill & MCP config security auditing against 71 vulnerability vectors (Prompt Injection, Data Exfiltration, Privilege Escalation) powered by NVIDIA SkillSpector spec. |
| 29 | `rbt-manual-testing` | 6-stage Risk-Based Testing (AI-RBT) manual test case synthesis, $P \times I$ risk scoring, Ambiguity Q&A log, 12-column matrix, 15-field validation checklist, and non-functional resilience scenarios (Double-Submit, Race Conditions). |

---

## 📜 5. 10 Core Rules Catalog (.agents/rules/)

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

---

## 📋 6. 7 Production Workflows (.agents/workflows/)

Synapse Hub equips agents with 7 standardized, slash-command-style workflows:

| Workflow | Core Engineering Purpose |
| :--- | :--- |
| **`generate_manual_testcases_rbt.md`** | Comprehensive 6-stage AI-RBT manual test generation with $P \times I$ risk scoring and 12-column table output. |
| **`generate_testcases_from_requirements.md`** | Direct compilation of requirement documents (SRS, PRD, User Stories) into acceptance test suites. |
| **`generate_cross_module_test_plan.md`** | E2E integration test planning across interconnected modules (Cart ➔ Checkout ➔ Payment ➔ Warehouse). |
| **`generate_combinatorial_test_data.md`** | All-Pairs / Pairwise test data generation optimizing boundary coverage with minimal test cases. |
| **`generate_requirements_from_website.md`** | Autonomous reverse-engineering of functional specs from live web pages via headless Playwright probing. |
| **`analyze_requirement_document.md`** | Static requirements linter surfacing logic contradictions, edge-case gaps, and ambiguity debt. |
| **`export_testcases_excel.md`** | Automated conversion of Markdown test cases into professionally styled Excel spreadsheets (.xlsx) via OpenPyXL. |

---

## 🧪 7. Golden Practices & Benchmark Corpus (examples/practices/)

Real-world domain specifications and benchmark test suites used for golden evaluations and offline few-shot learning:

- **`requirements/crm/`**: Modular CRM functional specs (Authentication, Customers, Projects, Contracts, Tasks).
- **`requirements/ecommerce/`**: E-Commerce Category and Brand management business rules.
- **`requirements/jira/`**: Jira Kanban Epic & Story export samples (`KAN-1` through `KAN-6`) with UI reference mocks.
- **`testcases/crm/` & `testcases/api/`**: Production-standard manual UI and REST API test suites (User & Book Management) in AI-RBT format.

---

## 🛠️ 8. Automated Tools Runbook (50+ Specialized Python Tools)

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

---

## 📚 9. Extended Technical Documentation & CLI Package (docs/)

1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Hub/Spoke architecture, 4-tier skill model, and 6-agent swarm coordination.
2. **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Contribution standards, new skill authoring principles, and verification pipelines.
3. **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)**: Comprehensive command-line reference for the `agent-qa` CLI.
4. **[docs/TOKEN_QUOTA_PLAYBOOK.md](docs/TOKEN_QUOTA_PLAYBOOK.md)**: Model tiering strategy (Claude Sonnet vs Gemini Pro vs Gemini Flash) and quota-conscious execution modes.

### Quick CLI Installation:
```bash
pip install -e .
agent-qa --help
agent-qa verify
agent-qa lint
agent-qa export-excel
agent-qa skillspector
```

---

## 🤝 10. Acknowledgments & Upstream Inspirations

**Synapse Hub** synthesizes, adapts, and builds upon groundbreaking methodologies and architectures from the global open-source and AI engineering community:

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

---

## 📄 11. License & Author Attribution

This project is licensed under the **[MIT License](LICENSE)**.

**Provenance & Copyright Notice:**
- **Author & Founder:** Thế Vị ([@TeeVee998](https://github.com/TeeVee998))
- **Original Repository:** [https://github.com/TeeVee998/Synapse-Hub](https://github.com/TeeVee998/Synapse-Hub)
- **Copyright:** Copyright (c) 2026 Thế Vị (@TeeVee998). Distributed under the MIT License.

> ⚖️ **MIT License Attribution Requirement:** Under the terms of the MIT License, you are granted permission to use, copy, modify, merge, publish, and distribute this software freely, **PROVIDED** that the original copyright notice crediting **Thế Vị (@TeeVee998)** and this permission notice are included in all copies or substantial portions of the Software.


