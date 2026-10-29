#!/usr/bin/env python3
"""
Environment & Secret Decoupling Engine
---------------------------------------
Scans automation test suites (Playwright, Katalon, Selenium, Cypress) for hardcoded
environment values (URLs, credentials, bearer tokens, DB connection strings).
Decouples them into standardized environment configurations:
  1. config/profiles/env.default.json
  2. .env.example
  3. Replaces hardcoded literals in AST/sources with process.env / os.getenv references.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Regex patterns for sensitive literals
URL_PATTERN = re.compile(r'https?://(?!www\.w3\.org|json-schema\.org|schemas\.xmlsoap\.org)[a-zA-Z0-9.\-]+(?::\d+)?(?:/[a-zA-Z0-9_\.\-~%!$&\'()*+,;=:@]*)*')
PASSWORD_PATTERN = re.compile(r'(?i)(?:password|secret|pwd|pass|client_secret)\s*[:=]\s*["\']([^"\']{4,})["\']')
TOKEN_PATTERN = re.compile(r'(?i)\b(?:Bearer\s+([A-Za-z0-9_\-\.]{16,})|api[_\-]?key\s*[:=]\s*["\']([A-Za-z0-9_\-]{16,})["\'])')
DB_URL_PATTERN = re.compile(r'(?:mongodb|mysql|postgres|postgresql|jdbc:[a-z0-9]+)://[^\s"\'<>]+')


class ConfigDecoupler:
    """Automated configuration and credentials decoupling engine."""

    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)
        self.decoupled_configs: Dict[str, Any] = {
            "APP_BASE_URL": "http://localhost:3000",
            "TEST_USER_USERNAME": "test_user@example.com",
            "TEST_USER_PASSWORD": "TestPassword123!",
            "API_AUTH_TOKEN": "mock_auth_token_secret"
        }
        self.findings: List[Dict[str, Any]] = []

    def scan(self) -> List[Dict[str, Any]]:
        """Scans the target directory for hardcoded URLs, credentials, and secrets."""
        extensions = {".ts", ".js", ".groovy", ".java", ".py", ".json"}
        exclude_dirs = {"node_modules", ".git", ".gradle", "build", "dist", "__pycache__", "config"}

        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file_name)
                    self._scan_file(file_path)

        return self.findings

    def _scan_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return

        rel_path = os.path.relpath(file_path, self.target_dir).replace("\\", "/")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("//") or line.strip().startswith("#"):
                continue

            # 1. URLs
            for url in URL_PATTERN.findall(line):
                key = "APP_BASE_URL"
                self.decoupled_configs[key] = url
                self.findings.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "URL",
                    "key": key,
                    "literal": url,
                    "replacement": f"process.env.{key} || '{url}'"
                })

            # 2. Passwords
            for pwd in PASSWORD_PATTERN.findall(line):
                key = "TEST_USER_PASSWORD"
                self.decoupled_configs[key] = pwd
                self.findings.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "PASSWORD",
                    "key": key,
                    "literal": pwd,
                    "replacement": f"process.env.{key}"
                })

            # 3. Tokens
            for t_match in TOKEN_PATTERN.findall(line):
                token = t_match[0] or t_match[1]
                if token:
                    key = "API_AUTH_TOKEN"
                    self.decoupled_configs[key] = token
                    self.findings.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "TOKEN",
                        "key": key,
                        "literal": token,
                        "replacement": f"process.env.{key}"
                    })

            # 4. DB URLs
            for db_url in DB_URL_PATTERN.findall(line):
                key = "DATABASE_URL"
                self.decoupled_configs[key] = db_url
                self.findings.append({
                    "file": rel_path,
                    "line": idx,
                    "type": "DATABASE_URL",
                    "key": key,
                    "literal": db_url,
                    "replacement": f"process.env.{key}"
                })

    def export_configs(self, output_dir: str = None) -> Tuple[str, str]:
        """Generates env.default.json and .env.example configuration files."""
        out_base = output_dir or os.path.join(self.target_dir, "config", "profiles")
        os.makedirs(out_base, exist_ok=True)

        json_path = os.path.join(out_base, "env.default.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.decoupled_configs, f, indent=2)

        env_example_path = os.path.join(self.target_dir, ".env.example")
        env_lines = [
            "# ===================================================================",
            "# AUTO-GENERATED ENVIRONMENT CONFIGURATION TEMPLATE",
            "# Decoupled via tools/config_decoupler.py",
            "# ===================================================================",
            ""
        ]
        for k, v in self.decoupled_configs.items():
            env_lines.append(f"{k}={v}")

        with open(env_example_path, "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines) + "\n")

        return json_path, env_example_path

    def apply_decoupling(self) -> int:
        """Replaces detected hardcoded literals with decoupled environment references in-place."""
        modified_count = 0
        grouped_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for f in self.findings:
            grouped_by_file.setdefault(f["file"], []).append(f)

        for rel_file, items in grouped_by_file.items():
            full_path = os.path.join(self.target_dir, rel_file)
            if not os.path.exists(full_path):
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as fp:
                    content = fp.read()
            except Exception:
                continue

            new_content = content
            ext = os.path.splitext(full_path)[1].lower()

            for it in items:
                lit = it["literal"]
                key = it["key"]

                if ext in {".ts", ".js"}:
                    replacement = f"process.env.{key} || '{lit}'" if it["type"] == "URL" else f"process.env.{key}"
                elif ext == ".py":
                    replacement = f"os.getenv('{key}', '{lit}')" if it["type"] == "URL" else f"os.getenv('{key}')"
                elif ext in {".groovy", ".java"}:
                    replacement = f"(System.getenv('{key}') ?: '{lit}')" if it["type"] == "URL" else f"System.getenv('{key}')"
                else:
                    replacement = f"${{{key}}}"

                # Only replace quotes wrapped around literal
                new_content = new_content.replace(f"'{lit}'", replacement)
                new_content = new_content.replace(f'"{lit}"', replacement)

            if new_content != content:
                with open(full_path, "w", encoding="utf-8") as fp:
                    fp.write(new_content)
                modified_count += 1

        return modified_count


def main():
    parser = argparse.ArgumentParser(description="Automated Environment & Secret Decoupling Engine")
    parser.add_argument("target", nargs="?", default=os.getcwd(), help="Target project root directory")
    parser.add_argument("--fix", action="store_true", help="Apply decoupling modifications in-place to files")
    parser.add_argument("--out-dir", default=None, help="Output directory for config profiles")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    decoupler = ConfigDecoupler(args.target)
    findings = decoupler.scan()
    json_path, env_path = decoupler.export_configs(args.out_dir)

    if args.fix:
        modified = decoupler.apply_decoupling()

    if args.json:
        print(json.dumps({
            "target": decoupler.target_dir,
            "total_findings": len(findings),
            "findings": findings,
            "config_json": json_path,
            "env_example": env_path
        }, indent=2))
    else:
        print("\n======================================================================")
        print("      ENVIRONMENT & SECRET DECOUPLING ENGINE (HERMETIC CONFIG)       ")
        print("======================================================================")
        print(f"📁 Target Scope        : {decoupler.target_dir}")
        print(f"🔍 Hardcoded Findings  : {len(findings)} literals detected")
        print(f"📄 Decoupled Config    : {json_path}")
        print(f"📄 Environment Template: {env_path}")
        print("======================================================================\n")

        for f in findings[:8]:
            print(f"  • [{f['type']}] {f['file']}:{f['line']} -> {f['key']}")
            print(f"    Literal    : {f['literal']}")
            print(f"    Replacement: {f['replacement']}\n")

        if len(findings) > 8:
            print(f"  ... and {len(findings) - 8} more literals decoupled.\n")

        if args.fix:
            print(f"✅ [IN-PLACE REFACTOR COMPLETED] {modified} files updated with environment variables.")
        else:
            print("💡 Run with '--fix' to apply environment variable replacements automatically in-place.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
