#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Thế Vị (@TeeVee998). All rights reserved.
# SPDX-License-Identifier: MIT
# Project: Synapse-Hub (https://github.com/TeeVee998/Synapse-Hub)

"""
Gherkin BDD Suite Compiler - Natural-Language Test Ingestion (0-Token)
----------------------------------------------------------------------
Parses Gherkin `.feature` files (Feature / Rule / Background / Scenario /
Scenario Outline / Examples / Tags / Doc Strings / Data Tables) and compiles
them into:

  1. An expanded, deterministic test-case matrix (one case per Example row).
  2. Hub-native Universal IR (TestCaseIR + StepIR) for the omni transpile
     pipeline (--emit-ir).
  3. A Markdown BDD test plan with "proven vs owed" coverage-gap analysis
     (missing assertions, missing negative paths, thin example tables,
     unresolved parameters).

Provenance:
  - Concept inspired by the Gherkin-driven E2E ingestion workflow popularized
    by TestZeus Hercules (AGPL-3.0). This is an independent, from-scratch,
    stdlib-only re-expression of the concept - no upstream code or text is
    used (AGPL content must not be copied into this MIT repository).
  - The "proven vs owed" coverage traceability idea is inspired by Kane CLI
    (Apache-2.0), re-expressed in original wording.
  - English Gherkin keywords only (Given/When/Then/And/But); a `# language:`
    header is ignored by design.

Exit codes: 0 = compiled (warnings allowed), 1 = parse/authoring errors
(report and plan are still emitted so the suite can be iterated on).
"""

import os
import re
import sys
import json
import copy
import glob
import argparse
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from universal_ir import (  # noqa: E402
    ActionType,
    AssertionType,
    StepIR,
    TestCaseIR,
    WaitStrategy,
)

REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
OUTPUT_JSON = os.path.join(REPORTS_DIR, "gherkin_suite_report.json")

# ANSI Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

CONCRETE_STEP_KEYWORDS = ("Given", "When", "Then")
STEP_ROLES = {"Given": "arrange", "When": "act", "Then": "assert"}
NEGATIVE_SIGNAL_PATTERN = re.compile(
    r"invalid|error|fail|negativ|empty|denied|unauthor|wrong|incorrect", re.IGNORECASE
)
QUOTE_PATTERN = re.compile(r'"([^"]+)"|\'([^\']+)\'')
PARAM_PATTERN = re.compile(r"<([^<>\n]+)>")
URL_PATTERN = re.compile(r"https?://[^\s\"']+")


# ---------------------------------------------------------------------------
# Gherkin document model
# ---------------------------------------------------------------------------

@dataclass
class GherkinStep:
    keyword: str          # Concrete keyword (And/But already resolved)
    raw_keyword: str      # Keyword as written in the file (may be And/But)
    text: str
    role: str             # arrange | act | assert
    docstring: Optional[str] = None
    docstring_type: str = ""
    table_rows: List[List[str]] = field(default_factory=list)

    def display_text(self) -> str:
        parts = [self.text]
        if self.table_rows:
            parts.append("\n".join("| " + " | ".join(r) + " |" for r in self.table_rows))
        if self.docstring is not None:
            parts.append('"""\n' + self.docstring + '\n"""')
        return "\n".join(parts)


@dataclass
class GherkinExamples:
    name: str = ""
    tags: List[str] = field(default_factory=list)
    header: Optional[List[str]] = None
    rows: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class GherkinScenario:
    name: str
    tags: List[str] = field(default_factory=list)
    description: str = ""
    steps: List[GherkinStep] = field(default_factory=list)
    is_outline: bool = False
    examples: List[GherkinExamples] = field(default_factory=list)
    rule_name: str = ""


@dataclass
class GherkinFeature:
    file: str
    name: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    background: List[GherkinStep] = field(default_factory=list)
    scenarios: List[GherkinScenario] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser (line-based state machine, stdlib only)
# ---------------------------------------------------------------------------

def _split_table_row(line: str) -> List[str]:
    """Splits a Gherkin data-table row into cells, honoring \\| escapes."""
    escaped = line.strip().replace("\\|", "\x00")
    if escaped.startswith("|"):
        escaped = escaped[1:]
    if escaped.endswith("|"):
        escaped = escaped[:-1]
    return [cell.replace("\x00", "|").strip() for cell in escaped.split("|")]


def _dedent_doc_line(line: str, indent: int) -> str:
    """Dedents a doc-string content line by the opening delimiter's indent
    (per Gherkin spec); blank lines collapse to empty strings."""
    if not line.strip():
        return ""
    if len(line) >= indent and line[:indent].strip() == "":
        return line[indent:]
    return line.lstrip()


class GherkinParser:
    """Parses English Gherkin text into a GherkinFeature model."""

    def __init__(self):
        self.errors: List[str] = []

    def _err(self, message: str) -> None:
        self.errors.append(message)

    def parse(self, text: str, filename: str = "<memory>") -> GherkinFeature:
        feature = GherkinFeature(file=filename)
        pending_tags: List[str] = []
        rule_tags: List[str] = []
        rule_name = ""
        container: Optional[str] = None  # None | "background" | "scenario"
        current_scenario: Optional[GherkinScenario] = None
        current_examples: Optional[GherkinExamples] = None
        examples_mode = False
        last_step: Optional[GherkinStep] = None
        last_concrete: Optional[str] = None
        in_docstring = False
        doc_delim = '"""'
        doc_type = ""
        doc_indent = 0
        doc_lines: List[str] = []

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for line_no, raw in enumerate(lines, 1):
            if in_docstring:
                if raw.strip() == doc_delim:
                    if last_step is not None:
                        last_step.docstring = "\n".join(doc_lines)
                        last_step.docstring_type = doc_type
                    else:
                        self._err(f"line {line_no}: doc string closed but no step is open")
                    in_docstring = False
                    doc_lines = []
                    doc_type = ""
                else:
                    doc_lines.append(_dedent_doc_line(raw, doc_indent))
                continue

            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue  # blank line or comment (incl. `# language:` header)

            if stripped.startswith("@"):
                pending_tags.extend(stripped.split())
                continue

            # Doc string openers attach to the most recent step.
            if stripped.startswith('"""') or stripped.startswith("```"):
                if last_step is None or examples_mode:
                    self._err(f"line {line_no}: doc string outside a step")
                else:
                    in_docstring = True
                    doc_delim = stripped[:3]
                    doc_type = stripped[3:].strip()
                    doc_indent = len(raw) - len(raw.lstrip())
                continue

            m = re.match(r"Feature\s*:\s*(.*)", stripped)
            if m:
                feature.name = m.group(1).strip()
                feature.tags = pending_tags
                pending_tags = []
                container = None
                examples_mode = False
                continue

            m = re.match(r"Rule\s*:\s*(.*)", stripped)
            if m:
                rule_name = m.group(1).strip()
                rule_tags = pending_tags
                pending_tags = []
                container = None
                examples_mode = False
                continue

            m = re.match(r"Background\s*:\s*(.*)", stripped)
            if m:
                container = "background"
                examples_mode = False
                last_step = None
                last_concrete = None
                pending_tags = []  # Background tags are not modeled
                continue

            m = re.match(r"Scenario\s+(?:Outline|Template)\s*:\s*(.*)", stripped)
            if m:
                container = "scenario"
                examples_mode = False
                last_step = None
                last_concrete = None
                current_scenario = GherkinScenario(
                    name=m.group(1).strip(),
                    tags=feature.tags + rule_tags + pending_tags,
                    is_outline=True,
                    rule_name=rule_name,
                )
                feature.scenarios.append(current_scenario)
                pending_tags = []
                continue

            m = re.match(r"Scenario\s*:\s*(.*)", stripped)
            if m:
                container = "scenario"
                examples_mode = False
                last_step = None
                last_concrete = None
                current_scenario = GherkinScenario(
                    name=m.group(1).strip(),
                    tags=feature.tags + rule_tags + pending_tags,
                    rule_name=rule_name,
                )
                feature.scenarios.append(current_scenario)
                pending_tags = []
                continue

            m = re.match(r"Examples\s*:\s*(.*)", stripped)
            if m:
                if current_scenario is None or not current_scenario.is_outline:
                    self._err(f"line {line_no}: Examples block without a Scenario Outline")
                else:
                    current_examples = GherkinExamples(name=m.group(1).strip(), tags=pending_tags)
                    current_scenario.examples.append(current_examples)
                    examples_mode = True
                pending_tags = []
                continue

            m = re.match(r"(Given|When|Then|And|But)\s+(.*)", stripped)
            if m:
                raw_kw, step_text = m.group(1), m.group(2).strip()
                if raw_kw in CONCRETE_STEP_KEYWORDS:
                    concrete = raw_kw
                    role = STEP_ROLES[concrete]
                else:
                    if last_concrete is None:
                        self._err(f"line {line_no}: '{raw_kw}' before any Given/When/Then")
                        concrete = "Given"
                        role = "arrange"
                    else:
                        concrete = last_concrete
                        role = STEP_ROLES[concrete]
                step = GherkinStep(keyword=concrete, raw_keyword=raw_kw, text=step_text, role=role)
                if container == "background":
                    feature.background.append(step)
                elif container == "scenario" and current_scenario is not None:
                    current_scenario.steps.append(step)
                else:
                    self._err(f"line {line_no}: step outside Scenario/Background - '{stripped}'")
                last_step = step
                last_concrete = concrete
                continue

            if stripped.startswith("|"):
                cells = _split_table_row(stripped)
                if examples_mode and current_examples is not None:
                    if current_examples.header is None:
                        current_examples.header = cells
                    else:
                        if len(cells) != len(current_examples.header):
                            self._err(
                                f"line {line_no}: example row has {len(cells)} cells, "
                                f"header has {len(current_examples.header)}"
                            )
                        else:
                            current_examples.rows.append(dict(zip(current_examples.header, cells)))
                elif last_step is not None:
                    last_step.table_rows.append(cells)
                else:
                    self._err(f"line {line_no}: data table outside a step or Examples block")
                continue

            # Prose: attach to the current container description.
            if container == "scenario" and current_scenario is not None:
                current_scenario.description = (current_scenario.description + " " + stripped).strip()
            elif container is None:
                feature.description = (feature.description + " " + stripped).strip()

        if in_docstring:
            self._err("unterminated doc string at end of file")

        return feature


# ---------------------------------------------------------------------------
# Scenario Outline expansion
# ---------------------------------------------------------------------------

def _substitute_param(text: str, row: Dict[str, str]) -> str:
    for key, value in row.items():
        text = text.replace("<" + key + ">", value)
    return text


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "unnamed"


def expand_feature(feature: GherkinFeature, errors: List[str]) -> List[Dict[str, Any]]:
    """Expands Scenario Outlines into concrete cases (one per Examples row)."""
    seen_ids: Dict[str, int] = {}
    cases: List[Dict[str, Any]] = []

    def register(case_id: str) -> str:
        if case_id in seen_ids:
            seen_ids[case_id] += 1
            return f"{case_id}-{seen_ids[case_id]}"
        seen_ids[case_id] = 1
        return case_id

    for scenario in feature.scenarios:
        base_steps = feature.background + scenario.steps
        if not scenario.is_outline:
            cases.append({
                "id": register(f"{_slug(feature.name)}--{_slug(scenario.name)}"),
                "name": scenario.name,
                "tags": scenario.tags,
                "steps": copy.deepcopy(base_steps),
                "scenario": scenario.name,
                "row": None,
                "errors": [],
            })
            continue

        if not scenario.examples:
            errors.append(f"Scenario Outline '{scenario.name}' has no Examples block")
            continue

        for example_block in scenario.examples:
            if example_block.header is None:
                errors.append(f"Scenario Outline '{scenario.name}' has an Examples block without a table")
                continue
            for row_no, row in enumerate(example_block.rows, 1):
                case_errors: List[str] = []
                expanded: List[GherkinStep] = []
                for step in base_steps:
                    text = _substitute_param(step.text, row)
                    doc = _substitute_param(step.docstring, row) if step.docstring is not None else None
                    table = [
                        [_substitute_param(cell, row) for cell in row_cells]
                        for row_cells in step.table_rows
                    ]
                    leftover = PARAM_PATTERN.search(text)
                    if leftover:
                        case_errors.append(
                            f"unresolved parameter <{leftover.group(1)}> in step '{step.text}' "
                            f"(not found in Examples header)"
                        )
                    expanded.append(GherkinStep(
                        keyword=step.keyword,
                        raw_keyword=step.raw_keyword,
                        text=text,
                        role=step.role,
                        docstring=doc,
                        table_rows=table,
                    ))
                row_tag = f"@row-{row_no}"
                cases.append({
                    "id": register(f"{_slug(feature.name)}--{_slug(scenario.name)}--row-{row_no}"),
                    "name": f"{scenario.name} [{row_tag}]",
                    "tags": scenario.tags + [row_tag],
                    "steps": expanded,
                    "scenario": scenario.name,
                    "row": row_no,
                    "errors": case_errors,
                })
    return cases


# ---------------------------------------------------------------------------
# Deterministic NL -> Universal IR mapping (keyword heuristics, 0 LLM tokens)
# ---------------------------------------------------------------------------

def _first_quoted(text: str) -> Optional[str]:
    m = QUOTE_PATTERN.search(text)
    if m:
        return m.group(1) if m.group(1) is not None else m.group(2)
    return None


def _after_word(text: str, words: tuple) -> Optional[str]:
    for w in words:
        m = re.search(r"\b" + w + r"\s+(.+)$", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def map_step_to_ir(step: GherkinStep) -> StepIR:
    """Maps a Gherkin step onto a StepIR action using deterministic rules.

    Best-effort by design: unrecognizable phrasing falls back to CUSTOM_CALL
    with the original text preserved in `description`.
    """
    text = step.text
    lower = text.lower()
    quoted = _first_quoted(text)
    role = step.role

    if role == "assert":
        if re.search(r"\burl\b", lower) and re.search(r"\b(should|must|is|contains)\b", lower):
            expected = quoted or (URL_PATTERN.search(text).group(0) if URL_PATTERN.search(text) else text)
            return StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.URL_CONTAINS,
                          expected=expected, description=text)
        # A quoted expectation ("should see "Order Confirmed"") is a text
        # assertion - stronger than a bare visibility check, so it wins.
        if quoted and re.search(r"\b(see|sees|contains|shows|displays|message|text)\b", lower):
            return StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.CONTAINS_TEXT,
                          target=None, expected=quoted, description=text)
        if re.search(r"\b(see|sees|visible|displayed|shown|appears|exists)\b", lower):
            return StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.VISIBLE,
                          target=quoted, expected=quoted, description=text)
        if quoted:
            return StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.CONTAINS_TEXT,
                          expected=quoted, description=text)
        return StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.VISIBLE,
                      description=text)

    if role == "act":
        # Verbs are matched anywhere in the sentence: Gherkin steps commonly
        # start with a subject ("the user clicks ..."), including 3rd person.
        if re.search(r"\b(navigates?|go(?:es)?\s+to|opens?|visits?|launch(?:es)?|browse(?:s)?)\b", lower):
            url_match = URL_PATTERN.search(text)
            return StepIR(action=ActionType.GOTO, value=url_match.group(0) if url_match else quoted,
                          description=text)
        if re.search(r"\b(fill(?:s)?\s+in|enter(?:s)?|type(?:s)?|input(?:s)?|provide(?:s)?|set(?:s)?)\b", lower):
            quotes = [
                m.group(1) if m.group(1) is not None else m.group(2)
                for m in QUOTE_PATTERN.finditer(text)
            ]
            value = quotes[0] if quotes else None
            if len(quotes) >= 2:
                target = quotes[1]
            else:
                target = _after_word(text, ("into", "in the", "in", "on"))
            return StepIR(action=ActionType.FILL, target=target, value=value, description=text)
        if re.search(r"\b(select|choose|pick)", lower):
            target = _after_word(text, ("from", "in"))
            return StepIR(action=ActionType.SELECT, target=target, value=quoted, description=text)
        if re.search(r"\b(uncheck|untick|deselect|clear)", lower):
            return StepIR(action=ActionType.UNCHECK, target=quoted, description=text)
        if re.search(r"\b(check|tick)", lower):
            return StepIR(action=ActionType.CHECK, target=quoted, description=text)
        if re.search(r"\b(hover|mouse\s?over)", lower):
            return StepIR(action=ActionType.HOVER, target=quoted, description=text)
        if re.search(r"\bwait", lower):
            return StepIR(action=ActionType.WAIT, wait_strategy=WaitStrategy.AUTO, description=text)
        if re.search(r"\b(double.?click|dblclick)", lower):
            return StepIR(action=ActionType.DBLCLICK, target=quoted, description=text)
        if re.search(r"\b(click|tap|press|submit)", lower):
            target = quoted or _after_word(text, ("on the", "on", "the"))
            return StepIR(action=ActionType.CLICK, target=target, description=text)

    # arrange (Given) and any unmapped phrasing -> explicit custom call
    return StepIR(action=ActionType.CUSTOM_CALL, description=f"{step.keyword} {text}")


def build_test_case_ir(case: Dict[str, Any]) -> TestCaseIR:
    steps = [map_step_to_ir(s) for s in case["steps"]]
    return TestCaseIR(
        id=case["id"],
        title=case["name"],
        steps=steps,
        tags=case["tags"],
        description=case.get("description", ""),
    )


# ---------------------------------------------------------------------------
# "Proven vs owed" coverage-gap analysis (idea re-expressed from Kane CLI)
# ---------------------------------------------------------------------------

def analyze_gaps(feature: GherkinFeature, cases: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    gaps: List[Dict[str, str]] = []

    for case in cases:
        if not any(s.role == "assert" for s in case["steps"]):
            gaps.append({
                "severity": "WARNING",
                "rule": "G1-MISSING_ASSERTION",
                "target": case["id"],
                "message": "Case has no Then/assert step - add an observable outcome assertion.",
            })

    has_negative = any(
        NEGATIVE_SIGNAL_PATTERN.search(" ".join([sc.name] + sc.tags)) for sc in feature.scenarios
    )
    if not has_negative:
        gaps.append({
            "severity": "WARNING",
            "rule": "G2-MISSING_NEGATIVE_PATH",
            "target": feature.name or feature.file,
            "message": "No negative/invalid scenario detected - add at least one "
                       "(e.g. invalid input, unauthorized access, empty state).",
        })

    for scenario in feature.scenarios:
        if not scenario.is_outline:
            continue
        for block in scenario.examples:
            if block.header is not None and len(block.rows) < 2:
                gaps.append({
                    "severity": "WARNING",
                    "rule": "G3-THIN_EXAMPLES",
                    "target": scenario.name,
                    "message": f"Examples table has {len(block.rows)} row(s) - add boundary and "
                               "negative rows (empty, max length, special chars).",
                })

    return gaps


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def emit_markdown_plan(feature: GherkinFeature, cases: List[Dict[str, Any]],
                       gaps: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    lines.append(f"# BDD Test Plan - {feature.name or os.path.basename(feature.file)}")
    lines.append("")
    if feature.tags:
        lines.append("**Tags:** " + " ".join(feature.tags))
    if feature.description:
        lines.append(f"> {feature.description}")
    lines.append(f"- Source: `{feature.file}`")
    lines.append(f"- Scenarios: {len(feature.scenarios)} | Expanded cases: {len(cases)}")
    lines.append("")

    if feature.background:
        lines.append("## Background")
        for step in feature.background:
            lines.append(f"- **{step.keyword}** {step.display_text()}")
        lines.append("")

    for scenario in feature.scenarios:
        kind = "Scenario Outline" if scenario.is_outline else "Scenario"
        heading = f"## {kind}: {scenario.name}"
        if scenario.rule_name:
            heading += f"  (Rule: {scenario.rule_name})"
        lines.append(heading)
        if scenario.tags:
            lines.append(" ".join(scenario.tags))
        lines.append("")
        lines.append("| # | Step | Role | Mapped Action |")
        lines.append("| :--- | :--- | :--- | :--- |")
        case_for_scenario = next((c for c in cases if c["scenario"] == scenario.name), None)
        step_source = case_for_scenario["steps"] if case_for_scenario else scenario.steps
        for idx, step in enumerate(step_source, 1):
            ir = map_step_to_ir(step)
            lines.append(f"| {idx} | **{step.keyword}** {step.text.splitlines()[0]} | {step.role} | `{ir.action.value}` |")
        if scenario.is_outline:
            for block in scenario.examples:
                lines.append("")
                label = f"Examples: {block.name}" if block.name else "Examples"
                tags = " " + " ".join(block.tags) if block.tags else ""
                lines.append(f"**{label}**{tags}")
                if block.header:
                    lines.append("")
                    lines.append("| " + " | ".join(block.header) + " |")
                    lines.append("|" + "---|" * len(block.header))
                    for row in block.rows:
                        lines.append("| " + " | ".join(row[h] for h in block.header) + " |")
        lines.append("")

    lines.append("## Coverage Gaps (proven vs owed)")
    if gaps:
        for gap in gaps:
            lines.append(f"- **[{gap['severity']}] {gap['rule']}** `{gap['target']}` - {gap['message']}")
    else:
        lines.append("- No gaps detected.")
    lines.append("")
    return "\n".join(lines)


def compile_feature(path: str) -> Dict[str, Any]:
    """Parses, expands, maps and audits one .feature file into a result dict."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    parser = GherkinParser()
    feature = parser.parse(text, filename=os.path.relpath(path, REPO_ROOT)
                           if path.startswith(REPO_ROOT) else path)
    errors = list(parser.errors)

    cases = expand_feature(feature, errors)
    error_count = sum(len(c["errors"]) for c in cases) + len(errors)
    gaps = analyze_gaps(feature, cases)

    mapped = {c["id"]: [map_step_to_ir(s).to_dict() for s in c["steps"]] for c in cases}
    total = len(cases)
    invalid = sum(1 for c in cases if c["errors"])
    health_score = 100.0 if total == 0 else max(0.0, round(((total - invalid) / total) * 100, 1))

    return {
        "timestamp": datetime.now().isoformat(),
        "file": feature.file,
        "feature": feature.name,
        "tags": feature.tags,
        "totals": {
            "scenarios": len(feature.scenarios),
            "expanded_cases": total,
            "steps": sum(len(c["steps"]) for c in cases),
            "invalid_cases": invalid,
        },
        "errors": errors + [f"{c['id']}: {e}" for c in cases for e in c["errors"]],
        "gaps": gaps,
        "cases": [
            {
                "id": c["id"],
                "name": c["name"],
                "tags": c["tags"],
                "steps": mapped[c["id"]],
                "valid": not c["errors"],
            }
            for c in cases
        ],
        "health_score_pct": health_score,
        "markdown_plan": emit_markdown_plan(feature, cases, gaps),
        "_feature": feature,
        "_ir_cases": [
            {"id": c["id"], "ir": build_test_case_ir(c).to_dict()}
            for c in cases if not c["errors"]
        ],
    }


def run(target: str, as_json: bool = False, emit_ir: bool = False) -> int:
    if os.path.isfile(target):
        feature_files = [target]
    elif os.path.isdir(target):
        feature_files = sorted(glob.glob(os.path.join(target, "**", "*.feature"), recursive=True))
    else:
        print(f"{RED}[ERROR]{RESET} Target not found: {target}")
        return 1
    if not feature_files:
        print(f"{YELLOW}[WARN]{RESET} No .feature files discovered under: {target}")
        return 1

    results = [compile_feature(p) for p in feature_files]
    all_errors = [e for r in results for e in r["errors"]]
    total_cases = sum(r["totals"]["expanded_cases"] for r in results)
    total_gaps = sum(len(r["gaps"]) for r in results)

    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}      GHERKIN BDD SUITE COMPILER (Natural-Language Test Ingestion)      {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}")
    print(f"  Feature Files          : {len(feature_files)}")
    print(f"  Expanded Test Cases    : {GREEN if total_cases else RED}{total_cases}{RESET}")
    print(f"  Coverage Gap Warnings  : {YELLOW if total_gaps else GREEN}{total_gaps}{RESET}")
    print(f"  Errors                 : {RED if all_errors else GREEN}{len(all_errors)}{RESET}")
    scores = [r["health_score_pct"] for r in results if r["totals"]["expanded_cases"]]
    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    print(f"  Case Validity Score    : {GREEN if avg == 100 else YELLOW}{avg}%{RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    for r in results:
        for e in r["errors"]:
            print(f"  - [{RED}ERROR{RESET}] {e}")
        for g in r["gaps"]:
            print(f"  - [{YELLOW}{g['severity']}{RESET}] {g['rule']} {g['target']} - {g['message']}")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    persist = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "features": persist}, f,
                  indent=2, ensure_ascii=False)
    print(f"Detailed audit saved to: {OUTPUT_JSON}\n")

    if emit_ir:
        ir_payload = [case["ir"] for r in results for case in r["_ir_cases"]]
        print(json.dumps(ir_payload, indent=2, ensure_ascii=False))

    if as_json:
        print(json.dumps(persist, indent=2, ensure_ascii=False))

    return 1 if all_errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gherkin BDD Suite Compiler - compiles .feature files into a test matrix, "
                    "Universal IR and coverage-gap report (0 LLM tokens).")
    parser.add_argument("target", help="A .feature file or a directory containing .feature files")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report to stdout")
    parser.add_argument("--emit-ir", action="store_true",
                        help="Print hub Universal IR (TestCaseIR) dicts for the omni pipeline")
    args = parser.parse_args()
    return run(args.target, as_json=args.json, emit_ir=args.emit_ir)


if __name__ == "__main__":
    sys.exit(main())
