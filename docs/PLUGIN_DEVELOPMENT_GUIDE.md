# 3rd-Party Plugin Development Guide — Synapse Hub

> **Specification Version:** 2.2.4  
> **Hub Core Provenance:** Thế Vị (@TeeVee998) — [Synapse Hub](https://github.com/TeeVee998/Synapse-Hub)  

---

## 1. Overview

Synapse Hub provides a decoupled, modular architecture enabling 3rd-party teams and community contributors to extend the Hub with specialized QA skills, runner adapters, or domain-specific security linters.

Every 3rd-party plugin is an independent package registered via `plugin.json` and vetted by the built-in **SkillSpector Security Sentinel** (`tools/skillspector.py`).

---

## 2. Plugin Structure & File Conventions

A standard Synapse Hub plugin adheres to the following directory layout:

```text
my-custom-plugin/
├── plugin.json                    # Mandatory plugin manifest
├── README.md                      # Plugin documentation & quickstart
├── skills/                        # Packaged AI skills (one folder per skill)
│   └── custom-security-audit/
│       ├── SKILL.md               # Standardized YAML frontmatter + prompt
│       └── examples/
│           └── audit_sample.json  # Demonstrable example fixture
└── tools/                         # Executable CLI tools (Python 3.9+)
    └── custom_auditor.py          # Deterministic, standalone tool
```

---

## 3. Plugin Manifest Specification (`plugin.json`)

The root `plugin.json` declares identity, capabilities, and dependencies:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "name": "sample-custom-plugin",
  "version": "1.0.0",
  "description": "3rd-party plugin extending Synapse Hub with custom HTTP security header auditing.",
  "author": "Community Contributor",
  "license": "MIT",
  "repository": "https://github.com/example/sample-custom-plugin",
  "skills": [
    "custom-security-headers-audit"
  ],
  "tools": [
    "tools/custom_security_headers.py"
  ],
  "minHubVersion": "2.2.0"
}
```

### Manifest Fields:
- `name` *(string, required)*: Unique kebab-case identifier.
- `version` *(string, required)*: Semantic versioning (`x.y.z`).
- `description` *(string, required)*: Concise summary of provided capabilities.
- `skills` *(array of strings)*: List of skill folder names inside `skills/`.
- `tools` *(array of strings)*: Relative file paths to executable scripts in `tools/`.
- `minHubVersion` *(string)*: Minimum compatible Synapse Hub core version.

---

## 4. Skill Authoring Standard (`SKILL.md`)

Each skill must contain valid YAML frontmatter followed by clear, token-optimized instructions:

```markdown
---
name: custom-security-headers-audit
description: Audits web applications for missing or misconfigured HTTP security headers (CSP, HSTS, X-Frame-Options).
version: 1.0.0
category: security_and_compliance
---

# Custom Security Headers Audit Skill

## Purpose
Inspects target endpoint response headers and reports compliance against OWASP ASVS Section 14.

## Quick CLI Execution
```bash
python tools/custom_security_headers.py https://staging.example.com --json report.json
```
```

### Skill Invariants:
1. **Token Ceiling:** Every `SKILL.md` must be $\le 1.500$ tokens (enforced by `scripts/lint_skills.ps1`).
2. **100% UTF-8 No BOM:** Zero BOM bytes (`0xEF, 0xBB, 0xBF`).
3. **Evidence-First:** Must reference deterministic tools rather than guessing.

---

## 5. Security & Safety Invariants (DoD Compliance)

All 3rd-party tools and scripts must adhere to Synapse Hub's safety rules:

1. **Zero `shell=True` Policy:** Never invoke `subprocess.Popen` or `subprocess.run` with `shell=True`. Always pass structured lists:
   ```python
   # Correct:
   subprocess.run(["curl", "-I", url], capture_output=True, check=True)
   # FORBIDDEN (will be rejected by Gatekeeper):
   subprocess.run(f"curl -I {url}", shell=True)
   ```
2. **Environment Allowlist Guard:** Any tool performing destructive modifications or fuzzing must verify staging allowlists (`SYNAPSE_ALLOW_PROD_FUZZ=1`).
3. **No Hardcoded Credentials:** Never store plaintext secrets or passwords.

---

## 6. Vetting & Verification Pipeline

Before distributing or publishing a plugin, run the Hub's verification sentinels:

```bash
# 1. Run SkillSpector Security Scan (Must report 0 High/Critical warnings)
python tools/skillspector.py --target path/to/my-custom-plugin

# 2. Run Quality Gates Linting
python tools/verify_all.py --target path/to/my-custom-plugin
```

Once passed, the plugin can be mounted directly into the Antigravity Plugin directory (`~/.gemini/config/plugins/`) or integrated via `skills_manifest.json`.
