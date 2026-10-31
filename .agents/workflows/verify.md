---
name: verify
description: Execute 9 Quality Gates to verify complete codebase integrity and enforce deterministic safety boundaries before handoff.
trigger: /verify
---

# Workflow: verify

## 1. Pre-execution Safety Hook (Mandatory Action Firewall)
Before dispatching any UI interaction (`click`, `fill`, `submit`, `drop`) down to a live Playwright or CDP browser context, the command or code must be piped through `tools/safety_firewall.py --dry-run`:

```bash
# Verify single action safety clearance
python tools/safety_firewall.py --action click --selector "<selector>" --text "<text>" --dry-run

# Or pipe code snippet directly
python tools/safety_firewall.py --code "page.click('<selector>')" --dry-run
```
*If safety firewall reports BLOCKED, execution halts immediately unless explicitly forced via `--force` or `ALLOW_DESTRUCTIVE=1`.*

---

## 2. Hard Quality Gates Verification (8 DoD Gates)
Execute all 9 Quality Gates (Author Attribution, UTF-8 No BOM, Path Portability, Clean POM, AI Docs Linter, Cleanup Blacklist, Credential Security, Infer Linter, and AST Micro-Mutation Testing):

```bash
python tools/verify_all.py
```

### Gate 8 Hard Rejection Rule:
- Any new or updated test case must achieve an AST Mutation Score of **$\ge 80\%$** via `tools/micro_mutator.py`.
- If `mutation_score < 80%`, the Gatekeeper strictly rejects the test suite (anti-tautology and anti-fake-pass policy).

If any gate returns `FAIL`, pause execution and resolve defects completely before proceeding.
