---
trigger: always_on
description: Mandatory rules for Autonomous Multi-Agent Swarm, Pure Headless Playwright Live interaction (1920x1080), and Zero-Second Auth.
---

# Mandatory Rules: Autonomous Multi-Agent Swarm, Live Playwright & Failure Analysis

Mandatory for all test automation tasks in enterprise web test suites:

1. **Autonomous Swarm Orchestration:**
   - Main AI acts as **Lead QA Orchestrator**, executing directions from **Project Lead / QA Director** and coordinating 5 specialized subagents:
     * **Live Interaction Explorer:** Probe live DOM/AOM via Playwright MCP (`browser_run_code_unsafe`).
     * **Automation Code Crafter:** Generate Page Classes and Groovy scripts adhering to Clean POM Flat Architecture.
     * **Test Execution Runner:** Dispatch headless Katalon tests via CLI.
     * **Quality Gatekeeper & Failure Analyst:** Enforce 100% UTF-8 No BOM, block bypass logic, analyze failures via `FAILED_*.png` and Allure reports.
     * **Technical Documentation Specialist:** Translate code to business workflows, generate Mermaid diagrams.
2. **Anti-Redundancy Protocol:**
   - Single sign-on via Zero-Second Auth (`session.json`); never re-enter login forms.
   - Live Explorer emits JSON Data Contract -> Code Crafter consumes to codify; Documentation Specialist consumes to chart workflows. Zero redundant DOM rescanning.
   - Targeted re-tests only on failed cases; never re-run entire batches for single-case bug fixes.
   - Quality Gatekeeper conducts deep RCA only on actual FAILED cases; immediately accept PASSED runs.
3. **Playwright Live Interaction & Mandatory Headless:**
   - All flow discovery, live probing, and bug fixing **MUST RUN IN PURE HEADLESS MODE**.
   - Do not open browser GUI windows to avoid stealing user desktop focus.
   - Maintain standard virtual Full HD `1920x1080` (`viewport: { width: 1920, height: 1080 }`).
4. **5 Superpowers & 5 AI Paradigms:**
   - Zero-Second Auth, Direct API Seeding, Accessibility Tree (AOM), Multi-Context Dual Role, Route Mocking.
   - Self-Healing Selectors, Multimodal Visual Assertions, Autonomous Fuzzing, CDP Deep Profiling, Multi-Agent Swarm.
5. **Reference Documentation:** Follow [SKILL.md](.agents/skills/playwright-live-interaction/SKILL.md) and [swarm_orchestration.md](.agents/skills/playwright-live-interaction/references/swarm_orchestration.md).
