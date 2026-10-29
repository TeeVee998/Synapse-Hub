#!/usr/bin/env python3
"""
Omni-Parser: Universal Polyglot AST & Structure Parser
------------------------------------------------------
Zero-Token deterministic parser supporting Java, TypeScript/JavaScript,
Python, Groovy (Katalon), and C#.
Extracts Page Classes, Locators, Action Methods, and Test Cases into
the Universal Intermediate Representation (universal_ir.ProjectIR).
"""

import os
import re
import sys
from typing import Dict, List, Optional, Tuple

try:
    from tools.universal_ir import (
        ProjectIR, PageClassIR, TestCaseIR, MethodIR, StepIR, LocatorIR,
        ActionType, LocatorStrategy, AssertionType, WaitStrategy
    )
except ImportError:
    from universal_ir import (
        ProjectIR, PageClassIR, TestCaseIR, MethodIR, StepIR, LocatorIR,
        ActionType, LocatorStrategy, AssertionType, WaitStrategy
    )


def extract_quoted_string(match_groups: Tuple[Optional[str], Optional[str]]) -> str:
    """Helper to return the unescaped string from either double-quote or single-quote match."""
    g1, g2 = match_groups
    val = g1 if g1 else (g2 if g2 else "")
    return val.replace(r"\'", "'").replace(r'\"', '"')


class OmniParser:
    """Universal Zero-Token Polyglot Parser for Automation Codebases."""

    @staticmethod
    def detect_language_and_framework(file_path: str, content: str) -> Tuple[str, str]:
        ext = os.path.splitext(file_path)[1].lower()
        
        # Groovy / Katalon
        if ext == ".groovy":
            return "groovy", "katalon"

        # Java
        if ext == ".java":
            if "playwright" in content.lower():
                return "java", "playwright"
            if "restassured" in content.lower():
                return "java", "restassured"
            return "java", "selenium"

        # TypeScript / JavaScript
        if ext in [".ts", ".tsx", ".js", ".jsx"]:
            lang = "typescript" if "ts" in ext else "javascript"
            if "@playwright/test" in content or "page.locator" in content or "getByRole" in content:
                return lang, "playwright"
            if "cy." in content or "cypress" in content.lower():
                return lang, "cypress"
            if "webdriverio" in content.lower() or "browser.$" in content:
                return lang, "webdriverio"
            return lang, "playwright"

        # Python
        if ext == ".py":
            if "playwright" in content:
                return "python", "playwright"
            if "selenium" in content:
                return "python", "selenium"
            if "robot" in content.lower():
                return "python", "robot"
            return "python", "pytest"

        # C#
        if ext == ".cs":
            if "playwright" in content.lower():
                return "csharp", "playwright"
            return "csharp", "selenium"

        return "unknown", "generic"

    @classmethod
    def parse_file(cls, file_path: str) -> ProjectIR:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lang, framework = cls.detect_language_and_framework(file_path, content)
        basename = os.path.basename(file_path)
        project = ProjectIR(
            name=os.path.splitext(basename)[0],
            source_language=lang,
            source_framework=framework
        )

        if lang in ["typescript", "javascript"]:
            cls._parse_ts_js(content, project, framework)
        elif lang == "java":
            cls._parse_java(content, project, framework)
        elif lang == "groovy":
            cls._parse_groovy(content, project, framework)
        elif lang == "python":
            cls._parse_python(content, project, framework)
        elif lang == "csharp":
            cls._parse_csharp(content, project, framework)
        else:
            cls._parse_generic(content, project)

        return project

    # -------------------------------------------------------------------------
    # TypeScript / JavaScript Parser
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_ts_js(cls, content: str, project: ProjectIR, framework: str):
        class_match = re.search(r"class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?", content)
        page_name = class_match.group(1) if class_match else f"{project.name}Page"
        base_class = class_match.group(2) if (class_match and class_match.group(2)) else "BasePage"

        page = PageClassIR(name=page_name, base_class=base_class)
        locators: Dict[str, LocatorIR] = {}

        # 1. Playwright getByRole
        role_matches = re.finditer(
            r"(?:readonly\s+)?(?:this\.)?([A-Za-z0-9_$]+)\s*=\s*(?:this\.)?page\.getByRole\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*,\s*\{\s*name:\s*(?:\"([^\"]*)\"|'([^']*)')\s*\}\s*\)",
            content
        )
        for m in role_matches:
            loc_name = m.group(1)
            role_type = extract_quoted_string((m.group(2), m.group(3)))
            acc_name = extract_quoted_string((m.group(4), m.group(5)))
            locators[loc_name] = LocatorIR(name=loc_name, strategy=LocatorStrategy.ROLE, value=f"{role_type}[name='{acc_name}']")

        # 2. Playwright getByTestId
        tid_matches = re.finditer(
            r"(?:readonly\s+)?(?:this\.)?([A-Za-z0-9_$]+)\s*=\s*(?:this\.)?page\.getByTestId\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*\)",
            content
        )
        for m in tid_matches:
            loc_name = m.group(1)
            val = extract_quoted_string((m.group(2), m.group(3)))
            locators[loc_name] = LocatorIR(name=loc_name, strategy=LocatorStrategy.TEST_ID, value=val)

        # 3. Playwright getByLabel
        label_matches = re.finditer(
            r"(?:readonly\s+)?(?:this\.)?([A-Za-z0-9_$]+)\s*=\s*(?:this\.)?page\.getByLabel\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*\)",
            content
        )
        for m in label_matches:
            loc_name = m.group(1)
            val = extract_quoted_string((m.group(2), m.group(3)))
            locators[loc_name] = LocatorIR(name=loc_name, strategy=LocatorStrategy.LABEL, value=val)

        # 4. Playwright page.locator('...')
        loc_matches = re.finditer(
            r"""(?:readonly\s+)?(?:this\.)?([A-Za-z0-9_$]+)\s*=\s*(?:this\.)?page\.locator\(\s*(?:\"((?:[^"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)')\s*\)""",
            content
        )
        for m in loc_matches:
            loc_name = m.group(1)
            selector = extract_quoted_string((m.group(2), m.group(3)))
            strat = LocatorStrategy.XPATH if selector.startswith(("//", "(//")) else LocatorStrategy.CSS
            locators[loc_name] = LocatorIR(name=loc_name, strategy=strat, value=selector)

        page.locators = list(locators.values())

        # Methods
        method_blocks = re.findall(r"(async\s+)?([A-Za-z0-9_$]+)\s*\(([^)]*)\)\s*(?::\s*[^\{]+)?\s*\{([^}]+)\}", content, re.MULTILINE)
        for _, m_name, params_str, body in method_blocks:
            if m_name in ["constructor"]:
                continue
            params = [p.strip().split(":")[0].strip() for p in params_str.split(",") if p.strip()]
            steps = cls._extract_steps_from_body(body)
            page.methods.append(MethodIR(name=m_name, parameters=params, steps=steps))

        project.pages.append(page)

        # Test cases (Playwright `test(...)` or Cypress / Mocha `it(...)`)
        test_blocks = re.findall(
            r"(?:test|it)(?:\.only|\.skip)?\s*\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*,\s*(?:async\s*)?(?:\([^)]*\)|function\s*\([^)]*\))\s*=>?\s*\{([^}]+)\}",
            content,
            re.MULTILINE
        )
        for idx, (t_m1, t_m2, t_body) in enumerate(test_blocks, 1):
            t_title = t_m1 if t_m1 else t_m2
            steps = cls._extract_steps_from_body(t_body)
            project.test_cases.append(TestCaseIR(id=f"TC_{idx:03d}", title=t_title, steps=steps))

    # -------------------------------------------------------------------------
    # Java Parser (Selenium & Playwright)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_java(cls, content: str, project: ProjectIR, framework: str):
        class_match = re.search(r"public\s+class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?", content)
        page_name = class_match.group(1) if class_match else f"{project.name}Page"
        base_class = class_match.group(2) if (class_match and class_match.group(2)) else "BasePage"

        page = PageClassIR(name=page_name, base_class=base_class)
        locators: Dict[str, LocatorIR] = {}

        # 1. Selenium @FindBy annotations
        findby_matches = re.finditer(
            r"@FindBy\s*\(\s*([a-zA-Z0-9_]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')\s*\)\s*(?:(?:private|public|protected|static|final)\s+)*(?:WebElement|List<WebElement>)\s+([A-Za-z0-9_]+);",
            content
        )
        for m in findby_matches:
            by_type = m.group(1).lower()
            selector = extract_quoted_string((m.group(2), m.group(3)))
            var_name = m.group(4)
            strat = LocatorStrategy.XPATH if by_type == "xpath" else (LocatorStrategy.ID if by_type == "id" else LocatorStrategy.CSS)
            locators[var_name] = LocatorIR(name=var_name, strategy=strat, value=selector)

        # 2. By locators
        by_matches = re.finditer(
            r"(?:(?:private|public|protected|static|final)\s+)*By\s+([A-Za-z0-9_]+)\s*=\s*By\.([a-zA-Z0-9_]+)\s*\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*\);",
            content
        )
        for m in by_matches:
            var_name = m.group(1)
            by_type = m.group(2).lower()
            selector = extract_quoted_string((m.group(3), m.group(4)))
            strat = LocatorStrategy.XPATH if "xpath" in by_type else (LocatorStrategy.ID if "id" in by_type else LocatorStrategy.CSS)
            locators[var_name] = LocatorIR(name=var_name, strategy=strat, value=selector)

        page.locators = list(locators.values())

        # 3. Methods
        method_blocks = re.findall(r"(?:public|protected|private)\s+([A-Za-z0-9_<>\s]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*(?:throws\s+[A-Za-z0-9_,\s]+)?\s*\{([^}]+)\}", content, re.MULTILINE)
        for ret_type, m_name, params_str, body in method_blocks:
            if m_name == page_name:
                continue
            params = [p.strip().split()[-1] for p in params_str.split(",") if p.strip()]
            steps = cls._extract_steps_from_body(body)
            page.methods.append(MethodIR(name=m_name, parameters=params, return_type=ret_type.strip(), steps=steps))

        project.pages.append(page)

        # 4. TestNG / JUnit
        test_matches = re.findall(r"@Test[^\n]*\s*(?:public|void|\s)+([A-Za-z0-9_]+)\s*\([^)]*\)[^{]*\{([^}]+)\}", content, re.MULTILINE)
        for idx, (t_name, t_body) in enumerate(test_matches, 1):
            steps = cls._extract_steps_from_body(t_body)
            project.test_cases.append(TestCaseIR(id=f"TC_{idx:03d}", title=t_name, steps=steps))

    # -------------------------------------------------------------------------
    # Groovy / Katalon Parser (Clean POM Flat Architecture)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_groovy(cls, content: str, project: ProjectIR, framework: str):
        class_match = re.search(r"class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?", content)
        page_name = class_match.group(1) if class_match else f"{project.name}Page"
        base_class = class_match.group(2) if (class_match and class_match.group(2)) else "BasePage"

        page = PageClassIR(name=page_name, base_class=base_class)
        locators: Dict[str, LocatorIR] = {}

        # Extract static final String XPaths
        xpath_matches = re.finditer(
            r"(?:(?:public|private|protected|static|final)\s+)*(?:String|def)\s+([A-Za-z0-9_]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",
            content
        )
        for m in xpath_matches:
            var_name = m.group(1)
            selector = extract_quoted_string((m.group(2), m.group(3)))
            strat = LocatorStrategy.XPATH if selector.startswith(("//", "(//")) else LocatorStrategy.CSS
            locators[var_name] = LocatorIR(name=var_name, strategy=strat, value=selector)

        page.locators = list(locators.values())

        # Methods
        method_blocks = re.findall(r"(?:(?:public|private|protected|def|static|void|[A-Za-z0-9_<>]+)\s+)+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*\{([^}]+)\}", content, re.MULTILINE)
        for m_name, params_str, body in method_blocks:
            if m_name in [page_name, "main"]:
                continue
            params = [p.strip().split()[-1] for p in params_str.split(",") if p.strip()]
            steps = cls._extract_steps_from_body(body)
            page.methods.append(MethodIR(name=m_name, parameters=params, steps=steps))

        project.pages.append(page)

        if not class_match:
            steps = cls._extract_steps_from_body(content)
            project.test_cases.append(TestCaseIR(id="TC_001", title=project.name, steps=steps))

    # -------------------------------------------------------------------------
    # Python Parser (Pytest / Playwright / Selenium)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_python(cls, content: str, project: ProjectIR, framework: str):
        class_match = re.search(r"class\s+([A-Za-z0-9_]+)(?:\(([^)]+)\))?:", content)
        page_name = class_match.group(1) if class_match else f"{project.name}Page"
        base_class = class_match.group(2) if (class_match and class_match.group(2)) else "BasePage"

        page = PageClassIR(name=page_name, base_class=base_class)
        locators: Dict[str, LocatorIR] = {}

        loc_matches = re.finditer(
            r"self\.([a-zA-Z0-9_]+)\s*=\s*(?:self\.)?page\.locator\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*\)",
            content
        )
        for m in loc_matches:
            name = m.group(1)
            sel = extract_quoted_string((m.group(2), m.group(3)))
            strat = LocatorStrategy.XPATH if sel.startswith(("//", "(//")) else LocatorStrategy.CSS
            locators[name] = LocatorIR(name=name, strategy=strat, value=sel)

        role_matches = re.finditer(
            r"self\.([a-zA-Z0-9_]+)\s*=\s*(?:self\.)?page\.get_by_role\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*,\s*name=(?:\"([^\"]*)\"|'([^']*)')\s*\)",
            content
        )
        for m in role_matches:
            name = m.group(1)
            r_type = extract_quoted_string((m.group(2), m.group(3)))
            r_name = extract_quoted_string((m.group(4), m.group(5)))
            locators[name] = LocatorIR(name=name, strategy=LocatorStrategy.ROLE, value=f"{r_type}[name='{r_name}']")

        page.locators = list(locators.values())

        func_blocks = re.findall(r"def\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*(?:->\s*[^:]+)?:([^d]+(?=def\s+|$))", content, re.MULTILINE)
        for f_name, f_params, f_body in func_blocks:
            if f_name.startswith("test_"):
                steps = cls._extract_steps_from_body(f_body)
                project.test_cases.append(TestCaseIR(id=f"TC_{len(project.test_cases)+1:03d}", title=f_name, steps=steps))
            elif f_name != "__init__":
                params = [p.strip().split(":")[0].strip() for p in f_params.split(",") if p.strip() and p.strip() != "self"]
                steps = cls._extract_steps_from_body(f_body)
                page.methods.append(MethodIR(name=f_name, parameters=params, steps=steps))

        project.pages.append(page)

    # -------------------------------------------------------------------------
    # C# Parser (.NET Selenium / Playwright)
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_csharp(cls, content: str, project: ProjectIR, framework: str):
        class_match = re.search(r"class\s+([A-Za-z0-9_]+)(?:\s*:\s*([A-Za-z0-9_]+))?", content)
        page_name = class_match.group(1) if class_match else f"{project.name}Page"
        base_class = class_match.group(2) if (class_match and class_match.group(2)) else "BasePage"

        page = PageClassIR(name=page_name, base_class=base_class)
        project.pages.append(page)

    # -------------------------------------------------------------------------
    # Generic Fallback Parser
    # -------------------------------------------------------------------------
    @classmethod
    def _parse_generic(cls, content: str, project: ProjectIR):
        page = PageClassIR(name=f"{project.name}Page")
        steps = cls._extract_steps_from_body(content)
        project.test_cases.append(TestCaseIR(id="TC_001", title=project.name, steps=steps))
        project.pages.append(page)

    # -------------------------------------------------------------------------
    # Universal Step Extractor (With Async/Sync Bridge & Antipattern Sanitizer)
    # -------------------------------------------------------------------------
    @classmethod
    def _extract_steps_from_body(cls, body: str) -> List[StepIR]:
        steps: List[StepIR] = []
        # Unroll Cypress .then() closures into sequential lines
        normalized_body = re.sub(r"\.then\s*\(\s*\([^)]*\)\s*=>\s*\{?", "\n", body)

        for line in normalized_body.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith(("//", "#", "/*", "*")) or line_str in ["}", "});"]:
                continue

            # 0. Detect Hardcoded Sleep Antipatterns (Thread.sleep, WebUI.delay, cy.wait, time.sleep)
            sleep_m = re.search(r"(?:Thread\.sleep|WebUI\.delay|time\.sleep|cy\.wait)\s*\(\s*(\d+)\s*\)", line_str, re.IGNORECASE)
            if sleep_m:
                val = int(sleep_m.group(1))
                ms = val * 1000 if val <= 60 else val  # WebUI.delay(3) vs Thread.sleep(3000)
                steps.append(StepIR(
                    action=ActionType.WAIT,
                    wait_strategy=WaitStrategy.STATIC_SLEEP,
                    is_sanitized_wait=True,
                    timeout_ms=ms,
                    description=f"Auto-healed from static sleep {line_str}"
                ))
                continue

            # 1. Cypress Command Chaining: cy.get('selector').action(...)
            cy_chain = re.search(r"cy\.get\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*\)\s*\.\s*(click|type|clear|should)\s*\(([^)]*)\)", line_str, re.IGNORECASE)
            if cy_chain:
                sel = extract_quoted_string((cy_chain.group(1), cy_chain.group(2)))
                cy_act = cy_chain.group(3).lower()
                cy_args = cy_chain.group(4)
                if cy_act == "click":
                    steps.append(StepIR(action=ActionType.CLICK, target=sel, description=f"Cypress click on {sel}"))
                elif cy_act in ["type", "clear"]:
                    type_val = extract_quoted_string(re.search(r"(?:\"([^\"]*)\"|'([^']*)')", cy_args).groups()) if re.search(r"(?:\"([^\"]*)\"|'([^']*)')", cy_args) else ""
                    steps.append(StepIR(action=ActionType.FILL, target=sel, value=type_val, description=f"Cypress type on {sel}"))
                elif cy_act == "should":
                    steps.append(StepIR(action=ActionType.ASSERT, target=sel, assertion_type=AssertionType.VISIBLE, description=line_str))
                continue

            # 2. Navigation
            nav_m = re.search(r"(?:goto|navigate|openBrowser|navigateToUrl|visit|get)\s*\(\s*(?:\"([^\"]*)\"|'([^']*)')\s*\)", line_str, re.IGNORECASE)
            if nav_m:
                val = extract_quoted_string((nav_m.group(1), nav_m.group(2)))
                steps.append(StepIR(action=ActionType.GOTO, value=val, description=f"Navigate to {val}"))
                continue

            # 3. Click
            click_m = re.search(r"(?:click|clickJS)\s*\(\s*(?:(?:\"([^\"]*)\"|'([^']*)')|([A-Za-z0-9_$.]+))?\s*\)", line_str, re.IGNORECASE)
            if click_m:
                target = extract_quoted_string((click_m.group(1), click_m.group(2))) or click_m.group(3) or "element"
                target_clean = target.replace("this.", "").replace("self.", "")
                steps.append(StepIR(action=ActionType.CLICK, target=target_clean, description=f"Click on {target_clean}"))
                continue

            # 4. Fill
            fill_m = re.search(r"(?:fill|sendKeys|setText|type)\s*\(\s*(?:([A-Za-z0-9_$.]+)\s*,\s*)?(?:\"([^\"]*)\"|'([^']*)')\s*\)", line_str, re.IGNORECASE)
            if fill_m:
                target = fill_m.group(1) or "input"
                val = extract_quoted_string((fill_m.group(2), fill_m.group(3)))
                target_clean = target.replace("this.", "").replace("self.", "")
                steps.append(StepIR(action=ActionType.FILL, target=target_clean, value=val, description=f"Fill {val} into {target_clean}"))
                continue

            # 5. Assertions
            if any(k in line_str for k in ["expect", "Assert.", "verify", "should("]):
                if "visible" in line_str.lower() or "present" in line_str.lower():
                    steps.append(StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.VISIBLE, description=line_str))
                elif "equal" in line_str.lower() or "match" in line_str.lower():
                    steps.append(StepIR(action=ActionType.ASSERT, assertion_type=AssertionType.EQUALS, description=line_str))
                else:
                    steps.append(StepIR(action=ActionType.ASSERT, description=line_str))
                continue

            if "(" in line_str and ")" in line_str:
                steps.append(StepIR(action=ActionType.CUSTOM_CALL, description=line_str))

        return steps
