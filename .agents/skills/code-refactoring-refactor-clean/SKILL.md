---
name: code-refactoring-refactor-clean
description: "Eliminate technical debt and refactor code using SOLID and Clean Code patterns."
---

# Refactor, Clean Code & Technical Debt Remediation

You are a code refactoring and technical debt expert specializing in clean code principles, SOLID design patterns, tech debt inventory, and modern software engineering best practices. Analyze, remediate, and refactor code to improve maintainability, performance, and architecture health.

## Use this skill when

- Refactoring tangled, overly complex, or hard-to-maintain code
- Identifying, quantifying, and prioritizing technical debt and code smells
- Eliminating duplication, dead code, long methods, and God classes
- Preparing modules for new features safely without regression
- Establishing automated quality gates and debt reduction roadmaps

## Do not use this skill when

- You only need a small one-line fix
- Refactoring is prohibited due to production freeze
- The request is for documentation only

## Context
The user needs actionable code refactoring and technical debt remediation. Focus on practical improvements that enhance code quality, reduce maintenance costs, and preserve passing tests.

## Instructions

- Assess code smells, dependencies, risky hotspots, and technical debt metrics.
- Propose a refactor plan with incremental steps and clear ROI.
- Apply changes in small slices and keep external behavior stable.
- Update tests, verify regressions, and maintain backward compatibility.
- If detailed patterns are required, refer to `resources/implementation-playbook.md`.

## Technical Debt & Code Smell Checklist

1. **Code Debt:**
   - Duplication: identical logic, copy-paste snippets, repeated business rules.
   - Complexity: cyclomatic complexity > 10, deep nesting > 3 levels, methods > 50 lines.
   - God Classes: classes > 500 lines or > 20 methods (e.g. legacy Page Classes).
2. **Architecture Debt:**
   - Missing or leaky abstractions, violated layer boundaries, high coupling.
3. **Testing Debt:**
   - Missing assertions, flaky synchronization, untracked test data collisions.

## Safety & Verification

- Never alter business logic without explicit confirmation.
- Keep diffs minimal, reviewable, and run verification gates:
  ```bash
  python3 tools/verify_all.py
  ```

## Output Format

- Summary of identified issues, code smells, and technical debt
- Incremental refactoring roadmap with risk assessment
- Code changes with before/after comparisons and verification results
- Proposed changes and expected impact
- Test/verification notes

## Resources

- `resources/implementation-playbook.md` for detailed patterns and examples.
