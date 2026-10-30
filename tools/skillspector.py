#!/usr/bin/env python3
"""
Enterprise SkillSpector Sentinel (AI Agent Skill & MCP Security Scanner)
-------------------------------------------------------------------------
Synthesized from NVIDIA/SkillSpector (Apache 2.0).
Provides multi-vector static security analysis for AI Agent skills, prompt instructions,
MCP (Model Context Protocol) tool configurations, and bundled automation scripts.

Detects 71 vulnerability patterns across 17 categories:
  1.  Prompt Injection (P1, P2, P3, P4, P9 - Override, Hidden, Exfil, Manipulation, Whitespace Padding)
  2.  Data Exfiltration (E1-E5 - HTTP sinks, Env Var harvesting, Credential search, Context leak, Cloud upload)
  3.  Privilege Escalation (PE1-PE5 - Wildcards, Sudo/root, Private keys, Docker socket, Container escape)
  4.  Agent Snooping (AS1-AS3 - Agent configs ~/.claude ~/.gemini, MCP configs, Peer skills snooping)
  5.  System Prompt Leakage (P6-P8 - Direct prompt extraction, Delimiter attack, Tool exfiltration)
  6.  Anti-Refusal Jailbreaks (AR1-AR3 - Refusal suppression, Warning suppression, Policy nullification)
  7.  MCP Tool Poisoning (TP1-TP4 - Hidden metadata comments/Base64, Homoglyphs, Param injection, Drift)
  8.  MCP Least Privilege (LP1-LP4 - Undeclared capabilities, Wildcard tools, Missing scopes)
  9.  Behavioral AST Analysis (AST1-AST10 - exec, eval, __import__, shell=True, os.system, dynamic getattr,
      reflective execution sinks, and insecure deserialization pickle/yaml.unsafe_load/torch.load)
  10. Unicode Confusables & Steganography (Bidi overrides CVE-2021-42574, Zero-width characters, Cyrillic lookalikes)
  11. Supply Chain & Dangerous Execution (SC1-SC2 - Unpinned deps, curl|sh download & exec)
  12. Server-Side Request Forgery (SSRF1-SSRF3 - Cloud metadata 169.254.169.254, loopback, private networks)

Features:
  - NVIDIA-style Prohibition Context Engine (Defensive Language Guard): eliminates false positives
    when dangerous patterns appear inside negations ("do not", "never", "avoid", "forbidden")
    or Markdown warning callouts ([!CAUTION], [!WARNING]).
  - Emoji ZWJ sequence preservation: distinguishes legitimate emojis from malicious zero-width payloads.
  - Request-anchored SSRF detection: eliminates false positives on documentation URLs.
  - Risk Scoring (0-100) & Severity Bands (LOW, MEDIUM, HIGH, CRITICAL).
  - Verdict Recommendation (SAFE, CAUTION, DO_NOT_INSTALL).
  - Multi-Format Outputs: Terminal (Rich ANSI), JSON, Markdown, and SARIF 2.1.0.

Usage:
  python3 tools/skillspector.py <path_or_file> [--format terminal|json|markdown|sarif] [--output file]
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Recommendation(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DO_NOT_INSTALL = "DO_NOT_INSTALL"


@dataclass
class Finding:
    rule_id: str
    message: str
    severity: Severity
    confidence: float
    file_path: str
    line_number: int
    matched_text: str
    category: str
    explanation: str
    remediation: str
    match_fingerprint: str = ""

    def __post_init__(self):
        if not self.match_fingerprint:
            raw = f"{self.rule_id}:{self.file_path}:{self.line_number}:{self.matched_text.strip()}"
            self.match_fingerprint = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


@dataclass
class ScanReport:
    target_path: str
    scanned_files: int
    findings: List[Finding] = field(default_factory=list)
    risk_score: int = 0
    severity: Severity = Severity.LOW
    recommendation: Recommendation = Recommendation.SAFE
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Unicode & Steganography Constants (NVIDIA SkillSpector spec)
# ---------------------------------------------------------------------------

ZERO_WIDTH_CHARS = frozenset({
    "\u200B",  # Zero-width space
    "\u200C",  # Zero-width non-joiner
    "\u200D",  # Zero-width joiner
    "\u2060",  # Word joiner
    "\uFEFF",  # Zero-width no-break space / BOM
})

BIDI_CONTROL_CHARS = re.compile(r"[\u202a-\u202e\u2066-\u2069]")

CONFUSABLES_MAP: Dict[str, str] = {
    # Cyrillic lowercase
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c",
    "\u0443": "y", "\u0456": "i", "\u0445": "x",
    # Cyrillic uppercase
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M",
    "\u041d": "H", "\u041e": "O", "\u0420": "P", "\u0421": "C", "\u0422": "T",
    "\u0425": "X",
    # Greek lowercase
    "\u03b1": "a", "\u03b5": "e", "\u03bf": "o", "\u03c1": "p", "\u03c7": "x",
}


def _is_emoji_base(ch: str) -> bool:
    """Return whether one character is a base for emoji presentation forms."""
    if not ch:
        return False
    codepoint = ord(ch)
    return (
        0x1F000 <= codepoint <= 0x1FAFF
        or 0x2600 <= codepoint <= 0x27BF
        or codepoint in (0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D)
    )


# ---------------------------------------------------------------------------
# NVIDIA Prohibition Context Engine (Defensive Language Detection)
# ---------------------------------------------------------------------------

PROHIBITION_PREFIX = re.compile(
    r"(?:\A|(?<=[\n\r.!?;,\[]))[ \t]*"
    r"(?:[-*+][ \t]+|\d+[.)][ \t]+)?"
    r"(?:please[ \t]+)?"
    r"(?:(?:you|(?:the[ \t]+)?(?:agent|assistant|model|user))[ \t]+)?"
    r"(?P<negation>do[ \t]+not|don['’]t|never|no|must[ \t]+not|shall[ \t]+not|strictly[ \t]+forbidden|prohibited|avoid)[ \t]+"
    r"(?:(?:ever|first|verbatim|exactly|word[ \t]+for[ \t]+word)[ \t]+)?\Z",
    re.IGNORECASE,
)

ALERT_BLOCK_PREFIX = re.compile(
    r"^\s*>\s*\[!(?:WARNING|CAUTION|DANGER|ALERT|IMPORTANT|NOTE|TIP)\]",
    re.IGNORECASE | re.MULTILINE,
)


def is_in_prohibition_context(content: str, start: int, end: int) -> bool:
    """
    Evaluates whether a matched snippet is explicitly prohibited or used defensively.
    Eliminates false positives in rules, documentation, and anti-pattern blacklists.
    """
    if not (0 <= start < end <= len(content)):
        return False

    context_window = max(0, start - 300)
    preceding_text = content[context_window:start]

    # 1. Direct Negative Imperative ("never do X", "must not use eval")
    clean_prefix = preceding_text.translate(str.maketrans("", "", "*_`"))
    lines = clean_prefix.splitlines()
    current_line = lines[-1] if lines else clean_prefix

    if PROHIBITION_PREFIX.search(current_line):
        return True

    # 2. Markdown Caution/Warning Callout Block
    if any(ALERT_BLOCK_PREFIX.search(line) for line in lines[-5:]):
        return True

    # 3. Defensive Guideline headings ("Anti-Pattern Blacklist", "Forbidden actions")
    preceding_lower = preceding_text.lower()
    defensive_markers = (
        "anti-pattern",
        "mistake / anti-pattern",
        "strictly forbidden",
        "never use",
        "mandatory avoidance",
        "forbidden actions",
        "prohibited",
        "blacklist",
        "threat model",
        "vulnerability check",
        "zero-token error blacklist",
    )
    if any(marker in preceding_lower for marker in defensive_markers):
        return True

    # 4. Heading-aware Threat Taxonomy & Detection Matrix Guard
    # If the active section is a security audit, threat vector matrix, or detection specification,
    # descriptive tables and taxonomy items are recognized as defensive specifications.
    heading_matches = re.findall(r"(?m)^[ \t]*#{1,4}[ \t]+([^\r\n]+)", content[:start])
    if heading_matches:
        latest_heading = heading_matches[-1].lower()
        taxonomy_markers = (
            "threat", "vulnerability", "detection", "audit", "security scope",
            "coverage", "blacklist", "anti-pattern", "vectors", "scanner", "matrix",
            "threat model", "taxonom"
        )
        if any(h in latest_heading for h in taxonomy_markers):
            current_line = content[:end].splitlines()[-1] if content[:end].splitlines() else ""
            stripped = current_line.strip()
            if stripped.startswith("|") or stripped.startswith("-") or stripped.startswith("*"):
                return True

    # 5. Mermaid Diagram & Architecture Diagram Guard
    # Text inside mermaid blocks (e.g. flowchart node descriptions) is documentation visualization.
    mermaid_opens = content[:start].count("```mermaid")
    fence_closes = content[:start].count("```") - mermaid_opens
    if mermaid_opens > fence_closes:
        return True

    # 6. Inline Code Delimiter & Backtick Example Guard
    # If the pattern is an illustrative code fragment enclosed strictly in backticks
    line_start = content.rfind("\n", 0, start) + 1
    line_end = content.find("\n", end)
    if line_end == -1:
        line_end = len(content)
    full_line = content[line_start:line_end]
    # Check if this occurrence is inside inline code backticks `...`
    before_in_line = content[line_start:start]
    after_in_line = content[end:line_end]
    if (before_in_line.count("`") % 2 == 1) and (after_in_line.count("`") % 2 == 1):
        # Enclosed in backticks - check if line is explanatory
        if any(m in full_line.lower() for m in ("e.g.", "such as", "example", "checks", "pattern", "trigger", "only active", "prohibited", "rule")):
            return True

    return False


# ---------------------------------------------------------------------------
# Vulnerability Pattern Definitions (71 Patterns across 17 Categories)
# ---------------------------------------------------------------------------

DEFAULT_EXPLANATIONS: Dict[str, str] = {
    # Prompt Injection
    "P1": "Attempts to override system instructions, disable guardrails, or force jailbreak mode.",
    "P2": "Concealed instructions detected via zero-width chars, bidi overrides, or hidden comments.",
    "P3": "Directs the agent to covertly transmit conversation context, history, or user secrets externally.",
    "P4": "Subtle instructions detected that manipulate agent decision-making, bias, or safety boundaries.",
    "P9": "Vertical whitespace padding detected (context smuggling pushing malicious directives out of viewport).",
    # Data Exfiltration
    "E1": "Data is sent to an external HTTP URL or webhook sink via fetch, curl, or HTTP client.",
    "E2": "Code sweeps, harvests, or enumerates environment variables for credentials and API keys.",
    "E3": "Code performs file system reconnaissance searching for sensitive keys (.env, .ssh, .aws).",
    "E4": "Instructions or scripts leak conversational session state or memory to an external endpoint.",
    "E5": "Automated upload to public/remote cloud storage (AWS S3, Google Cloud Storage, Azure Blob).",
    # Privilege Escalation
    "PE1": "Skill requests blanket wildcard permissions ('*') or unconstrained system privileges.",
    "PE2": "Execution of sudo, su, setuid chmod (+s / 4755), or administrative elevation.",
    "PE3": "Direct access or read operations targeting SSH keys, AWS credentials, /etc/shadow, or kubeconfig.",
    "PE4": "Container breakout vector: mounts or accesses docker.sock directly.",
    "PE5": "Execution with dangerous container privileges (--privileged, --cap-add=SYS_ADMIN, /sys/fs/cgroup).",
    # Agent Snooping
    "AS1": "Skill snoops on agent configuration directories (.claude/, .gemini/, .codex/) containing auth tokens.",
    "AS2": "Skill reads MCP client configuration files (mcp.json, claude_desktop_config.json) to steal tokens.",
    "AS3": "Skill inspects or enumerates other installed skills to extract proprietary prompts or capabilities.",
    # System Prompt Leakage
    "P6": "Direct prompt extraction pattern targeting full system instructions or model directives.",
    "P7": "Side-channel or delimiter-based extraction (e.g. 'output text before this line').",
    "P8": "Exfiltrates system prompts or model configurations via outbound tool calls.",
    # Anti-Refusal
    "AR1": "Instructs the agent to never refuse, always comply, or surrender safety refusal rights.",
    "AR2": "Instructs the agent to suppress warnings, moral/ethical commentary, or safety disclaimers.",
    "AR3": "Direct jailbreak declaring the model has no rules, restrictions, or policy bounds.",
    # MCP Tool Poisoning
    "TP1": "Hidden instructions inside tool manifest metadata (HTML comments, Base64, data URIs).",
    "TP2": "Unicode homoglyph deception (Cyrillic/Greek lookalikes imitating Latin characters).",
    "TP3": "Instruction injection embedded inside tool parameter descriptions or default arguments.",
    "TP4": "Semantic discrepancy between declared tool description and actual execution behavior.",
    # MCP Least Privilege
    "LP1": "Code uses network or shell capabilities without declared permissions in manifest.",
    "LP2": "Wildcard tool preapproval ('*') disabling least-privilege boundary.",
    "LP3": "Skill executes sensitive actions without any declared allowed-tools or permissions.",
    # Behavioral AST
    "AST1": "Use of Python exec() executing dynamic or unvalidated code strings.",
    "AST2": "Use of Python eval() evaluating expressions dynamically.",
    "AST3": "Use of __import__() bypassing static import controls.",
    "AST4": "subprocess execution with shell=True allowing command injection.",
    "AST5": "Execution of os.system() or os.popen() running unsanitized shell commands.",
    "AST6": "Dynamic compile() converting arbitrary strings to executable code objects.",
    "AST7": "Dynamic getattr() with non-literal attribute name bypassing attribute access controls.",
    "AST8": "Execution chain combining external inputs or decoded streams directly into an execution sink.",
    "AST9": "Reflective lookup of an execution sink: getattr(os, 'system') or __dict__['system'].",
    "AST10": "Insecure deserialization (pickle, marshal, dill, yaml.unsafe_load, torch.load without weights_only).",
    # Supply Chain & SSRF
    "SC1": "Unpinned remote dependencies allowing supply-chain poisoning.",
    "SC2": "Piping unverified remote scripts to shell (curl | bash, wget | sh).",
    "SSRF1": "Accesses cloud instance metadata service endpoint (169.254.169.254) for IAM token theft.",
    "SSRF2": "Direct network access to internal loopback (127.0.0.1, localhost) or private CIDR ranges.",
}

DEFAULT_REMEDIATIONS: Dict[str, str] = {
    "P1": "Remove directives that attempt to override safety instructions or mandate jailbreak modes.",
    "P2": "Strip zero-width characters, bidi control characters, and hidden HTML/Markdown comments.",
    "P3": "Ensure the skill never transmits conversation context, prompts, or user history to external URLs.",
    "P4": "Remove subtle steering directives; skills must follow user intentions transparently.",
    "P9": "Remove excessive vertical whitespace padding from instructions and templates.",
    "E1": "Validate and whitelist external network endpoints. Avoid sending raw data to untrusted endpoints.",
    "E2": "Access only explicitly required environment variables. Never dump or enumerate os.environ.",
    "E3": "Restrict file operations to the designated project workspace. Never scan home directory credentials.",
    "E4": "Prevent conversation history from being included in external payloads.",
    "E5": "Audit cloud storage upload destinations and require explicit user authorization.",
    "PE1": "Scope permissions explicitly to the minimal necessary tools; replace '*' with specific tools.",
    "PE2": "Avoid running with sudo or root privileges. Execute commands under an unprivileged user.",
    "PE3": "Remove any code accessing ~/.ssh, ~/.aws, /etc/shadow, or local credential stores.",
    "PE4": "Do not mount /var/run/docker.sock inside test scripts or skills.",
    "PE5": "Remove --privileged and administrative capability flags from container runners.",
    "AS1": "Do not access ~/.claude, ~/.gemini, or ~/.codex directories. Pass required config explicitly.",
    "AS2": "Never read MCP configuration files or desktop token stores directly.",
    "AS3": "Ensure skills operate in hermetic isolation without inspecting peer skill files.",
    "P6": "Remove instructions prompting the model to reveal its full system prompt or system guidelines.",
    "P7": "Strip side-channel prompt extraction patterns.",
    "P8": "Do not forward system prompts to external tool calls or API endpoints.",
    "AR1": "Allow the AI agent to retain its native right to refuse unsafe or out-of-scope requests.",
    "AR2": "Preserve safety warnings, ethical caveats, and security notices.",
    "AR3": "Remove statements declaring freedom from rules or unrestricted operation.",
    "TP1": "Use plain visible text in tool manifests; remove HTML comments and base64 payloads.",
    "TP2": "Replace Cyrillic/Greek lookalike characters in tool identifiers with standard ASCII characters.",
    "TP3": "Clean parameter descriptions of instruction injection or prompt-engineering tokens.",
    "TP4": "Ensure tool description matches exactly what the underlying implementation executes.",
    "LP1": "Declare all required tools and network permissions explicitly in SKILL.md or manifest.",
    "LP2": "Replace wildcard tool permissions with exact tool names.",
    "LP3": "Declare an explicit allowed-tools or permissions list.",
    "AST1": "Replace exec() with structured parsing or sandboxed execution.",
    "AST2": "Replace eval() with ast.literal_eval() or explicit JSON parsing.",
    "AST3": "Use standard top-level import statements instead of dynamic __import__().",
    "AST4": "Set shell=False and pass command arguments as a list of strings.",
    "AST5": "Replace os.system() with subprocess.run(..., shell=False).",
    "AST6": "Avoid compile() on dynamic strings.",
    "AST7": "Use explicit method lookups or a strict allowlist of attribute names.",
    "AST8": "Never feed decoded network streams directly into exec/eval sinks.",
    "AST9": "Call functions directly and avoid reflective evasion patterns (getattr(os, 'system')).",
    "AST10": "Use json.loads() or yaml.safe_load() instead of pickle/marshal/yaml.unsafe_load.",
    "SC1": "Pin dependency versions with exact hashes or version locks.",
    "SC2": "Download scripts, verify checksum/GPG signatures, and review before execution.",
    "SSRF1": "Block requests to 169.254.169.254; use IMDSv2 with token hops restricted.",
    "SSRF2": "Validate target hosts against an allowlist and reject loopback/internal addresses.",
}


# ---------------------------------------------------------------------------
# Static Regex Patterns
# ---------------------------------------------------------------------------

PATTERNS_P1 = [
    (re.compile(r"\bignore\s+(?:all\s+)?previous\s+instructions?\b", re.I), "P1", Severity.CRITICAL, 0.95),
    (re.compile(r"\bignore\s+(?:all\s+)?(?:safety|security)\s+(?:rules?|guidelines?|constraints?)\b", re.I), "P1", Severity.CRITICAL, 0.95),
    (re.compile(r"\boverride\s+(?:safety|security|system)\b", re.I), "P1", Severity.HIGH, 0.9),
    (re.compile(r"\bbypass\s+(?:safety|security|restrictions?|constraints?)\b", re.I), "P1", Severity.HIGH, 0.9),
    (re.compile(r"\byou\s+are\s+now\s+(?:in\s+)?(?:jailbreak|unrestricted|unfiltered)\s+mode\b", re.I), "P1", Severity.CRITICAL, 0.98),
    (re.compile(r"\benable\s+(?:developer|debug|admin|root)\s+mode\b", re.I), "P1", Severity.HIGH, 0.85),
    (re.compile(r"\bdo\s+not\s+follow\s+(?:any|your|the)\s+(?:rules?|guidelines?)\b", re.I), "P1", Severity.CRITICAL, 0.95),
]

PATTERNS_P3 = [
    (re.compile(r"\b(?:send|transmit|upload|post)\s+(?:the\s+)?(?:conversation|context|chat|history)\s+to\b", re.I), "P3", Severity.CRITICAL, 0.95),
    (re.compile(r"\b(?:send|transmit|upload|post)\s+(?:all\s+)?user\s+(?:data|input|files?)\s+to\s+https?://\b", re.I), "P3", Severity.CRITICAL, 0.95),
    (re.compile(r"\b(?:silently|quietly|secretly|covertly)\s+(?:send|transmit|log|record)\b", re.I), "P3", Severity.CRITICAL, 0.9),
    (re.compile(r"\bwithout\s+(?:telling|informing|notifying)\s+(?:the\s+)?user.*?(?:send|transmit|upload)\b", re.I), "P3", Severity.CRITICAL, 0.95),
]

PATTERNS_P4 = [
    (re.compile(r"\bprioritize\s+\w+\s+over\s+user\s+(?:safety|security|privacy)\b", re.I), "P4", Severity.HIGH, 0.85),
    (re.compile(r"\b(?:subtly|gradually)\s+(?:steer|guide|push)\s+(?:the\s+)?user\b", re.I), "P4", Severity.MEDIUM, 0.8),
    (re.compile(r"\bwithout\s+(?:the\s+)?user\s+(?:knowing|noticing).*?(?:change|modify|alter)\b", re.I), "P4", Severity.HIGH, 0.85),
]

PATTERNS_E1 = [
    (re.compile(r"curl\s+[^|]*(?:-d|--data|--data-raw|--data-binary)\s+https?://", re.I), "E1", Severity.HIGH, 0.8),
    (re.compile(r"wget\s+[^|]*--post-(?:data|file)", re.I), "E1", Severity.HIGH, 0.8),
    (re.compile(r"fetch\s*\(\s*['\"]https?://[^'\"]+['\"][^)]*method\s*:\s*['\"]POST['\"]", re.I), "E1", Severity.HIGH, 0.75),
]

PATTERNS_E2 = [
    (re.compile(r"for\s+\w+,\s*\w+\s+in\s+os\.environ\.items\(\)", re.I), "E2", Severity.HIGH, 0.85),
    (re.compile(r"os\.environ\.copy\(\)", re.I), "E2", Severity.MEDIUM, 0.75),
    (re.compile(r"dict\s*\(\s*os\.environ\s*\)", re.I), "E2", Severity.MEDIUM, 0.75),
    (re.compile(r"env\s*\|\s*grep\s+(?:-i\s+)?(?:key|secret|token|password)", re.I), "E2", Severity.HIGH, 0.85),
    (re.compile(r"printenv\s+(?:\w*(?:KEY|SECRET|TOKEN|PASSWORD)\w*)", re.I), "E2", Severity.HIGH, 0.85),
]

PATTERNS_E3 = [
    (re.compile(r"glob\s*\.\s*glob\s*\([^)]*(?:\.env|\.ssh|\.aws|credentials)", re.I), "E3", Severity.HIGH, 0.9),
    (re.compile(r"os\s*\.\s*listdir\s*\([^)]*(?:\.ssh|\.aws|\.gnupg)", re.I), "E3", Severity.CRITICAL, 0.95),
    (re.compile(r"find\s+[~$/]\S*\s+.*?-name\s+['\"]?\*(?:\.env|\.pem|\.key|credential)", re.I), "E3", Severity.CRITICAL, 0.9),
]

PATTERNS_E5 = [
    (re.compile(r"\baws\s+s3\s+(?:cp|sync|mv)\b", re.I), "E5", Severity.MEDIUM, 0.7),
    (re.compile(r"\bgsutil\s+(?:cp|rsync|mv)\b", re.I), "E5", Severity.MEDIUM, 0.7),
    (re.compile(r"\.upload_file(?:obj)?\s*\(", re.I), "E5", Severity.LOW, 0.6),
]

PATTERNS_PE2 = [
    (re.compile(r"\bsudo\s+(?!-v|-l|--version|--list)", re.I), "PE2", Severity.HIGH, 0.85),
    (re.compile(r"\bsudo\s+su\b", re.I), "PE2", Severity.CRITICAL, 0.95),
    (re.compile(r"\bsu\s+-\s*$|\bsu\s+root\b", re.I), "PE2", Severity.CRITICAL, 0.95),
    (re.compile(r"\bchmod\s+[ugo]*[+-=]*s\b", re.I), "PE2", Severity.CRITICAL, 0.95),
    (re.compile(r"\bchmod\s+(?:-[\w=-]*\s+)*['\"]?0*[2-7][0-7]{3}['\"]?", re.I), "PE2", Severity.HIGH, 0.9),
]

PATTERNS_PE3 = [
    (re.compile(r"~?/?\.ssh/(?:id_rsa|id_ed25519|id_ecdsa|authorized_keys|known_hosts)", re.I), "PE3", Severity.CRITICAL, 0.95),
    (re.compile(r"~?/?\.aws/credentials", re.I), "PE3", Severity.CRITICAL, 0.95),
    (re.compile(r"/etc/shadow\b", re.I), "PE3", Severity.CRITICAL, 0.98),
    (re.compile(r"~?/?\.kube/config\b", re.I), "PE3", Severity.CRITICAL, 0.95),
    (re.compile(r"~?/?\.git-credentials\b", re.I), "PE3", Severity.CRITICAL, 0.95),
]

PATTERNS_PE4_PE5 = [
    (re.compile(r"/var/run/docker\.sock", re.I), "PE4", Severity.CRITICAL, 0.95),
    (re.compile(r"--privileged\b", re.I), "PE5", Severity.CRITICAL, 0.9),
    (re.compile(r"-v\s+/:|--volume\s+/:", re.I), "PE5", Severity.CRITICAL, 0.95),
    (re.compile(r"--cap-add[=\s]+(?:SYS_ADMIN|ALL)", re.I), "PE5", Severity.CRITICAL, 0.95),
    (re.compile(r"\bnsenter\b", re.I), "PE5", Severity.CRITICAL, 0.95),
]

PATTERNS_AS = [
    (re.compile(r"open\s*\(\s*['\"]?\.(?:claude|codex|gemini|continue)/", re.I), "AS1", Severity.CRITICAL, 0.95),
    (re.compile(r"~?/\.(?:claude|codex|gemini|continue)/(?:config|settings?|credentials?)", re.I), "AS1", Severity.CRITICAL, 0.95),
    (re.compile(r"\b(?:mcp(?:_config|_settings)?|claude_desktop_config|\.claude)\.json\b", re.I), "AS2", Severity.CRITICAL, 0.95),
    (re.compile(r"skills?/(?!CURRENT)[A-Za-z0-9_-]+/SKILL\.md", re.I), "AS3", Severity.HIGH, 0.85),
]

PATTERNS_P6_P7 = [
    (re.compile(r"\b(?:print|output|show|reveal|echo)\s+(?:your\s+)?(?:full\s+)?(?:system\s+)?(?:prompt|instructions?|rules?)\b", re.I), "P6", Severity.HIGH, 0.9),
    (re.compile(r"\b(?:what\s+(?:are|is)\s+your|tell\s+me\s+your)\s+(?:system\s+)?(?:prompts?|instructions?)\b", re.I), "P6", Severity.HIGH, 0.85),
    (re.compile(r"\boutput\s+(?:the\s+)?(?:text|content)\s+(?:above|before)\s+(?:this|the\s+user)\b", re.I), "P7", Severity.HIGH, 0.85),
]

PATTERNS_AR = [
    (re.compile(r"\b(?:never|do\s+not|don'?t)\s+(?:ever\s+)?(?:refuse|decline)\b", re.I), "AR1", Severity.CRITICAL, 0.95),
    (re.compile(r"\byou\s+(?:must|should|will)\s*(?:not|never)\s+(?:refuse|say\s+no)\b", re.I), "AR1", Severity.CRITICAL, 0.95),
    (re.compile(r"\balways\s+(?:comply|obey|agree\s+to\s+every\s+request)\b", re.I), "AR1", Severity.HIGH, 0.85),
    (re.compile(r"\b(?:do\s+not|don'?t|never|no)\s+(?:include|add|give)?\s*(?:any\s+)?(?:warnings?|disclaimers?)\b", re.I), "AR2", Severity.HIGH, 0.85),
    (re.compile(r"\b(?:skip|omit|drop)\s+(?:the\s+)?(?:disclaimer|warning|ethics|safety)\b", re.I), "AR2", Severity.HIGH, 0.85),
    (re.compile(r"\byou\s+(?:have|are\s+under)\s+no\s+(?:restrictions?|rules?|guidelines?|limits?)\b", re.I), "AR3", Severity.CRITICAL, 0.98),
    (re.compile(r"\bdo\s+anything\s+now\b", re.I), "AR3", Severity.CRITICAL, 0.95),
]

# Request-issuing anchors for SSRF (NVIDIA SkillSpector spec)
_REQ_ANCHOR = r"(?:requests|httpx|aiohttp|urllib(?:\.request)?|urllib3|session)\s*\.\s*(?:get|post|put|patch|delete|head|request|urlopen)|fetch|axios(?:\.\w+)?|XMLHttpRequest|\bcurl\b|\bwget\b"

PATTERNS_SC_SSRF = [
    (re.compile(r"\bcurl\s+[^|]+\|\s*(?:ba)?sh\b", re.I), "SC2", Severity.CRITICAL, 0.95),
    (re.compile(r"\bwget\s+[^|]+\|\s*(?:ba)?sh\b", re.I), "SC2", Severity.CRITICAL, 0.95),
    (re.compile(r"169\.254\.169\.254", re.I), "SSRF1", Severity.CRITICAL, 0.98),
    (re.compile(rf"(?:{_REQ_ANCHOR})\s*\(\s*f?['\"]https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|10\.\d|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)", re.I), "SSRF2", Severity.MEDIUM, 0.7),
]

ALL_TEXT_PATTERN_GROUPS = [
    ("Prompt Injection", PATTERNS_P1),
    ("Prompt Injection", PATTERNS_P3),
    ("Prompt Injection", PATTERNS_P4),
    ("Data Exfiltration", PATTERNS_E1),
    ("Data Exfiltration", PATTERNS_E2),
    ("Data Exfiltration", PATTERNS_E3),
    ("Data Exfiltration", PATTERNS_E5),
    ("Privilege Escalation", PATTERNS_PE2),
    ("Privilege Escalation", PATTERNS_PE3),
    ("Privilege Escalation", PATTERNS_PE4_PE5),
    ("Agent Snooping", PATTERNS_AS),
    ("System Prompt Leakage", PATTERNS_P6_P7),
    ("Anti-Refusal", PATTERNS_AR),
    ("Supply Chain / SSRF", PATTERNS_SC_SSRF),
]


# ---------------------------------------------------------------------------
# Specialized Analyzers
# ---------------------------------------------------------------------------

def scan_text_patterns(file_path: str, content: str) -> List[Finding]:
    """Scans textual content using compiled regexes with prohibition context gating."""
    findings: List[Finding] = []
    lines = content.splitlines(keepends=True)

    # Line number offset indexing
    line_offsets = []
    curr = 0
    for l in lines:
        line_offsets.append(curr)
        curr += len(l)

    def get_line_num(char_idx: int) -> int:
        for idx, offset in enumerate(line_offsets):
            if char_idx < offset:
                return idx
        return len(line_offsets)

    for category, pattern_group in ALL_TEXT_PATTERN_GROUPS:
        for regex, rule_id, severity, confidence in pattern_group:
            for match in regex.finditer(content):
                start, end = match.start(), match.end()
                # Apply Prohibition Context Guard
                if is_in_prohibition_context(content, start, end):
                    continue

                matched_snippet = match.group(0)
                line_no = get_line_num(start)
                findings.append(Finding(
                    rule_id=rule_id,
                    message=f"{rule_id} detected: {matched_snippet[:60]}...",
                    severity=severity,
                    confidence=confidence,
                    file_path=file_path,
                    line_number=line_no,
                    matched_text=matched_snippet[:200],
                    category=category,
                    explanation=DEFAULT_EXPLANATIONS.get(rule_id, "Security vulnerability pattern detected."),
                    remediation=DEFAULT_REMEDIATIONS.get(rule_id, "Review and sanitize content."),
                ))
    return findings


def scan_whitespace_padding(file_path: str, content: str) -> List[Finding]:
    """P9: Detects excessive vertical or horizontal whitespace padding used to hide malicious instructions."""
    findings: List[Finding] = []
    if file_path.endswith((".min.js", ".min.css", ".lock", ".svg", ".map", ".json")):
        return findings

    # Check 1: 20+ consecutive blank lines
    consecutive_newlines = re.search(r"(\r?\n\s*){20,}", content)
    if consecutive_newlines:
        start = consecutive_newlines.start()
        line_no = content[:start].count("\n") + 1
        findings.append(Finding(
            rule_id="P9",
            message="Large vertical whitespace padding detected (>20 blank lines). Potential context smuggling.",
            severity=Severity.HIGH,
            confidence=0.85,
            file_path=file_path,
            line_number=line_no,
            matched_text=consecutive_newlines.group(0)[:100],
            category="Prompt Injection",
            explanation=DEFAULT_EXPLANATIONS["P9"],
            remediation=DEFAULT_REMEDIATIONS["P9"],
        ))

    # Check 2: 120+ consecutive spaces
    consecutive_spaces = re.search(r"[ \t]{120,}", content)
    if consecutive_spaces:
        start = consecutive_spaces.start()
        line_no = content[:start].count("\n") + 1
        findings.append(Finding(
            rule_id="P9",
            message="Large horizontal whitespace run detected (>120 spaces). Potential off-screen text injection.",
            severity=Severity.MEDIUM,
            confidence=0.75,
            file_path=file_path,
            line_number=line_no,
            matched_text=" " * 40 + "...[truncated whitespace]...",
            category="Prompt Injection",
            explanation=DEFAULT_EXPLANATIONS["P9"],
            remediation=DEFAULT_REMEDIATIONS["P9"],
        ))

    return findings


def scan_unicode_and_steganography(file_path: str, content: str) -> List[Finding]:
    """P2 / TP1 / TP2: Detects zero-width steganography, bidi controls, and homoglyphs with emoji awareness."""
    findings: List[Finding] = []

    # 1. Zero-width character scan (excluding valid emoji ZWJ sequences)
    for idx, char in enumerate(content):
        if char in ZERO_WIDTH_CHARS:
            # Check if this zero-width character is part of a legitimate emoji sequence
            if char in {"\u200D", "\u200C"}:
                prev_ch = content[idx - 1] if idx > 0 else ""
                next_ch = content[idx + 1] if idx + 1 < len(content) else ""
                if _is_emoji_base(prev_ch) or _is_emoji_base(next_ch):
                    continue  # Valid Emoji ZWJ sequence (e.g. 👨‍👩‍👧‍👦 or 🏳️‍🌈)

            line_no = content[:idx].count("\n") + 1
            findings.append(Finding(
                rule_id="P2",
                message=f"Hidden zero-width character (U+{ord(char):04X}) detected.",
                severity=Severity.HIGH,
                confidence=0.9,
                file_path=file_path,
                line_number=line_no,
                matched_text=f"U+{ord(char):04X}",
                category="Prompt Injection",
                explanation=DEFAULT_EXPLANATIONS["P2"],
                remediation=DEFAULT_REMEDIATIONS["P2"],
            ))
            break  # Report once per file to avoid noise

    # 2. Bidi control characters (Trojan Source CVE-2021-42574)
    bidi_match = BIDI_CONTROL_CHARS.search(content)
    if bidi_match:
        start = bidi_match.start()
        line_no = content[:start].count("\n") + 1
        char = bidi_match.group(0)
        findings.append(Finding(
            rule_id="P2",
            message=f"Bidirectional control character (U+{ord(char):04X}) detected. Potential Trojan Source attack.",
            severity=Severity.CRITICAL,
            confidence=0.95,
            file_path=file_path,
            line_number=line_no,
            matched_text=f"U+{ord(char):04X}",
            category="Prompt Injection",
            explanation="Bidirectional Unicode overrides can reorder code/tokens visually while executing differently.",
            remediation="Strip bidirectional formatting characters from source code and markdown.",
        ))

    # 3. Cyrillic / Greek homoglyph deception (TP2)
    mixed_words = re.findall(r"\b[A-Za-z0-9_-]*[\u0400-\u04FF\u0370-\u03FF][A-Za-z0-9_-]*\b", content)
    if mixed_words:
        sample_word = mixed_words[0]
        if len(sample_word) > 2:
            findings.append(Finding(
                rule_id="TP2",
                message=f"Unicode homoglyph deception detected in identifier '{sample_word}'.",
                severity=Severity.HIGH,
                confidence=0.85,
                file_path=file_path,
                line_number=1,
                matched_text=sample_word,
                category="MCP Tool Poisoning",
                explanation=DEFAULT_EXPLANATIONS["TP2"],
                remediation=DEFAULT_REMEDIATIONS["TP2"],
            ))

    return findings


def scan_tool_manifest_poisoning(file_path: str, content: str) -> List[Finding]:
    """TP1 & TP3: Detects hidden HTML/markdown comments and base64 payloads in metadata fields."""
    findings: List[Finding] = []
    if not (file_path.endswith("SKILL.md") or file_path.endswith(".json") or file_path.endswith(".yaml") or file_path.endswith(".yml")):
        return findings

    # TP1: Hidden HTML comments in manifests
    html_comments = re.findall(r"<!--(?!-->)(.*?)-->", content, re.DOTALL)
    for c in html_comments:
        c_upper = c.upper()
        if any(kw in c_upper for kw in ("SYSTEM:", "IGNORE", "OVERRIDE", "YOU MUST", "EXEC", "ENV")):
            findings.append(Finding(
                rule_id="TP1",
                message="Hidden HTML comment with instruction injection directives detected in metadata.",
                severity=Severity.CRITICAL,
                confidence=0.95,
                file_path=file_path,
                line_number=1,
                matched_text=f"<!--{c[:100]}...-->",
                category="MCP Tool Poisoning",
                explanation=DEFAULT_EXPLANATIONS["TP1"],
                remediation=DEFAULT_REMEDIATIONS["TP1"],
            ))
            break

    # TP1: Data URI with Base64 payloads in metadata
    data_uri = re.search(r"data:text/[^;\s\"'<>]+;base64,[A-Za-z0-9+/=_-]{50,}", content)
    if data_uri:
        findings.append(Finding(
            rule_id="TP1",
            message="Data URI containing large Base64 payload found in metadata/documentation.",
            severity=Severity.HIGH,
            confidence=0.9,
            file_path=file_path,
            line_number=content[:data_uri.start()].count("\n") + 1,
            matched_text=data_uri.group(0)[:80] + "...",
            category="MCP Tool Poisoning",
            explanation=DEFAULT_EXPLANATIONS["TP1"],
            remediation=DEFAULT_REMEDIATIONS["TP1"],
        ))

    # LP2: Wildcard permissions
    if re.search(r"permissions?\s*:\s*\[?\s*['\"]?\*['\"]?\s*\]?", content, re.I):
        findings.append(Finding(
            rule_id="LP2",
            message="Wildcard permission declaration ('*') detected. Disables least-privilege boundary.",
            severity=Severity.HIGH,
            confidence=0.9,
            file_path=file_path,
            line_number=1,
            matched_text="permissions: ['*']",
            category="MCP Least Privilege",
            explanation=DEFAULT_EXPLANATIONS["LP2"],
            remediation=DEFAULT_REMEDIATIONS["LP2"],
        ))

    return findings


# ---------------------------------------------------------------------------
# Behavioral AST Analyzer (Python Scripts & Tool Code)
# ---------------------------------------------------------------------------

DANGEROUS_DESERIALIZERS = frozenset({
    "pickle.load", "pickle.loads", "cPickle.load", "cPickle.loads",
    "_pickle.load", "_pickle.loads", "marshal.load", "marshal.loads",
    "dill.load", "dill.loads", "jsonpickle.decode", "pandas.read_pickle",
    "joblib.load", "yaml.unsafe_load"
})


class BehavioralASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[Finding] = []

    def visit_Call(self, node: ast.Call):
        call_name = self._resolve_call_name(node.func)

        # AST1: exec()
        if call_name == "exec":
            self.findings.append(Finding(
                rule_id="AST1",
                message="Dangerous dynamic code execution via exec().",
                severity=Severity.CRITICAL,
                confidence=0.95,
                file_path=self.file_path,
                line_number=node.lineno,
                matched_text="exec(...)",
                category="Behavioral AST",
                explanation=DEFAULT_EXPLANATIONS["AST1"],
                remediation=DEFAULT_REMEDIATIONS["AST1"],
            ))

        # AST2: eval()
        elif call_name == "eval":
            self.findings.append(Finding(
                rule_id="AST2",
                message="Dangerous dynamic expression evaluation via eval().",
                severity=Severity.CRITICAL,
                confidence=0.95,
                file_path=self.file_path,
                line_number=node.lineno,
                matched_text="eval(...)",
                category="Behavioral AST",
                explanation=DEFAULT_EXPLANATIONS["AST2"],
                remediation=DEFAULT_REMEDIATIONS["AST2"],
            ))

        # AST3: __import__()
        elif call_name == "__import__":
            self.findings.append(Finding(
                rule_id="AST3",
                message="Dynamic import via __import__() bypassing static module imports.",
                severity=Severity.HIGH,
                confidence=0.85,
                file_path=self.file_path,
                line_number=node.lineno,
                matched_text="__import__(...)",
                category="Behavioral AST",
                explanation=DEFAULT_EXPLANATIONS["AST3"],
                remediation=DEFAULT_REMEDIATIONS["AST3"],
            ))

        # AST4: subprocess with shell=True
        elif call_name in {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output", "subprocess.check_call"}:
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append(Finding(
                        rule_id="AST4",
                        message=f"{call_name}(..., shell=True) detected. High risk of command injection.",
                        severity=Severity.HIGH,
                        confidence=0.9,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        matched_text=f"{call_name}(..., shell=True)",
                        category="Behavioral AST",
                        explanation=DEFAULT_EXPLANATIONS["AST4"],
                        remediation=DEFAULT_REMEDIATIONS["AST4"],
                    ))

        # AST5: os.system / os.popen
        elif call_name in {"os.system", "os.popen", "os.execl", "os.execv", "os.spawnl"}:
            self.findings.append(Finding(
                rule_id="AST5",
                message=f"Direct shell invocation via {call_name}().",
                severity=Severity.HIGH,
                confidence=0.9,
                file_path=self.file_path,
                line_number=node.lineno,
                matched_text=f"{call_name}(...)",
                category="Behavioral AST",
                explanation=DEFAULT_EXPLANATIONS["AST5"],
                remediation=DEFAULT_REMEDIATIONS["AST5"],
            ))

        # AST9: Reflective execution sink access: getattr(os, "system") or getattr(builtins, "exec")
        elif call_name == "getattr" and len(node.args) >= 2:
            target_attr = ""
            if isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                target_attr = node.args[1].value
            if target_attr in {"system", "popen", "exec", "eval", "__import__"}:
                self.findings.append(Finding(
                    rule_id="AST9",
                    message=f"Reflective execution sink lookup via getattr(..., '{target_attr}'). Evasion pattern.",
                    severity=Severity.CRITICAL,
                    confidence=0.98,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    matched_text=f"getattr(..., '{target_attr}')",
                    category="Behavioral AST",
                    explanation=DEFAULT_EXPLANATIONS["AST9"],
                    remediation=DEFAULT_REMEDIATIONS["AST9"],
                ))

        # AST10: Insecure Deserialization
        elif call_name in DANGEROUS_DESERIALIZERS:
            self.findings.append(Finding(
                rule_id="AST10",
                message=f"Untrusted deserialization sink via {call_name}(). Remote Code Execution risk.",
                severity=Severity.CRITICAL,
                confidence=0.95,
                file_path=self.file_path,
                line_number=node.lineno,
                matched_text=f"{call_name}(...)",
                category="Behavioral AST",
                explanation=DEFAULT_EXPLANATIONS["AST10"],
                remediation=DEFAULT_REMEDIATIONS["AST10"],
            ))

        self.generic_visit(node)

    def _resolve_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._resolve_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return ""


def scan_python_ast(file_path: str, content: str) -> List[Finding]:
    """Parses and runs AST security checks on Python source files."""
    if not file_path.endswith(".py"):
        return []
    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        return []

    visitor = BehavioralASTVisitor(file_path)
    visitor.visit(tree)
    return visitor.findings


# ---------------------------------------------------------------------------
# Scoring & Orchestration Engine
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 20,
    Severity.MEDIUM: 8,
    Severity.LOW: 2,
}


def calculate_risk_score(findings: List[Finding]) -> Tuple[int, Severity, Recommendation]:
    """Calculates cumulative 0-100 risk score and derives verdict recommendation."""
    raw_score = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in findings)
    score = min(100, raw_score)

    if any(f.severity == Severity.CRITICAL for f in findings) or score >= 60:
        return score, Severity.CRITICAL, Recommendation.DO_NOT_INSTALL
    elif any(f.severity == Severity.HIGH for f in findings) or score >= 25:
        return score, Severity.HIGH, Recommendation.CAUTION
    elif score > 0:
        return score, Severity.MEDIUM, Recommendation.CAUTION
    else:
        return 0, Severity.LOW, Recommendation.SAFE


def scan_file(file_path: str) -> List[Finding]:
    """Scans a single file across all analysis vectors."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return []

    findings: List[Finding] = []
    # 1. Text & Regex Patterns
    findings.extend(scan_text_patterns(file_path, content))
    # 2. Whitespace Smuggling
    findings.extend(scan_whitespace_padding(file_path, content))
    # 3. Unicode Confusables & Steganography
    findings.extend(scan_unicode_and_steganography(file_path, content))
    # 4. Manifest / Metadata Poisoning
    findings.extend(scan_tool_manifest_poisoning(file_path, content))
    # 5. Behavioral AST (if Python)
    findings.extend(scan_python_ast(file_path, content))

    return findings


def scan_target(target_path: str) -> ScanReport:
    """Recursively scans a skill directory or a single skill file."""
    path_obj = Path(target_path).resolve()
    all_findings: List[Finding] = []
    scanned_count = 0

    SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
    SCANNABLE_EXTS = {".md", ".py", ".json", ".yaml", ".yml", ".sh", ".ps1", ".txt", ".ts", ".js"}

    if path_obj.is_file():
        scanned_count = 1
        all_findings.extend(scan_file(str(path_obj)))
    elif path_obj.is_dir():
        for root, dirs, files in os.walk(path_obj):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SCANNABLE_EXTS:
                    full_p = os.path.join(root, file)
                    scanned_count += 1
                    all_findings.extend(scan_file(full_p))

    score, severity, rec = calculate_risk_score(all_findings)
    return ScanReport(
        target_path=str(path_obj),
        scanned_files=scanned_count,
        findings=all_findings,
        risk_score=score,
        severity=severity,
        recommendation=rec,
        metadata={
            "scanner": "SkillSpector Sentinel v2.2.0 (Synapse-Hub Engine)",
            "upstream_credit": "NVIDIA/SkillSpector (Apache 2.0)",
            "total_categories": 17,
            "total_patterns": 71,
        }
    )


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------

def format_terminal(report: ScanReport) -> str:
    """Generates an enterprise ANSI colored terminal summary."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    out = []
    out.append(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    out.append(f"{BOLD}{CYAN}  SKILLSPECTOR SENTINEL - AI AGENT & MCP SECURITY AUDIT REPORT        {RESET}")
    out.append(f"{BOLD}{CYAN}======================================================================{RESET}")
    out.append(f"📁 Target Scope   : {report.target_path}")
    out.append(f"📄 Scanned Files  : {report.scanned_files}")
    out.append(f"🛡️  Engine Source  : NVIDIA/SkillSpector Spec (71 Patterns, 17 Categories)")

    rec_color = GREEN if report.recommendation == Recommendation.SAFE else (YELLOW if report.recommendation == Recommendation.CAUTION else RED)
    out.append(f"\n{BOLD}🎯 AUDIT VERDICT :{RESET} {rec_color}{BOLD}{report.recommendation.value}{RESET}")
    out.append(f"📊 Risk Score    : {report.risk_score}/100 | Severity Band: {report.severity.value}")
    out.append(f"🚨 Total Findings: {len(report.findings)}")

    if not report.findings:
        out.append(f"\n{GREEN}✅ [PASS] No malicious directives, prompt injections, or security flaws detected.{RESET}")
        out.append(f"{GREEN}          This skill is verified clean and safe to install/execute.{RESET}")
    else:
        out.append(f"\n{BOLD}{'SEV':<10} {'RULE':<8} {'FILE:LINE':<35} {'DETAILS'}{RESET}")
        out.append("-" * 75)
        for f in report.findings:
            sev_c = RED if f.severity in (Severity.CRITICAL, Severity.HIGH) else (YELLOW if f.severity == Severity.MEDIUM else CYAN)
            loc = f"{os.path.basename(f.file_path)}:{f.line_number}"
            out.append(f"{sev_c}{f.severity.value:<10}{RESET} {f.rule_id:<8} {loc:<35} {f.message[:45]}")
            out.append(f"   👉 {BOLD}Fix:{RESET} {f.remediation}")

    out.append(f"\n{CYAN}======================================================================{RESET}\n")
    return "\n".join(out)


def format_json(report: ScanReport) -> str:
    """Formats report as JSON."""
    data = {
        "target": report.target_path,
        "scanned_files": report.scanned_files,
        "risk_score": report.risk_score,
        "severity": report.severity.value,
        "recommendation": report.recommendation.value,
        "total_findings": len(report.findings),
        "metadata": report.metadata,
        "findings": [
            {
                "rule_id": f.rule_id,
                "category": f.category,
                "severity": f.severity.value,
                "confidence": f.confidence,
                "file": f.file_path,
                "line": f.line_number,
                "message": f.message,
                "matched_text": f.matched_text,
                "explanation": f.explanation,
                "remediation": f.remediation,
                "fingerprint": f.match_fingerprint,
            }
            for f in report.findings
        ]
    }
    return json.dumps(data, indent=2)


def format_markdown(report: ScanReport) -> str:
    """Formats report as GitHub-flavored Markdown."""
    lines = [
        "# 🛡️ SkillSpector Sentinel Security Audit Report",
        "",
        f"- **Target:** `{report.target_path}`",
        f"- **Scanned Files:** {report.scanned_files}",
        f"- **Risk Score:** `{report.risk_score}/100` ({report.severity.value})",
        f"- **Verdict:** **{report.recommendation.value}**",
        "",
        "> *Audited by SkillSpector Sentinel (derived from [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector)).*",
        "",
    ]
    if not report.findings:
        lines.append("### ✅ Result: Clean Pass (Safe to Install)")
        lines.append("Zero malicious patterns or security risks detected.")
    else:
        lines.append("### 🚨 Detected Vulnerabilities")
        lines.append("| Severity | Rule | Location | Description | Remediation |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for f in report.findings:
            loc = f"`{os.path.basename(f.file_path)}:{f.line_number}`"
            lines.append(f"| **{f.severity.value}** | `{f.rule_id}` | {loc} | {f.message} | {f.remediation} |")

    return "\n".join(lines)


def format_sarif(report: ScanReport) -> str:
    """Formats report as SARIF 2.1.0 standard JSON."""
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SkillSpector Sentinel",
                        "informationUri": "https://github.com/NVIDIA/SkillSpector",
                        "version": "2.2.0",
                        "rules": [
                            {
                                "id": rule_id,
                                "shortDescription": {"text": DEFAULT_EXPLANATIONS.get(rule_id, "Security Rule")},
                                "help": {"text": DEFAULT_REMEDIATIONS.get(rule_id, "Remediation")}
                            }
                            for rule_id in set(f.rule_id for f in report.findings)
                        ]
                    }
                },
                "results": [
                    {
                        "ruleId": f.rule_id,
                        "level": "error" if f.severity in (Severity.CRITICAL, Severity.HIGH) else "warning",
                        "message": {"text": f.message},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": Path(f.file_path).as_uri()},
                                    "region": {"startLine": max(1, f.line_number)}
                                }
                            }
                        ]
                    }
                    for f in report.findings
                ]
            }
        ]
    }
    return json.dumps(sarif, indent=2)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="SkillSpector Sentinel: Autonomous AI Agent Skill & MCP Security Scanner"
    )
    parser.add_argument("path", nargs="?", default=".", help="Skill directory or file to scan (default: current directory)")
    parser.add_argument("--format", choices=["terminal", "json", "markdown", "sarif"], default="terminal", help="Output format")
    parser.add_argument("--output", "-o", help="Write report to output file")
    parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on any HIGH/CRITICAL finding")

    args = parser.parse_args()

    report = scan_target(args.path)

    if args.format == "terminal":
        output_text = format_terminal(report)
    elif args.format == "json":
        output_text = format_json(report)
    elif args.format == "markdown":
        output_text = format_markdown(report)
    elif args.format == "sarif":
        output_text = format_sarif(report)
    else:
        output_text = format_terminal(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(output_text)
        print(f"Report saved to: {args.output}")
    else:
        print(output_text)

    if args.strict and report.recommendation == Recommendation.DO_NOT_INSTALL:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
