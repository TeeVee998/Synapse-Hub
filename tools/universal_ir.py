#!/usr/bin/env python3
"""
Universal Testing Intermediate Representation (IR) Schema
---------------------------------------------------------
Defines a language-agnostic and framework-agnostic schema for test automation.
Represents pages, locators, methods, test cases, and assertions independently of
whether the target is Playwright, Selenium, Cypress, Katalon, or Appium.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json


class ActionType(str, Enum):
    GOTO = "goto"
    CLICK = "click"
    DBLCLICK = "dblclick"
    FILL = "fill"
    PRESS_KEY = "press_key"
    HOVER = "hover"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    WAIT = "wait"
    ASSERT = "assert"
    CUSTOM_CALL = "custom_call"
    API_CALL = "api_call"


class LocatorStrategy(str, Enum):
    ROLE = "role"
    LABEL = "label"
    TEST_ID = "test_id"
    TEXT = "text"
    CSS = "css"
    XPATH = "xpath"
    PLACEHOLDER = "placeholder"
    ID = "id"
    NAME = "name"
    CLASS_NAME = "class_name"
    UNKNOWN = "unknown"


class AssertionType(str, Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    EQUALS = "equals"
    CONTAINS_TEXT = "contains_text"
    HAS_VALUE = "has_value"
    IS_ENABLED = "is_enabled"
    IS_DISABLED = "is_disabled"
    URL_CONTAINS = "url_contains"


class WaitStrategy(str, Enum):
    AUTO = "auto"
    EXPLICIT_VISIBLE = "explicit_visible"
    NETWORK_IDLE = "network_idle"
    STATIC_SLEEP = "static_sleep"  # Flagged antipattern


class DataDependencyType(str, Enum):
    ID = "id"
    AUTH_TOKEN = "auth_token"
    ORDER_NUMBER = "order_number"
    EMAIL = "email"
    SESSION = "session"
    CUSTOM = "custom"


@dataclass
class HermeticFixture:
    variable_name: str
    fixture_type: str = "synthetic_mock"  # "api_seed", "synthetic_mock", "auth_session"
    seed_endpoint: Optional[str] = None
    mock_data: Dict[str, Any] = field(default_factory=dict)
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "fixture_type": self.fixture_type,
            "seed_endpoint": self.seed_endpoint,
            "mock_data": self.mock_data,
            "code_snippet": self.code_snippet
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermeticFixture":
        return cls(
            variable_name=data.get("variable_name", ""),
            fixture_type=data.get("fixture_type", "synthetic_mock"),
            seed_endpoint=data.get("seed_endpoint"),
            mock_data=data.get("mock_data", {}),
            code_snippet=data.get("code_snippet", "")
        )


@dataclass
class SharedStateVariable:
    name: str
    producer_test_id: Optional[str] = None
    consumer_test_ids: List[str] = field(default_factory=list)
    dep_type: DataDependencyType = DataDependencyType.CUSTOM
    synthetic_fixture_code: str = ""
    mock_route: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "producer_test_id": self.producer_test_id,
            "consumer_test_ids": self.consumer_test_ids,
            "dep_type": self.dep_type.value if isinstance(self.dep_type, DataDependencyType) else self.dep_type,
            "synthetic_fixture_code": self.synthetic_fixture_code,
            "mock_route": self.mock_route
        }


@dataclass
class LocatorIR:
    name: str
    strategy: LocatorStrategy
    value: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "strategy": self.strategy.value if isinstance(self.strategy, LocatorStrategy) else self.strategy,
            "value": self.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocatorIR":
        strat = data.get("strategy", "unknown")
        try:
            strategy_enum = LocatorStrategy(strat)
        except ValueError:
            strategy_enum = LocatorStrategy.UNKNOWN
        return cls(
            name=data.get("name", "loc_unnamed"),
            strategy=strategy_enum,
            value=data.get("value", ""),
            description=data.get("description", ""),
        )


@dataclass
class StepIR:
    action: ActionType
    target: Optional[str] = None  # Locator name or raw selector
    value: Optional[str] = None   # Input text, key code, URL, etc.
    assertion_type: Optional[AssertionType] = None
    expected: Optional[str] = None
    wait_strategy: Optional[WaitStrategy] = None
    is_sanitized_wait: bool = False
    timeout_ms: int = 5000
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value if isinstance(self.action, ActionType) else self.action,
            "target": self.target,
            "value": self.value,
            "assertion_type": self.assertion_type.value if isinstance(self.assertion_type, AssertionType) and self.assertion_type else (self.assertion_type or None),
            "expected": self.expected,
            "wait_strategy": self.wait_strategy.value if isinstance(self.wait_strategy, WaitStrategy) and self.wait_strategy else (self.wait_strategy or None),
            "is_sanitized_wait": self.is_sanitized_wait,
            "timeout_ms": self.timeout_ms,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepIR":
        act = data.get("action", "custom_call")
        try:
            act_enum = ActionType(act)
        except ValueError:
            act_enum = ActionType.CUSTOM_CALL

        assert_type = data.get("assertion_type")
        assert_enum = None
        if assert_type:
            try:
                assert_enum = AssertionType(assert_type)
            except ValueError:
                assert_enum = None

        wait_strat = data.get("wait_strategy")
        wait_enum = None
        if wait_strat:
            try:
                wait_enum = WaitStrategy(wait_strat)
            except ValueError:
                wait_enum = None

        return cls(
            action=act_enum,
            target=data.get("target"),
            value=data.get("value"),
            assertion_type=assert_enum,
            expected=data.get("expected"),
            wait_strategy=wait_enum,
            is_sanitized_wait=data.get("is_sanitized_wait", False),
            timeout_ms=data.get("timeout_ms", 5000),
            description=data.get("description", ""),
        )


@dataclass
class MethodIR:
    name: str
    parameters: List[str] = field(default_factory=list)
    return_type: str = "void"
    steps: List[StepIR] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "steps": [s.to_dict() for s in self.steps],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MethodIR":
        return cls(
            name=data.get("name", "execute"),
            parameters=data.get("parameters", []),
            return_type=data.get("return_type", "void"),
            steps=[StepIR.from_dict(s) for s in data.get("steps", [])],
            description=data.get("description", ""),
        )


@dataclass
class PageClassIR:
    name: str
    base_class: str = "BasePage"
    url: Optional[str] = None
    locators: List[LocatorIR] = field(default_factory=list)
    methods: List[MethodIR] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "base_class": self.base_class,
            "url": self.url,
            "locators": [loc.to_dict() for loc in self.locators],
            "methods": [m.to_dict() for m in self.methods],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageClassIR":
        return cls(
            name=data.get("name", "UnnamedPage"),
            base_class=data.get("base_class", "BasePage"),
            url=data.get("url"),
            locators=[LocatorIR.from_dict(loc) for loc in data.get("locators", [])],
            methods=[MethodIR.from_dict(m) for m in data.get("methods", [])],
            description=data.get("description", ""),
        )


@dataclass
class TestCaseIR:
    # IR model, not a pytest test class - prefix "Test" must not trigger collection.
    __test__ = False

    id: str
    title: str
    steps: List[StepIR] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    produced_variables: List[str] = field(default_factory=list)
    consumed_variables: List[str] = field(default_factory=list)
    hermetic_fixtures: List[HermeticFixture] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "steps": [s.to_dict() for s in self.steps],
            "tags": self.tags,
            "description": self.description,
            "produced_variables": self.produced_variables,
            "consumed_variables": self.consumed_variables,
            "hermetic_fixtures": [hf.to_dict() for hf in self.hermetic_fixtures],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCaseIR":
        return cls(
            id=data.get("id", "TC_001"),
            title=data.get("title", "Automated Test Case"),
            steps=[StepIR.from_dict(s) for s in data.get("steps", [])],
            tags=data.get("tags", []),
            description=data.get("description", ""),
            produced_variables=data.get("produced_variables", []),
            consumed_variables=data.get("consumed_variables", []),
            hermetic_fixtures=[HermeticFixture.from_dict(hf) for hf in data.get("hermetic_fixtures", [])],
        )


@dataclass
class ProjectIR:
    name: str = "OmniTestProject"
    source_language: str = "generic"
    source_framework: str = "generic"
    pages: List[PageClassIR] = field(default_factory=list)
    test_cases: List[TestCaseIR] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_language": self.source_language,
            "source_framework": self.source_framework,
            "pages": [p.to_dict() for p in self.pages],
            "test_cases": [tc.to_dict() for tc in self.test_cases],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectIR":
        return cls(
            name=data.get("name", "OmniTestProject"),
            source_language=data.get("source_language", "generic"),
            source_framework=data.get("source_framework", "generic"),
            pages=[PageClassIR.from_dict(p) for p in data.get("pages", [])],
            test_cases=[TestCaseIR.from_dict(tc) for tc in data.get("test_cases", [])],
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectIR":
        data = json.loads(json_str)
        return cls.from_dict(data)


import re

SHARED_VAR_PATTERNS = [
    (r"\b(?:created_id|order_id|user_id|item_id|customer_id|invoice_id)\b", DataDependencyType.ID),
    (r"\b(?:auth_token|bearer_token|access_token|jwt_token|token)\b", DataDependencyType.AUTH_TOKEN),
    (r"\b(?:last_order_number|order_number|receipt_no|tracking_code)\b", DataDependencyType.ORDER_NUMBER),
    (r"\b(?:email|user_email|customer_email)\b", DataDependencyType.EMAIL),
    (r"\b(?:session_id|cookie_session|session_token)\b", DataDependencyType.SESSION),
]


def analyze_data_dependencies(project: ProjectIR) -> List[SharedStateVariable]:
    """
    Hermetic State & Data-Dependency Resolver:
    Performs data-flow analysis across test cases in ProjectIR to identify shared state
    and test coupling (variables produced in one test and consumed in another).
    """
    producers: Dict[str, str] = {}
    consumers: Dict[str, List[str]] = {}
    var_types: Dict[str, DataDependencyType] = {}

    for tc in project.test_cases:
        tc_produced = set(tc.produced_variables)
        tc_consumed = set(tc.consumed_variables)

        for s in tc.steps:
            text = f"{s.target or ''} {s.value or ''} {s.description or ''}"

            creation_match = re.search(
                r"\b(?:const|let|var|def|String|int)?\s*([a-zA-Z0-9_]+)\s*=\s*(?:response|created|new|generate|extract|get)",
                text,
                re.I
            )
            if creation_match:
                var_name = creation_match.group(1).lower()
                tc_produced.add(var_name)
                if var_name not in producers:
                    producers[var_name] = tc.id

            for pattern, dep_type in SHARED_VAR_PATTERNS:
                matches = re.findall(pattern, text, re.I)
                for m in matches:
                    v_name = m.lower()
                    var_types[v_name] = dep_type
                    if v_name not in tc_produced:
                        tc_consumed.add(v_name)
                        if v_name not in consumers:
                            consumers[v_name] = []
                        if tc.id not in consumers[v_name]:
                            consumers[v_name].append(tc.id)

        tc.produced_variables = sorted(list(tc_produced))
        tc.consumed_variables = sorted(list(tc_consumed))

    shared_vars: List[SharedStateVariable] = []
    all_var_names = set(producers.keys()) | set(consumers.keys())
    for v_name in sorted(all_var_names):
        d_type = var_types.get(v_name, DataDependencyType.CUSTOM)
        shared_vars.append(SharedStateVariable(
            name=v_name,
            producer_test_id=producers.get(v_name),
            consumer_test_ids=consumers.get(v_name, []),
            dep_type=d_type,
            synthetic_fixture_code=f"const {v_name} = 'HERMETIC_AUTO_' + Date.now();",
            mock_route=f"/api/v1/mock/{v_name}"
        ))

    return shared_vars


def resolve_hermetic_fixtures(project: ProjectIR) -> ProjectIR:
    """
    Transforms coupled test cases into 100% Hermetic Tests:
    Auto-generates and prepends Pre-flight Fixtures or API Data Seeds for any test case
    consuming external state without producing it locally.
    Enables zero-collision parallel sharding and isolated test impact execution.
    """
    shared_vars = analyze_data_dependencies(project)
    var_map = {sv.name: sv for sv in shared_vars}

    for tc in project.test_cases:
        fixtures_to_inject = []
        for consumed in list(tc.consumed_variables):
            if consumed not in tc.produced_variables:
                sv = var_map.get(consumed)
                dep_type = sv.dep_type if sv else DataDependencyType.CUSTOM

                if dep_type in (DataDependencyType.AUTH_TOKEN, DataDependencyType.SESSION):
                    fixture = HermeticFixture(
                        variable_name=consumed,
                        fixture_type="auth_session",
                        seed_endpoint="/api/v1/auth/mock",
                        mock_data={"token": "HERMETIC_MOCK_JWT", "role": "ADMIN", "active": True},
                        code_snippet=f"// Hermetic Auth Fixture\nawait page.setExtraHTTPHeaders({{ Authorization: 'Bearer HERMETIC_JWT_{consumed}' }});"
                    )
                    seed_step = StepIR(
                        action=ActionType.API_CALL,
                        target="/api/v1/auth/session",
                        value=f'{{"{consumed}": "HERMETIC_MOCK_JWT", "status": "ACTIVE"}}',
                        description=f"Hermetic Pre-flight: Injected Zero-Second Auth Session for {consumed}"
                    )
                elif dep_type in (DataDependencyType.ID, DataDependencyType.ORDER_NUMBER):
                    endpoint = f"/api/v1/{consumed.replace('_id', 's')}/seed"
                    fixture = HermeticFixture(
                        variable_name=consumed,
                        fixture_type="api_seed",
                        seed_endpoint=endpoint,
                        mock_data={"id": f"AUTO_{consumed.upper()}_SEED", "status": "CONFIRMED"},
                        code_snippet=f"const {consumed} = 'AUTO_SEED_' + Date.now();"
                    )
                    seed_step = StepIR(
                        action=ActionType.API_CALL,
                        target=endpoint,
                        value=f'{{"{consumed}": "AUTO_SEED_" + Date.now(), "status": "CONFIRMED"}}',
                        description=f"Hermetic Pre-flight: Seed direct API data record for {consumed}"
                    )
                else:
                    fixture = HermeticFixture(
                        variable_name=consumed,
                        fixture_type="synthetic_mock",
                        code_snippet=f"const {consumed} = 'HERMETIC_' + Date.now();"
                    )
                    seed_step = StepIR(
                        action=ActionType.CUSTOM_CALL,
                        value=f"const {consumed} = 'HERMETIC_' + Date.now();",
                        description=f"Hermetic Pre-flight: Synthetic state generator for {consumed}"
                    )

                tc.hermetic_fixtures.append(fixture)
                fixtures_to_inject.append(seed_step)
                tc.produced_variables.append(consumed)

        if fixtures_to_inject:
            tc.steps = fixtures_to_inject + tc.steps

    return project
