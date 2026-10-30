# GitHub Copilot Instructions — Synapse-Hub Enterprise QA

When assisting in this repository, you must adhere strictly to the enterprise testing standards governed by Synapse-Hub:

## 1. Clean Page Object Model (POM)
- Keep all test scripts (`tests/`, `Scripts/`) decoupled from UI implementation details.
- Never write raw XPaths, CSS selectors, or direct DOM queries in test scripts.
- Encapsulate all element locators and page actions within Page Classes extending `BasePage`.

## 2. Truth Anchor (Zero Fake Passes)
- Every test must contain robust, non-trivial assertions that verify actual system state or business outputs.
- Never write tests without assertions or catch-all exception swallowers that mask failures.
- If an application defect is uncovered, report it cleanly; do not modify expected values to force a pass.

## 3. Dynamic & Idempotent Test Data
- Generate unique identifiers dynamically (e.g. `AUTO_` + timestamp) for all entities created during tests.
- Always include automated cleanup/teardown logic to prevent test environment pollution.

## 4. Smart Synchronization
- Never suggest or write static sleep calls (`Thread.sleep`, `time.sleep`).
- Always use explicit/dynamic waits (visibility, DOM stability, network idle).

## 5. Verification Gate
- When tests or page objects are added or modified, verify adherence by running `npx synapse-hub verify`.
- Consult `PROJECT_AI_GUIDE.md` for project-specific setup and architecture patterns.
