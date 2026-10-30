---
name: clean-pom-crafter
description: "Build and refactor Clean POM Page Classes adhering to Flat Architecture standards."
---

# Clean POM Crafter — Enterprise Clean POM Architecture Standards

Specialized skill for creating, refactoring, and standardizing test automation scripts using **Clean Page Object Model (POM)** and **Flat Architecture** across enterprise test suites.

---

## 1. Core Architectural Principles

1. **Flat Architecture:**
   - All `Test Cases/`, `Scripts/`, and `Test Suites/` reside directly in their parent directory (no module subfolders).
   - Naming convention: `TC-<Number>_<FeatureName>`, e.g. `TC-101_CreateUserAccount.groovy` or `tc-101-create-user.spec.ts`.
2. **Unified Inheritance from `BasePage`:**
   - All Page Classes in `Keywords/<project_namespace>/pages/` (or `pages/*.ts` in Playwright/TS) inherit from `BasePage`.
3. **Zero Raw XPaths in Test Scripts:**
   - Scripts (`Scripts/TC-xxx_*.groovy` or `tests/*.spec.ts`) only orchestrate business workflows. All locators and UI interactions are encapsulated in Page Classes.
4. **Mandatory 100% UTF-8 No BOM:**
   - All `.groovy`, `.java`, `.ts`, `.tc` files must NEVER contain UTF-8 BOM bytes (`0xEF, 0xBB, 0xBF`).
5. **Context Window Protection (Zero-Token Economy):**
   - 🚫 **NEVER read entire monolithic Page Class files (> 100KB) into LLM context.**
   - Always use `python3 tools/lookup_xpath.py <keyword>` or line-range targeted reads (`read_file` with `StartLine`/`EndLine`) to find selectors and methods on demand.

---

## 2. Master Locator Priority Map (6 Tiers)

All Page Classes **MUST** follow this strict locator hierarchy:
1. **Tier 1 — Angular Semantic / ARIA:** `[formcontrolname="..."]`, `[aria-label="..."]`, `[role="..."]`.
2. **Tier 2 — Dedicated Test Attributes:** `[data-testid="..."]`, `[data-test="..."]`.
3. **Tier 3 — HTML Identifier:** `id`, `name`.
4. **Tier 4 — PrimeNG Business Attributes:** `p-dropdown[formcontrolname="..."]`, `button[icon*="pencil"]`.
5. **Tier 5 — Resilient CSS Selectors:** `.card.popup-data input.p-inputtext`.
6. **Tier 6 — Relative XPath (Last Resort):** `//div[contains(@class, 'card')]//button[contains(., 'Confirm')]`.

> 🚫 **FORBIDDEN:** Absolute positional XPaths (`//tbody/tr[1]/td[6]/button[2]`) and dynamic hash classes (`.p-element-1n2xyz`).

---

## 3. Test Data Management & Cross-Module Data Chain

- **Supporting Field:** Generate dynamically using `BasePage.uniqueCode(prefix)` (e.g. `BasePage.uniqueCode("AUTO_")`).
- **Dimension Field:** Fixed category values selected from dropdowns (`"Active"`, `"Standard"`).
- **Reference Field:** Pass output records from prior TCs into subsequent TCs (Create -> Edit -> Delete).
- **Computed Field:** Auto-calculated system metrics; assert 100% exact match.

---

## 4. Universal Page Object Architecture Model

| No. | Page Class Role | Functional Module | Typical Test Scope | Core Methods & Responsibilities |
|:---:|---|---|:---:|---|
| 1 | `BasePage` | Core Engine, Driver, JS Helpers, Smart Wait | Global | `openUrl()`, `smartWait()`, `clickSafe()`, `uniqueCode()` |
| 2 | `LoginPage` | Authentication & User Profile | Auth & Session | `login()`, `logout()`, `verifyUserProfile()` |
| 3 | `UserAdminPage` | System Administration & Users | Admin / RBAC | `createUser()`, `assignRole()`, `filterUsers()` |
| 4 | `CommonCategoryPage` | Common Categories & System Catalogs | Catalogs & Lookups | `addCategory()`, `editCategory()`, `verifyCatalog()` |
| 5 | `WorkflowPlanningPage`| Sector Planning & Approvals | Workflows & Approvals | `createPlan()`, `submitForReview()`, `approvePlan()` |
| 6 | `DataManagementPage` | Enterprise CRUD & Search Tables | Master Data | `searchRecord()`, `editRecord()`, `deleteRecord()` |
| 7 | `ReportAnalyticsPage` | Statistical Reporting & Dashboards | Reporting | `generateReport()`, `exportExcel()`, `verifyKPI()` |
| 8 | `ApiTokenMgmtPage` | Data Sharing & API Tokens | API & Integration | `generateToken()`, `revokeToken()`, `verifyScopes()` |

---

## 5. Implementation References & Examples

- [**Standard Clean POM Methods (`pom_patterns.groovy`)**](references/pom_patterns.groovy): Full implementation of `searchRecord`, `editRecord`, `deleteRecord`, `setCalendarDate`, `selectMultiOptions`, `verifyRecordExists`, `verifyRecordNotExists`, `jsSetInput`.
- [**Standard Test Script Template (`standard_test_case.groovy`)**](examples/standard_test_case.groovy): 7-step complete script template from Login -> Create -> Search -> Edit -> Delete.
- [**Zero-Token XPath Lookup (`tools/lookup_xpath.py`)**](tools/lookup_xpath.py): Command `python3 tools/lookup_xpath.py <PageClass>` returns exact locators in <200 tokens without parsing full files.
- [**Browser Runtime Helper (`tools/browser_helpers.js`)**](tools/browser_helpers.js): In-browser validation engine for form audits, safe clicks, and batch verification.
