# PROJECT AI GUIDE TEMPLATE: [TARGET_PROJECT_NAME] (`PROJECT_AI_GUIDE.md`)

> **Purpose:** This file provides project-specific business context, technology stack definitions, and execution commands to AI Agents (Antigravity / Cursor / Claude Code).
> AI Agents combine universal skills from the `agent-skills` hub with the project context declared below.

---

## 1. General System Under Test (SUT) Information
- **Project / Module Name:** `[e.g., Enterprise Billing Platform / Customer Portal]`
- **Environments:**
  - Test / Dev URL: `https://test.example.com`
  - Staging / UAT URL: `https://staging.example.com`
- **Frontend Framework:** `[e.g., React 18, Angular 17 + PrimeNG, Vue 3, Next.js]`
- **Testing Framework:** `[e.g., Playwright Test, Katalon Studio 10.x, Cypress, Selenium]`
- **Script Language:** `[e.g., TypeScript, Groovy, Python, JavaScript]`

---

## 2. Test Accounts & Authentication Credentials
- **Admin Account:** `ADMIN_USER` / `ADMIN_PASS` (Sourced via environment variables)
- **Standard User Account:** `USER_NAME` / `USER_PASS`
- **Auth Mechanism:** `[e.g., JWT Bearer Token, Cookie StorageState, OAuth2 / OIDC, SSO]`
- **Zero-Second Auth Storage State Path:** `.auth/user_state.json`

---

## 3. Repository Architecture & Directory Mapping
- **Page Objects / Page Classes:** `src/pages/...` or `Keywords/pages/...`
- **Test Scripts / Specs:** `tests/e2e/...` or `Scripts/...`
- **Test Suites / Collections:** `tests/suites/...` or `Test Suites/...`
- **Fixtures & Mock Payloads:** `tests/fixtures/...` or `Data Files/...`
- **Environment Configuration:** `.env` or `Profiles/default.glbl`

---

## 4. Engineering Standards & Quality Gates
1. **Clean POM Architecture:** 100% of locators, selectors, and assertions encapsulated within Page Classes inheriting from `BasePage`. Zero raw selectors in test scripts.
2. **Dynamic Test Data:** Always use randomized identifiers with execution timestamp prefixes (`uniqueCode("AUTO_")`) to eliminate DB unique key collisions.
3. **Encoding Discipline:** 100% `UTF-8 No BOM` across all code, script, and documentation files.
4. **Smart Wait & Synchronization:** Pure event-driven waiting (`waitForLoadState('networkidle')`, Angular `zone.isStable()`). Static sleeps (`Thread.sleep`, `waitForTimeout`) are strictly forbidden.
5. **Idempotent Teardown:** Every data creation test case must be paired with automated deletion cleanup in its teardown phase.

---

## 5. Standard CLI Execution Commands
- **Run Headless E2E Suite:**
  ```bash
  [e.g., npx playwright test --project=chromium --reporter=html,junit:results.xml]
  ```
- **Run Targeted Test Case:**
  ```bash
  [e.g., npx playwright test tests/e2e/login.spec.ts]
  ```
- **Execute 7 Quality Gates Verification:**
  ```bash
  python tools/verify_all.py
  ```

---

## 6. Git Push & SCM Workflow
- **Clean SCM by Architecture:** Because `agent-skills` is a separate external repository, this target project stays 100% clean of AI skills, rules, and prompts. No dual-remote or smart push script is needed.
- **Push Command:** Commit verified code and push directly to this project's remote branch:
  ```bash
  git add <project-files>
  git commit -m "feat(module): add verified test scenario"
  git push origin <current-branch>
  ```
- **Privacy Mode:** If enterprise policy restricts AI markdown files in the repository, add `PROJECT_AI_GUIDE.md` to `.gitignore`.

---

## 7. Fast Index & Reference Data Configuration (`lookup_tc` & `lookup_xpath`)

To enable instant (<300 tokens) lookups for Test Cases and DOM Locators without cluttering LLM context:
- **Test Case Metadata File:**
  - Standard path: `testcases.json` (or `references/testcases.json`)
  - Environment variable: `TC_DATA_FILE="references/testcases.json"` in `.env`
  - Lookup command: `python ../agent-skills/tools/lookup_tc.py <TC-ID> --file references/testcases.json`
- **Scraped Selectors & XPath File:**
  - Standard path: `selectors.json` (or `references/selectors.json`)
  - Environment variable: `XPATH_DATA_FILE="references/selectors.json"` in `.env`
  - Lookup command: `python ../agent-skills/tools/lookup_xpath.py <PageClass> --file references/selectors.json`

---

## 8. First-Time SQLite Memory Cache Bootstrap (CI / Docker / Fresh Clone)

The Central Agent Memory (`~/.agent_memory/global_cache.db`) stores positive healing patches and negative anti-patterns.
- **In fresh environments (CI runner, Docker container, new developer machine):**
  Initialize and seed the database with baseline solutions:
  ```bash
  agent-qa heal init
  # or directly via python:
  python ../agent-skills/tools/cache_resolver.py init
  ```
- **Automatic bootstrap:** Running `./scripts/install.ps1` (Windows) or `./scripts/setup.sh` (Linux/macOS) in `agent-skills` performs this initialization automatically.
