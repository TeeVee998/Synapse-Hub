# Contributing to Agent-Skills Hub

We welcome contributions to expand and refine skills, tools, and rules in the `agent-skills` ecosystem. All contributions must adhere to the **Truth Anchor** and **Token-Efficiency** standards.

---

## 1. Skill Authoring Standards

Every skill resides in `.agents/skills/<skill-name>/` and must satisfy:

1. **`SKILL.md` Structure:**
   - Must contain valid YAML frontmatter with `name` and `description`.
   - `name` must exactly match the directory name in kebab-case.
   - `description` must clearly articulate the triggering scope and disambiguate itself from adjacent skills.
2. **Conciseness & Token Budget:**
   - Write instructions in technical English to minimize token consumption.
   - Use progressive disclosure: keep `SKILL.md` between 40 and 150 lines, and offload deep code patterns to `references/` or `examples/`.
3. **No Project Coupling:**
   - Never hardcode specific project names, proprietary URLs, test credentials, or internal namespaces.
   - Always use generic placeholders: `<project_namespace>`, `https://app.example.com`, `APP_PASSWORD`.

---

## 2. Integrity Verification Workflow

Before submitting a pull request or committing changes:

```powershell
# 1. Verify markdown metadata & frontmatter across all 27 skills
powershell -ExecutionPolicy Bypass -File scripts/lint_skills.ps1

# 2. Run automated test suite for Python engine tools
python -m unittest discover -s tests -p "test_*.py"

# 3. Verify all 9 Quality Gates
python tools/verify_all.py
```

---

## 3. Tool Development Guidelines

All helper scripts in `tools/` must:
1. **Rely on Standard Libraries:** Minimize third-party package dependencies so tools execute seamlessly across clean host machines and CI pipelines.
2. **Be Fast & Non-Blocking:** AST scans and regex lookups must complete in under 500ms.
3. **Handle Errors Gracefully:** Provide clear remedies and pointers rather than dumping raw stack traces.
