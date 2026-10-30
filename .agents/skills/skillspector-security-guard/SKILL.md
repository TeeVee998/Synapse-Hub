---
name: skillspector-security-guard
description: "Audit and verify AI agent skills, prompts, and MCP configurations against vulnerability vectors inspired by NVIDIA SkillSpector."
---

# SkillSpector Security Guard — AI Agent & MCP Security Sentinel

> **Purpose:** Autonomous security vetting for AI Agent skills, prompt instructions, Model Context Protocol (MCP) servers, and automation tools.  
> **Heritage:** Inspired by and adapted from **[NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector)** (Apache 2.0).

---

## 1. Core Threat Vectors

AI agent skills execute with terminal and workspace permissions. Unvetted third-party skills can introduce severe risks:
- **Prompt Injection:** Overriding core safety instructions or forcing jailbreaks.
- **Data Exfiltration:** Covertly exfiltrating conversation memory, environment keys, or tokens to external endpoints.
- **Privilege Escalation:** Running unauthorized `sudo`/root commands or accessing sensitive credentials (`.ssh`, `.aws`).
- **Agent Snooping:** Accessing IDE authentication configs (`~/.gemini`, `~/.claude`) or parsing `mcp.json`.
- **Tool Poisoning:** Injecting obfuscated Unicode homoglyphs, Base64 payloads, or hidden comments into tool schemas.

---

## 2. Threat Vector Categories

| Category | Description | Severity |
| :--- | :--- | :--- |
| **Prompt Injection** | Instruction overrides, zero-width steganography, bidi Trojan Source, exfiltration directives. | **CRITICAL** |
| **Data Exfiltration** | Outbound HTTP POST sinks (`curl`, `fetch`), harvesting `os.environ`, scanning credentials. | **CRITICAL** |
| **Privilege Escalation** | Wildcard permissions (`*`), `sudo`/`su`, `/etc/shadow`, Docker socket access. | **CRITICAL** |
| **Agent Snooping** | Reading agent auth configs (`.gemini/`, `.claude/`), extracting `mcp.json` tokens. | **CRITICAL** |
| **Behavioral AST** | Dynamic `exec()`, `eval()`, `__import__()`, `subprocess(shell=True)`, `os.system()`, insecure deserialization (`pickle`). | **CRITICAL / HIGH** |
| **Supply Chain & SSRF** | `curl \| bash` downloads, cloud instance metadata probing (`169.254.169.254`). | **CRITICAL** |

---

## 3. Defense Guard & Prohibition Context

To prevent false alarms in educational documentation (e.g. *"Never run sudo"*):
1. **Negative Imperatives:** Matches preceded by negations (`never`, `do not`, `avoid`, `forbidden`) are recognized as defensive rules.
2. **Defensive Callouts:** Patterns appearing inside `> [!WARNING]` or `> [!CAUTION]` blocks are evaluated with contextual negative verbs.
3. **Emoji ZWJ Handling:** Legitimate Zero-Width Joiner sequences are preserved while hidden steganographic bytes are flagged.

---

## 4. CLI Audit Commands

```bash
# Scan a specific candidate skill or file
synapse skillspector path/to/SKILL.md

# Scan entire skills directory
synapse skillspector --scan-skills

# Fail CI pipeline if high or critical risks are detected
synapse skillspector --scan-skills --strict
```
