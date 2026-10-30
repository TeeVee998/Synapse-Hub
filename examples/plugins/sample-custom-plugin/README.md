# Sample Custom 3rd-Party Plugin for Synapse Hub

This is a reference implementation of a 3rd-party extension plugin for Synapse Hub.

## Included Components
- **Plugin Manifest:** `plugin.json` declaring metadata and dependencies.
- **Skill:** `skills/custom-security-headers-audit/SKILL.md` (OWASP ASVS HTTP Security Headers).
- **Tool:** `tools/custom_security_headers.py` (Autonomous header compliance auditor).
- **Example Fixture:** `skills/custom-security-headers-audit/examples/audit_fixture.json`.

## Quick Test
```bash
python tools/custom_security_headers.py --headers skills/custom-security-headers-audit/examples/audit_fixture.json --report report.json
```
