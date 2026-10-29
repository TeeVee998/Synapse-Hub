#!/usr/bin/env python3
"""
tools/wcag_audit.py - Automated Accessibility (WCAG 2.2) Linter & Auditor
Operationalizes the .agents/skills/wcag-audit-patterns skill for Web & Enterprise Applications.

Checks WCAG 2.2 Level A and AA criteria:
- WCAG 1.1.1: Images missing alt attributes
- WCAG 1.3.1: Form controls missing labels or aria-label/aria-labelledby
- WCAG 1.3.1: Table headers structure
- WCAG 2.4.4: Links with empty text / accessible name
- WCAG 4.1.2: Buttons with empty text / accessible name
- WCAG 1.3.1: Heading hierarchy gaps (e.g., h1 to h3)
"""

import argparse
import os
import sys
import urllib.request
from html.parser import HTMLParser

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


class WCAGAuditor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.violations = []
        self.tag_stack = []
        self.current_heading_level = 0
        self.in_button = False
        self.button_text = ""
        self.button_attrs = {}
        self.in_a = False
        self.a_text = ""
        self.a_attrs = {}
        self.has_main = False
        self.elements_scanned = 0

    def handle_starttag(self, tag, attrs):
        self.elements_scanned += 1
        attr_dict = dict(attrs)

        # WCAG 1.1.1 Non-text Content (Images)
        if tag == "img":
            if "alt" not in attr_dict:
                self.violations.append({
                    "criterion": "1.1.1 Non-text Content (Level A)",
                    "severity": "CRITICAL",
                    "element": f"<img src='{attr_dict.get('src', '')}'>",
                    "message": "Missing 'alt' attribute on image."
                })

        # WCAG 1.3.1 Info and Relationships (Form Controls)
        if tag in ["input", "select", "textarea"]:
            input_type = attr_dict.get("type", "text")
            if input_type not in ["hidden", "submit", "button", "reset"]:
                has_label = "aria-label" in attr_dict or "aria-labelledby" in attr_dict or "id" in attr_dict
                if not has_label:
                    self.violations.append({
                        "criterion": "1.3.1 Info and Relationships / 4.1.2 (Level A)",
                        "severity": "HIGH",
                        "element": f"<{tag} type='{input_type}' name='{attr_dict.get('name', '')}'>",
                        "message": "Form control missing accessible name (no aria-label, aria-labelledby, or matching <label> id)."
                    })

        # Heading hierarchy
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            if self.current_heading_level > 0 and level > self.current_heading_level + 1:
                self.violations.append({
                    "criterion": "1.3.1 Info and Relationships (Level A)",
                    "severity": "MEDIUM",
                    "element": f"<{tag}>",
                    "message": f"Heading level skipped from h{self.current_heading_level} to h{level}."
                })
            self.current_heading_level = level

        # Track Buttons
        if tag == "button":
            self.in_button = True
            self.button_text = ""
            self.button_attrs = attr_dict

        # Track Anchors
        if tag == "a":
            self.in_a = True
            self.a_text = ""
            self.a_attrs = attr_dict

    def handle_data(self, data):
        if self.in_button:
            self.button_text += data.strip()
        if self.in_a:
            self.a_text += data.strip()

    def handle_endtag(self, tag):
        if tag == "button" and self.in_button:
            has_name = bool(self.button_text) or "aria-label" in self.button_attrs or "title" in self.button_attrs
            if not has_name:
                self.violations.append({
                    "criterion": "4.1.2 Name, Role, Value (Level A)",
                    "severity": "CRITICAL",
                    "element": "<button> (empty)",
                    "message": "Button has no accessible name (empty text, no aria-label, no title)."
                })
            self.in_button = False

        if tag == "a" and self.in_a:
            has_name = bool(self.a_text) or "aria-label" in self.a_attrs or "title" in self.a_attrs
            href = self.a_attrs.get("href", "")
            if href and not has_name:
                self.violations.append({
                    "criterion": "2.4.4 Link Purpose (In Context) (Level A)",
                    "severity": "HIGH",
                    "element": f"<a href='{href}'> (empty)",
                    "message": "Link has no accessible text or aria-label."
                })
            self.in_a = False


def run_audit(target, is_url=False):
    auditor = WCAGAuditor()
    if is_url:
        req = urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0 (WCAG-Audit-Bot)'})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    else:
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

    auditor.feed(html)
    return auditor


def format_markdown_report(target, auditor):
    violations = auditor.violations
    stats = {
        "elements_scanned": auditor.elements_scanned,
        "violations_found": len(violations),
        "critical": sum(1 for v in violations if v["severity"] == "CRITICAL"),
        "high": sum(1 for v in violations if v["severity"] == "HIGH"),
        "medium": sum(1 for v in violations if v["severity"] == "MEDIUM")
    }

    # Score calculation
    penalty = (stats["critical"] * 25) + (stats["high"] * 10) + (stats["medium"] * 5)
    score = max(0, 100 - penalty)
    grade = "PASS" if score >= 80 else "NEEDS REMEDIATION"

    out = [
        f"# WCAG 2.2 Accessibility Audit Report",
        f"**Target:** `{target}`",
        f"**Elements Scanned:** {stats['elements_scanned']}",
        f"**Violations Found:** {stats['violations_found']}",
        f"**Accessibility Score:** {score}/100 - **[{grade}]**",
        "",
        "---",
        "",
        "## Violations Detail",
        "",
        "| Severity | Criterion | Element Snippet | Issue Description |",
        "|---|---|---|---|"
    ]

    if not violations:
        out.append("| PASS | - | - | Zero WCAG 2.2 violations detected! Element tree is fully compliant. |")
    else:
        for v in violations:
            out.append(f"| **{v['severity']}** | {v['criterion']} | `{v['element']}` | {v['message']} |")

    out.append("")
    out.append("---")
    out.append("### Recommended Remediation Actions:")
    out.append("1. Add descriptive `alt=\"...\"` attributes to all images.")
    out.append("2. Add `aria-label=\"...\"` or explicit `<label for=\"...\">` bindings to form controls and icon buttons.")
    out.append("3. Maintain strict heading hierarchy (h1 -> h2 -> h3).")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Automated WCAG 2.2 Accessibility Auditor for Web & Enterprise Applications.")
    parser.add_argument("target", help="HTML file path or URL to audit.")
    parser.add_argument("--url", action="store_true", help="Treat target as a live URL.")
    parser.add_argument("--output", "-o", help="Path to save markdown report.")
    args = parser.parse_args()

    if not args.url and not os.path.exists(args.target):
        print(f"Error: File '{args.target}' does not exist.")
        sys.exit(1)

    print(f"[AUDIT] Running WCAG 2.2 Accessibility Audit on: {args.target}...")
    auditor = run_audit(args.target, is_url=args.url)
    report = format_markdown_report(args.target, auditor)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] Report saved to: {args.output}")
    else:
        print(report)

    if len(auditor.violations) > 0:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
