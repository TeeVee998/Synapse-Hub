---
description: Reverse-engineer structured functional requirements and user story specifications by inspecting a live web application using headless Playwright.
skills:
  - playwright-live-interaction
  - clean-pom-crafter
---

# /generate_requirements_from_website — Live Web Reverse-Engineering

Reverse-engineers functional requirements, acceptance criteria, and input field rules directly from a deployed web application when written specifications are missing or outdated.

---

## Execution Pipeline

1. **Target Navigation:** Launch headless Playwright session at 1920x1080 and navigate to the target URL.
2. **Compact AOM Survey:** Extract the interactive Accessibility Tree (`qa.getCompactAOM()`) to discover forms, controls, roles, and validation messages.
3. **Behavioral Probing:**
   - Probe required fields by triggering empty form submissions.
   - Inspect client-side HTML5 validation attributes (`pattern`, `min`, `max`, `maxlength`, `required`).
   - Identify active dropdown choices and conditional UI toggles.
4. **Structured Requirements Document:** Output a structured Markdown specification with:
   - Feature summary and business objective.
   - User Stories with Gherkin Acceptance Criteria (`Given-When-Then`).
   - Field Specification Table: Name, Type, Required, Format Rules, Min/Max Limits, Error Messages.
