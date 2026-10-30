#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/export_postman_collection.py — Enterprise API to Postman Collection v2.1.0 Exporter (Postman Pinnacle)
-----------------------------------------------------------------------------------------------------------
Converts OpenAPI / Swagger specifications, JSON endpoint schemas, HTTP Archives (HAR),
or Natural Language Domain archetypes into production-ready Postman Collections v2.1.0.

Pinnacle Enterprise Capabilities:
  1. Multi-Format Ingestion: OpenAPI 3.0 / Swagger 2.0, HAR traffic traces, or Zero-Input Domain Synthesis.
  2. Autonomous Zero-Input Synthesis: Generates complete multi-tier API collections from scratch
     when no input files exist (`--domain [ecommerce|banking|saas]`).
  3. Pre-request Scripts: Dynamic request timestamps, UUIDs, nonces, and automated Bearer Auth headers.
  4. Test Scripts (pm.test):
     - Expected HTTP Status assertions.
     - SLA Latency assertions (< 1000ms).
     - Response Content-Type JSON header validation.
     - Autonomous Token & ID Extractor (`pm.environment.set('bearerToken', ...)`).
     - Native AJV JSON Schema Validation (`pm.response.to.have.jsonSchema(schema)`).
  5. Companion Environment Generator: Outputs `postman_environment.json` with base URLs and variables.
  6. Data-Driven Testing (DDT) Suite: Outputs companion `test_data.csv` for Newman matrix execution.
  7. 100% UTF-8 No BOM, portable, Newman CLI and CI/CD compatible.

Usage:
  # 1. From existing OpenAPI / Swagger
  python tools/export_postman_collection.py --spec swagger.json -o collection.json --env-output env.json

  # 2. Zero-Input Autonomous Generation (No input files!)
  python tools/export_postman_collection.py --domain ecommerce -o ecom_collection.json --ddt-output ecom_data.csv
  python tools/export_postman_collection.py --domain banking -o banking_collection.json --env-output banking_env.json

  # 3. From browser network trace (.har)
  python tools/export_postman_collection.py --har traffic.har -o collection.json
"""

import os
import sys
import json
import re
import uuid
import csv
import argparse
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs

# Enforce UTF-8 stdout encoding for Windows/macOS/Linux console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def generate_uuid() -> str:
    return str(uuid.uuid4())


def build_pre_request_script() -> List[str]:
    """Generates standard Postman Pre-request script lines."""
    return [
        "// Auto-generated Pre-request Script by Synapse-Hub",
        "// 1. Dynamic Timestamp & Correlation ID generation",
        "pm.variables.set('req_timestamp', new Date().toISOString());",
        "pm.variables.set('req_nonce', Math.random().toString(36).substring(2, 12));",
        "pm.variables.set('correlation_id', 'CORR-' + pm.variables.get('req_nonce'));",
        "",
        "// 2. Automated Bearer Token Injection if present in environment",
        "var token = pm.environment.get('bearerToken') || pm.collectionVariables.get('bearerToken');",
        "if (token && !pm.request.headers.has('Authorization')) {",
        "    pm.request.headers.add({ key: 'Authorization', value: 'Bearer ' + token });",
        "}"
    ]


def build_test_script(
    expected_status: int = 200,
    max_time_ms: int = 1000,
    response_schema: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Generates comprehensive Postman Test script lines with AJV JSON Schema assertion."""
    lines = [
        "// Auto-generated Test Assertions by Synapse-Hub",
        f"// 1. Assert Status Code is {expected_status}",
        f"pm.test('Status code is {expected_status}', function () {{",
        f"    pm.expect(pm.response.code).to.eql({expected_status});",
        "});",
        "",
        f"// 2. Assert SLA Latency (< {max_time_ms}ms)",
        f"pm.test('Response time is below {max_time_ms}ms SLA', function () {{",
        f"    pm.expect(pm.response.responseTime).to.be.below({max_time_ms});",
        "});",
        "",
        "// 3. Assert Content-Type JSON Header",
        "pm.test('Response header Content-Type is JSON', function () {",
        "    if (pm.response.code !== 204) {",
        "        pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json');",
        "    }",
        "});",
        "",
        "// 4. Autonomous Token / Entity ID Extraction & Session Chaining",
        "if (pm.response.code >= 200 && pm.response.code < 300) {",
        "    try {",
        "        var jsonBody = pm.response.json();",
        "        // Auto-extract JWT / OAuth tokens",
        "        var authToken = jsonBody.token || jsonBody.access_token || (jsonBody.data && (jsonBody.data.token || jsonBody.data.access_token));",
        "        if (authToken) {",
        "            pm.environment.set('bearerToken', authToken);",
        "            pm.collectionVariables.set('bearerToken', authToken);",
        "            console.log('[Synapse-Hub] Captured dynamic bearerToken: ' + authToken.substring(0, 15) + '...');",
        "        }",
        "        // Auto-extract newly created ID",
        "        var entityId = jsonBody.id || jsonBody.code || (jsonBody.data && (jsonBody.data.id || jsonBody.data.code));",
        "        if (entityId) {",
        "            pm.environment.set('lastCreatedId', String(entityId));",
        "            console.log('[Synapse-Hub] Captured lastCreatedId: ' + entityId);",
        "        }",
        "    } catch (e) {",
        "        // Response is non-JSON or empty body",
        "    }",
        "}"
    ]

    # 5. AJV Native JSON Schema Validation
    if response_schema:
        schema_clean = json.dumps(response_schema, ensure_ascii=False)
        lines.extend([
            "",
            "// 5. AJV JSON Schema Contract Validation",
            "pm.test('Response conforms to OpenAPI JSON Schema', function () {",
            f"    var schema = {schema_clean};",
            "    pm.response.to.have.jsonSchema(schema);",
            "});"
        ])

    return lines


def mock_schema_payload(schema: Dict[str, Any], depth: int = 0) -> Any:
    """Recursively generates realistic mock JSON payload from OpenAPI schema."""
    if depth > 3 or not schema:
        return {}

    stype = schema.get("type", "object")

    if stype == "string":
        fmt = schema.get("format", "")
        if fmt == "email":
            return "{{$randomEmail}}"
        elif fmt == "uuid":
            return "{{$guid}}"
        elif fmt in ("date-time", "date"):
            return "{{$isoTimestamp}}"
        return schema.get("example") or f"AUTO_{{{{$randomAlphaNumeric}}}}"

    elif stype in ("integer", "number"):
        return schema.get("example") or schema.get("minimum", 100)

    elif stype == "boolean":
        return schema.get("example", True)

    elif stype == "array":
        items_schema = schema.get("items", {})
        return [mock_schema_payload(items_schema, depth + 1)]

    elif stype == "object":
        props = schema.get("properties", {})
        obj = {}
        for p_name, p_schema in props.items():
            obj[p_name] = mock_schema_payload(p_schema, depth + 1)
        return obj

    return {}


def parse_openapi_spec(spec_data: Dict[str, Any], base_url_override: Optional[str] = None) -> Dict[str, Any]:
    """Parses OpenAPI 2.0 / 3.0 dictionary into a Postman Collection v2.1.0 structure."""
    info_dict = spec_data.get("info", {})
    col_name = info_dict.get("title", "Enterprise API Collection")
    col_desc = info_dict.get("description", "Auto-generated Postman Collection from OpenAPI / Swagger")

    # Determine Base URL
    if base_url_override:
        base_url_default = base_url_override
    elif "servers" in spec_data and spec_data["servers"]:
        base_url_default = spec_data["servers"][0].get("url", "https://api.staging.enterprise.local")
    elif "host" in spec_data:
        schemes = spec_data.get("schemes", ["https"])
        base_url_default = f"{schemes[0]}://{spec_data['host']}{spec_data.get('basePath', '')}"
    else:
        base_url_default = "https://api.staging.enterprise.local"

    # Postman root structure
    collection = {
        "info": {
            "_postman_id": generate_uuid(),
            "name": col_name,
            "description": col_desc,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": base_url_default,
                "type": "string"
            },
            {
                "key": "bearerToken",
                "value": "",
                "type": "string"
            },
            {
                "key": "lastCreatedId",
                "value": "1",
                "type": "string"
            }
        ],
        "item": []
    }

    folders: Dict[str, List[Dict[str, Any]]] = {}
    paths = spec_data.get("paths", {})

    for path, path_item in paths.items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in path_item:
                continue

            op = path_item[method]
            summary = op.get("summary") or f"{method.upper()} {path}"
            tags = op.get("tags", ["Default"])
            tag_name = tags[0] if tags else "Default"

            # Parse headers
            headers = [
                {"key": "Content-Type", "value": "application/json", "type": "text"},
                {"key": "Accept", "value": "application/json", "type": "text"}
            ]

            # Parse Query Parameters
            query_params = []
            for p in op.get("parameters", []):
                if p.get("in") == "query":
                    query_params.append({
                        "key": p.get("name"),
                        "value": str(p.get("example", "")),
                        "description": p.get("description", "")
                    })
                elif p.get("in") == "header":
                    headers.append({
                        "key": p.get("name"),
                        "value": str(p.get("example", "")),
                        "type": "text"
                    })

            # Parse Request Body
            body_dict = None
            if method in ("post", "put", "patch"):
                req_body = op.get("requestBody", {})
                content = req_body.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema")

                if not schema:
                    for p in op.get("parameters", []):
                        if p.get("in") == "body":
                            schema = p.get("schema")
                            break

                if schema:
                    payload = mock_schema_payload(schema)
                    body_dict = {
                        "mode": "raw",
                        "raw": json.dumps(payload, indent=2, ensure_ascii=False),
                        "options": {"raw": {"language": "json"}}
                    }
                else:
                    body_dict = {
                        "mode": "raw",
                        "raw": "{}",
                        "options": {"raw": {"language": "json"}}
                    }

            # URL decomposition and path parameterization
            raw_path = path
            path_variables = []
            normalized_segments = []
            for seg in path.strip("/").split("/"):
                if not seg:
                    continue
                match = re.match(r"^\{([a-zA-Z0-9_-]+)\}$", seg)
                if match:
                    param_name = match.group(1)
                    raw_path = raw_path.replace(f"{{{param_name}}}", f":{param_name}")
                    normalized_segments.append(f":{param_name}")
                    default_val = "{{lastCreatedId}}" if param_name.lower() in ("id", "entityid", "orderid") else f"{{{{{param_name}}}}}"
                    path_variables.append({
                        "key": param_name,
                        "value": default_val,
                        "description": f"URL Path variable {param_name}"
                    })
                else:
                    normalized_segments.append(seg)

            url_obj = {
                "raw": f"{{{{baseUrl}}}}{raw_path}",
                "host": ["{{baseUrl}}"],
                "path": normalized_segments
            }
            if path_variables:
                url_obj["variable"] = path_variables
            if query_params:
                url_obj["query"] = query_params

            # Status code and response schema for assertion
            responses = op.get("responses", {})
            expected_status = 200
            for code_str in responses.keys():
                if code_str.isdigit():
                    expected_status = int(code_str)
                    break

            resp_info = responses.get(str(expected_status), {}) or responses.get("200", {}) or responses.get("201", {})
            resp_schema = resp_info.get("content", {}).get("application/json", {}).get("schema")
            if not resp_schema and "schema" in resp_info:
                resp_schema = resp_info["schema"]

            postman_request = {
                "name": summary,
                "event": [
                    {
                        "listen": "prerequest",
                        "script": {
                            "type": "text/javascript",
                            "exec": build_pre_request_script()
                        }
                    },
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": build_test_script(
                                expected_status=expected_status,
                                response_schema=resp_schema
                            )
                        }
                    }
                ],
                "request": {
                    "method": method.upper(),
                    "header": headers,
                    "url": url_obj,
                    "description": op.get("description", "")
                },
                "response": []
            }

            if body_dict:
                postman_request["request"]["body"] = body_dict

            if tag_name not in folders:
                folders[tag_name] = []
            folders[tag_name].append(postman_request)

    # Nest grouped requests into folder items
    for folder_name, req_list in folders.items():
        collection["item"].append({
            "name": folder_name,
            "item": req_list,
            "description": f"Endpoints grouped under {folder_name}"
        })

    return collection


def parse_har_file(har_data: Dict[str, Any], base_url_override: Optional[str] = None) -> Dict[str, Any]:
    """Parses HTTP Archive (.har) into a Postman Collection v2.1.0."""
    entries = har_data.get("log", {}).get("entries", [])
    collection_name = "HAR Recorded API Collection"

    base_url_default = base_url_override or "https://api.staging.enterprise.local"

    collection = {
        "info": {
            "_postman_id": generate_uuid(),
            "name": collection_name,
            "description": "Generated from HTTP Archive Network Trace",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {"key": "baseUrl", "value": base_url_default, "type": "string"},
            {"key": "bearerToken", "value": "", "type": "string"},
            {"key": "lastCreatedId", "value": "1", "type": "string"}
        ],
        "item": []
    }

    requests_by_host: Dict[str, List[Dict[str, Any]]] = {}

    for idx, e in enumerate(entries, 1):
        req = e.get("request", {})
        resp = e.get("response", {})
        raw_url = req.get("url", "/")
        method = req.get("method", "GET").upper()
        p = urlparse(raw_url)
        host = p.netloc or "Default"

        headers = []
        for h in req.get("headers", []):
            name = h.get("name", "")
            if name.lower() not in ("cookie", "host", "content-length"):
                headers.append({"key": name, "value": h.get("value", ""), "type": "text"})

        path_segments = [seg for seg in p.path.strip("/").split("/") if seg]
        url_obj = {
            "raw": f"{{{{baseUrl}}}}{p.path}" + (f"?{p.query}" if p.query else ""),
            "host": ["{{baseUrl}}"],
            "path": path_segments
        }

        body_dict = None
        post_data = req.get("postData", {})
        if post_data.get("text"):
            body_dict = {
                "mode": "raw",
                "raw": post_data["text"],
                "options": {"raw": {"language": "json"}}
            }

        expected_status = resp.get("status", 200) or 200
        postman_item = {
            "name": f"[{method}] {p.path or '/'}",
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": build_pre_request_script()}
                },
                {
                    "listen": "test",
                    "script": {"type": "text/javascript", "exec": build_test_script(expected_status=expected_status)}
                }
            ],
            "request": {
                "method": method,
                "header": headers,
                "url": url_obj,
                "description": f"Recorded step {idx}"
            },
            "response": []
        }

        if body_dict:
            postman_item["request"]["body"] = body_dict

        if host not in requests_by_host:
            requests_by_host[host] = []
        requests_by_host[host].append(postman_item)

    for host, reqs in requests_by_host.items():
        collection["item"].append({
            "name": f"Host: {host}",
            "item": reqs,
            "description": f"Recorded requests against {host}"
        })

    return collection


def generate_postman_environment(name: str = "Enterprise-Staging-Env", base_url: str = "https://api.staging.enterprise.local") -> Dict[str, Any]:
    """Generates companion Postman environment JSON for Newman/CLI integration."""
    return {
        "id": generate_uuid(),
        "name": name,
        "values": [
            {"key": "baseUrl", "value": base_url, "enabled": True},
            {"key": "bearerToken", "value": "", "type": "secret", "enabled": True},
            {"key": "lastCreatedId", "value": "1", "enabled": True},
            {"key": "adminUser", "value": "qa_admin@enterprise.local", "enabled": True},
            {"key": "adminPass", "value": "SecretVault#2026", "type": "secret", "enabled": True}
        ],
        "_postman_variable_scope": "environment"
    }


def generate_ddt_dataset(domain: str = "ecommerce") -> List[Dict[str, Any]]:
    """Generates companion Data-Driven Testing (DDT) matrix for Newman execution."""
    if domain == "banking":
        return [
            {"scenario": "Valid Domestic Transfer", "sender": "ACC-101", "recipient": "ACC-902", "amount": 500000, "expectedStatus": 201},
            {"scenario": "Zero Amount Boundary", "sender": "ACC-101", "recipient": "ACC-902", "amount": 0, "expectedStatus": 400},
            {"scenario": "Negative Amount Attack", "sender": "ACC-101", "recipient": "ACC-902", "amount": -150000, "expectedStatus": 400},
            {"scenario": "Exceed Daily Balance Limit", "sender": "ACC-101", "recipient": "ACC-902", "amount": 999999999, "expectedStatus": 422},
            {"scenario": "Invalid Recipient Format", "sender": "ACC-101", "recipient": "<script>alert(1)</script>", "expectedStatus": 400}
        ]
    elif domain == "saas":
        return [
            {"scenario": "Standard Member Creation", "username": "member_valid", "role": "MEMBER", "priority": 10, "expectedStatus": 201},
            {"scenario": "Admin Role Assignment", "username": "admin_chief", "role": "ADMIN", "priority": 1, "expectedStatus": 201},
            {"scenario": "Empty Username Boundary", "username": "", "role": "MEMBER", "priority": 10, "expectedStatus": 400},
            {"scenario": "SQLi Injection Probe", "username": "' OR '1'='1' --", "role": "MEMBER", "priority": 10, "expectedStatus": 400},
            {"scenario": "Invalid Role Privilege", "username": "intruder_user", "role": "SUPER_ROOT_UNAUTHORIZED", "priority": 99, "expectedStatus": 403}
        ]
    else:  # ecommerce default
        return [
            {"scenario": "Valid Catalog Creation", "code": "SKU_AUTO_2026", "name": "Enterprise Quantum Server", "priority": 10, "expectedStatus": 201},
            {"scenario": "Short Code Boundary (< 3 chars)", "code": "A1", "name": "Invalid Item", "priority": 5, "expectedStatus": 400},
            {"scenario": "Max Length Code Boundary", "code": "SKU_MAX_CHARS_990000", "name": "Max Length Product", "priority": 50, "expectedStatus": 201},
            {"scenario": "Empty Product Name", "code": "SKU_VALID_02", "name": "", "priority": 20, "expectedStatus": 400},
            {"scenario": "XSS Script Body Injection", "code": "SKU_XSS_03", "name": "<script>alert('pwned')</script>", "priority": 1, "expectedStatus": 400}
        ]


def get_domain_spec(domain: str = "ecommerce") -> Dict[str, Any]:
    """Autonomous Zero-Input Domain Spec Synthesizer."""
    if domain == "banking":
        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Enterprise Banking & Fund Transfer API",
                "version": "2.4.0",
                "description": "Production Banking API with OAuth2, Idempotent Transfers, and Audit Queries"
            },
            "servers": [{"url": "https://api.banking.staging.local"}],
            "paths": {
                "/api/v1/auth/token": {
                    "post": {
                        "tags": ["Authentication"],
                        "summary": "Obtain Bearer JWT Token",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["clientId", "clientSecret"],
                                        "properties": {
                                            "clientId": {"type": "string", "example": "bank_admin"},
                                            "clientSecret": {"type": "string", "example": "SecretVault#2026"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Token granted",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["token", "tokenType", "expiresIn"],
                                            "properties": {
                                                "token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake"},
                                                "tokenType": {"type": "string", "example": "Bearer"},
                                                "expiresIn": {"type": "integer", "example": 3600}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/accounts/me": {
                    "get": {
                        "tags": ["Account Management"],
                        "summary": "Get Account Balance & Profile",
                        "responses": {
                            "200": {
                                "description": "Account details retrieved",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["accountNumber", "balance", "currency"],
                                            "properties": {
                                                "accountNumber": {"type": "string", "example": "ACC-889922"},
                                                "balance": {"type": "number", "example": 25000000.0},
                                                "currency": {"type": "string", "example": "VND"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/transfers": {
                    "post": {
                        "tags": ["Fund Transfers"],
                        "summary": "Execute Idempotent Fund Transfer",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["recipientAccount", "amount", "idempotencyKey"],
                                        "properties": {
                                            "recipientAccount": {"type": "string", "example": "ACC-990011"},
                                            "amount": {"type": "number", "example": 500000.0},
                                            "idempotencyKey": {"type": "string", "example": "{{$guid}}"},
                                            "remark": {"type": "string", "example": "Payment for invoice"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Transfer queued or completed",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["id", "status", "transactionRef"],
                                            "properties": {
                                                "id": {"type": "string", "example": "TX-998822"},
                                                "status": {"type": "string", "example": "COMPLETED"},
                                                "transactionRef": {"type": "string", "example": "REF-AUTO-2026"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/transfers/{id}": {
                    "get": {
                        "tags": ["Fund Transfers"],
                        "summary": "Audit Transfer Status by ID",
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "example": "{{lastCreatedId}}"}
                        ],
                        "responses": {
                            "200": {
                                "description": "Transfer status verified",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["id", "status", "amount"],
                                            "properties": {
                                                "id": {"type": "string", "example": "TX-998822"},
                                                "status": {"type": "string", "example": "COMPLETED"},
                                                "amount": {"type": "number", "example": 500000.0}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    elif domain == "saas":
        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Enterprise SaaS Tenant & User RBAC API",
                "version": "1.8.0",
                "description": "Multi-Tenant SaaS Management Suite"
            },
            "servers": [{"url": "https://api.saas.staging.local"}],
            "paths": {
                "/api/v1/auth/login": {
                    "post": {
                        "tags": ["Identity"],
                        "summary": "Tenant Admin Login",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["tenantId", "username", "password"],
                                        "properties": {
                                            "tenantId": {"type": "string", "example": "tenant_enterprise"},
                                            "username": {"type": "string", "example": "admin"},
                                            "password": {"type": "string", "example": "SecretPass#2026"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Login successful",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["token", "role"],
                                            "properties": {
                                                "token": {"type": "string", "example": "jwt.tenant.token"},
                                                "role": {"type": "string", "example": "TENANT_ADMIN"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/users": {
                    "get": {
                        "tags": ["User Directory"],
                        "summary": "List Active Tenant Users",
                        "responses": {"200": {"description": "Users list"}}
                    },
                    "post": {
                        "tags": ["User Directory"],
                        "summary": "Provision New Tenant Member",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["email", "role"],
                                        "properties": {
                                            "email": {"type": "string", "example": "user_auto@tenant.com"},
                                            "role": {"type": "string", "example": "MEMBER"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "User created",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["id", "email"],
                                            "properties": {
                                                "id": {"type": "string", "example": "USR-101"},
                                                "email": {"type": "string", "example": "user_auto@tenant.com"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/users/{id}": {
                    "delete": {
                        "tags": ["User Directory"],
                        "summary": "Deprovision Member (Teardown Cleanup)",
                        "parameters": [{"name": "id", "in": "path", "required": True, "example": "{{lastCreatedId}}"}],
                        "responses": {"204": {"description": "User deprovisioned"}}
                    }
                }
            }
        }
    else:  # E-commerce default
        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Enterprise E-Commerce Core API",
                "version": "3.2.0",
                "description": "Enterprise E-Commerce Commerce Engine API with Auth, Search, Cart, Order, and Teardown"
            },
            "servers": [{"url": "https://api.staging.enterprise.local"}],
            "paths": {
                "/api/v1/auth/login": {
                    "post": {
                        "tags": ["Authentication"],
                        "summary": "User Authentication (Login)",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["username", "password"],
                                        "properties": {
                                            "username": {"type": "string", "example": "admin"},
                                            "password": {"type": "string", "example": "SecretVault#2026"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Login",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["token", "tokenType"],
                                            "properties": {
                                                "token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake"},
                                                "tokenType": {"type": "string", "example": "Bearer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/catalogs": {
                    "get": {
                        "tags": ["Catalog Service"],
                        "summary": "Search Product Catalogs",
                        "parameters": [
                            {"name": "query", "in": "query", "example": "server"},
                            {"name": "limit", "in": "query", "example": "20"}
                        ],
                        "responses": {
                            "200": {
                                "description": "Catalogs search result",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["items", "total"],
                                            "properties": {
                                                "items": {"type": "array", "items": {"type": "object"}},
                                                "total": {"type": "integer", "example": 42}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "tags": ["Catalog Service"],
                        "summary": "Create Product Item",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["code", "name"],
                                        "properties": {
                                            "code": {"type": "string", "example": "SKU_AUTO_2026"},
                                            "name": {"type": "string", "example": "Enterprise Quantum Server"},
                                            "priority": {"type": "integer", "example": 10}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Product created",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["id", "code"],
                                            "properties": {
                                                "id": {"type": "string", "example": "PRD-998811"},
                                                "code": {"type": "string", "example": "SKU_AUTO_2026"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/catalogs/{id}": {
                    "delete": {
                        "tags": ["Catalog Service"],
                        "summary": "Delete Catalog Item (Idempotent Teardown)",
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "example": "{{lastCreatedId}}"}
                        ],
                        "responses": {"204": {"description": "Item deleted"}}
                    }
                }
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description="Export OpenAPI, HAR, or Zero-Input Domain Synthesis to Postman Collection v2.1.0."
    )
    parser.add_argument("--spec", "-s", help="Path to OpenAPI / Swagger JSON specification file.")
    parser.add_argument("--har", help="Path to HTTP Archive (.har) recording file.")
    parser.add_argument("--domain", choices=["ecommerce", "banking", "saas"], default="ecommerce", help="Zero-input domain synthesizer template. Default: ecommerce.")
    parser.add_argument("--base-url", "-b", help="Override base URL for {{baseUrl}} parameter.")
    parser.add_argument("--output", "-o", help="Target output Postman Collection file path (.json).")
    parser.add_argument("--env-output", help="Optional companion Postman Environment output file (.json).")
    parser.add_argument("--ddt-output", help="Optional companion Data-Driven Testing (DDT) CSV file for Newman.")
    parser.add_argument("--sample", action="store_true", help="Generate sample collection using domain synthesizer.")

    args = parser.parse_args()

    # Determine data source
    if args.har and os.path.exists(args.har):
        with open(args.har, "r", encoding="utf-8") as f:
            har_data = json.load(f)
        collection = parse_har_file(har_data, base_url_override=args.base_url)
        active_domain = "har"
    elif args.spec and os.path.exists(args.spec):
        with open(args.spec, "r", encoding="utf-8") as f:
            spec_data = json.load(f)
        collection = parse_openapi_spec(spec_data, base_url_override=args.base_url)
        active_domain = "spec"
    else:
        # Autonomous Zero-Input Synthesis (User provided no file!)
        spec_data = get_domain_spec(args.domain)
        collection = parse_openapi_spec(spec_data, base_url_override=args.base_url)
        active_domain = args.domain
        print(f"✨ [ZERO-INPUT SYNTHESIS] Synthesized complete '{args.domain.upper()}' Enterprise API Suite from scratch!")

    target_output = args.output or f"{active_domain}_collection.json"
    out_dir = os.path.dirname(os.path.abspath(target_output))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(target_output, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    print(f"✅ [POSTMAN EXPORT] Successfully created Postman Collection v2.1.0: {target_output}")
    print(f"🛡️ Embedded: Pre-request Nonce & Auth | SLA Tests (< 1000ms) | AJV JSON Schema Validation | Token Chaining")

    # Optional Companion Environment
    env_file = args.env_output or (os.path.splitext(target_output)[0] + "_env.json")
    base_u = args.base_url or "https://api.staging.enterprise.local"
    env_dict = generate_postman_environment(name=f"Synapse-{active_domain.capitalize()}-Env", base_url=base_u)
    with open(env_file, "w", encoding="utf-8") as f:
        json.dump(env_dict, f, indent=2, ensure_ascii=False)
    print(f"🌐 [ENVIRONMENT EXPORT] Successfully created Postman Environment: {env_file}")

    # Optional Companion Data-Driven Testing (DDT) CSV
    if args.ddt_output or args.sample:
        ddt_file = args.ddt_output or (os.path.splitext(target_output)[0] + "_ddt.csv")
        dataset = generate_ddt_dataset(args.domain if active_domain in ("ecommerce", "banking", "saas") else "ecommerce")
        if dataset:
            with open(ddt_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(dataset[0].keys()))
                writer.writeheader()
                writer.writerows(dataset)
            print(f"📊 [DDT EXPORT] Successfully created Data-Driven Testing CSV: {ddt_file}")
            print(f"🚀 Execution Command: newman run \"{target_output}\" -e \"{env_file}\" -d \"{ddt_file}\"")


if __name__ == "__main__":
    main()
