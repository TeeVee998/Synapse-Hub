---
trigger: always_on
description: Skill Resolution Precedence and Anti-Collision Protocol enforcing Workspace-Local skills over external generic plugin skills.
---

# Skill Resolution Precedence & Anti-Collision Protocol

> **Purpose:** Resolve overlapping trigger scopes between Project-Local Skills and External Plugins, eliminating context contagion, token bloat, and conflicting instructions.

---

## 1. Non-Negotiable Precedence Order

When executing tasks within automated testing repositories, Agent must strictly apply the following resolution order:

```text
[Tier 1: Project-Local Skills] (.agent/skills/*) 
       v (Higher priority - Specialized & Context-Aware)
[Tier 2: Core Project Rules] (.agents/rules/*)
       v
[Tier 3: External Plugin Skills] (antigravity-testing-kit, chrome-devtools-plugin)
```

---

## 2. Specific Skill Mapping & Exclusion Matrix

| Task Type | REQUIRED Skill (Tier 1) | EXCLUDED / SUPPRESSED Skill (Tier 3) | Reason |
|---|---|---|---|
| **Test Script & POM Generation** | `clean-pom-crafter`<br/>`lam-script-generator` | `QA Automation Engineer` | Enforces Flat Architecture, zero XPaths in scripts, dynamic `uniqueCode`, and 2-phase search. Generic plugin templates violate Clean POM standards. |
| **Locator Healing & DOM Diffing** | `self-healing-locator`<br/>`failure-autopsy-and-healing` | `Locator Healer Agent` | Uses token-efficient AOM diffing (Role > Label > TestId) and reads local JUnit XML/Screenshots. |
| **Flaky Test Triage & Root Cause** | `failure-autopsy-and-healing` | `Flaky Test Analyzer` | Triage occurs via 0-token JUnit XML parsing, `Screenshots/FAILED_*.png` autopsy, and SQLite cosine cache (`memory_cache.db`). |
| **Live Web & Locator Probing** | `playwright-live-interaction` | `Smart Locator Agent` | Direct CDP network idle 0, dynamic overlay bypass, and in-browser helper integration. |
| **Code Refactoring & Tech Debt** | `code-refactoring-refactor-clean` | *(Consolidated)* | Single unified skill covering SOLID refactoring, code smells, and technical debt remediation. |
| **Accessibility (A11y) Testing** | `wcag-audit-patterns`<br/>*(Guideline)* | `a11y-debugging`<br/>*(Tooling Only)* | `wcag-audit-patterns` governs WCAG 2.2 rules; `a11y-debugging` is used solely for low-level Chrome DevTools inspection. |

---

## 3. Strict Prohibitions

1. **Never use generic test generation:** Do not generate boilerplate Selenium/Cucumber tests from external plugins that use `findTestObject` or Object Repository folders.
2. **Never dump raw HTML for locator healing:** Always extract compact AOM subtrees (< 500 tokens).
