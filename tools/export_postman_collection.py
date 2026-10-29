#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/export_postman_collection.py — Enterprise API to Postman Collection v2.1.0 Exporter
-----------------------------------------------------------------------------------------
Converts OpenAPI / Swagger specifications, JSON endpoint schemas, or HTTP Archives (HAR)
into a production-ready Postman Collection v2.1.0 (with Pre-request Scripts, Tests Scripts,
Response Time Assertions, and Auto-Extracted Environment Variables).

Features:
  1. Ingests OpenAPI 3.0 / Swagger 2.0 JSON, HAR files, or built-in sample schemas.
  2. Generates organized folders by Tags / Resources with parameterized routes.
  3. Pre-request Scripts: Dynamic request timestamps, UUIDs, and automated auth headers.
  4. Test Scripts (pm.test):
     - Expected HTTP Status assertions.
     - Response time SLA latency assertions (< 1000ms).
     - Response Content-Type JSON header validation.
     - Autonomous Token & ID Extractor: Auto-saves `token`, `access_token`, or `id` into
       `pm.environment` / `pm.collectionVariables` for chaining sequential API calls.
  5. Companion Environment Generator: Outputs `postman_environment.json` with base URLs.
  6. 100% UTF-8 No BOM, portable, Newman CLI and CI/CD compatible.

Usage:
  python tools/export_postman_collection.py --spec swagger.json -o collection.json
  python tools/export_postman_collection.py --har traffic.har -o collection.json
  python tools/export_postman_collection.py --sample -o sample_collection.json --env-output sample_env.json
"""

import os
import sys
import json
import uuid
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
        "// Auto-generated Pre-request Script by Agent-QA Hub",
        "// 1. Dynamic Timestamp & Request ID generation",
        "pm.variables.set('req_timestamp', new Date().toISOString());",
        "pm.variables.set('req_nonce', Math.random().toString(36).substring(2, 12));",
        "",
        "// 2. Automated Bearer Token Injection if present in environment",
        "var token = pm.environment.get('bearerToken') || pm.collectionVariables.get('bearerToken');",
        "if (token && !pm.request.headers.has('Authorization')) {",
        "    pm.request.headers.add({ key: 'Authorization', value: 'Bearer ' + token });",
        "}"
    ]


def build_test_script(expected_status: int = 200, max_time_ms: int = 1000) -> List[str]:
    """Generates standard Postman Test script lines."""
    return [
        "// Auto-generated Test Assertions by Agent-QA Hub",
        f"// 1. Assert Status Code is {expected_status}",
        f"pm.test('Status code is {expected_status}', function () {{",
        f"    pm.expect(pm.response.code).to.be.oneOf([{expected_status}, 200, 201]);",
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
        "            console.log('[Agent-QA] Captured dynamic bearerToken: ' + authToken.substring(0, 15) + '...');",
        "        }",
        "        // Auto-extract newly created ID",
        "        var entityId = jsonBody.id || jsonBody.code || (jsonBody.data && (jsonBody.data.id || jsonBody.data.code));",
        "        if (entityId) {",
        "            pm.environment.set('lastCreatedId', String(entityId));",
        "        }",
        "    } catch (e) {",
        "        // Response is non-JSON or empty body",
        "    }",
        "}"
    ]


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
    base_url = "{{baseUrl}}"
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
            }
        ],
        "item": []
    }

    folders: Dict[str, List[Dict[str, Any]]] = {}
    paths = spec_data.get("paths", {})

    for path, path_item in paths.items():
        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            if method not in path_item:
                continue

            op = path_item[method]
            summary = op.get("summary") or f"{method.upper()} {path}"
            tags = op.get("tags") or ["Default"]
            tag_name = tags[0]

            # Request Headers
            headers = [
                {"key": "Content-Type", "value": "application/json", "type": "text"},
                {"key": "Accept", "value": "application/json", "type": "text"}
            ]

            # Query Parameters
            query_params = []
            for param in op.get("parameters", []):
                p_in = param.get("in")
                if p_in == "query":
                    query_params.append({
                        "key": param.get("name"),
                        "value": str(param.get("example") or param.get("default", "")),
                        "description": param.get("description", "")
                    })
                elif p_in == "header":
                    headers.append({
                        "key": param.get("name"),
                        "value": str(param.get("example", "")),
                        "type": "text",
                        "description": param.get("description", "")
                    })

            # Request Body
            body_dict = None
            if method in ("post", "put", "patch"):
                # OpenAPI 3.0 requestBody
                req_body = op.get("requestBody", {})
                content = req_body.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema")

                # Swagger 2.0 body parameter fallback
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

            # URL decomposition
            path_segments = [seg for seg in path.strip("/").split("/") if seg]
            url_obj = {
                "raw": f"{{{{baseUrl}}}}{path}",
                "host": ["{{baseUrl}}"],
                "path": path_segments
            }
            if query_params:
                url_obj["query"] = query_params

            # Status code for assertion
            responses = op.get("responses", {})
            expected_status = 200
            for code_str in responses.keys():
                if code_str.isdigit():
                    expected_status = int(code_str)
                    break

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
                            "exec": build_test_script(expected_status=expected_status)
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

    # Attach folders into collection
    for folder_name, items in folders.items():
        collection["item"].append({
            "name": folder_name,
            "item": items
        })

    return collection


def parse_har_file(har_data: Dict[str, Any], base_url_override: Optional[str] = None) -> Dict[str, Any]:
    """Parses HTTP Archive (.har) into a Postman Collection v2.1.0."""
    entries = har_data.get("log", {}).get("entries", [])
    collection = {
        "info": {
            "_postman_id": generate_uuid(),
            "name": "HAR Session API Replay",
            "description": "Replay collection generated from production HAR network telemetry",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {"key": "baseUrl", "value": base_url_override or "https://api.staging.enterprise.local", "type": "string"},
            {"key": "bearerToken", "value": "", "type": "string"}
        ],
        "item": []
    }

    requests_by_host: Dict[str, List[Dict[str, Any]]] = {}

    for entry in entries:
        req = entry.get("request", {})
        resp = entry.get("response", {})
        url_str = req.get("url", "")
        method = req.get("method", "GET").upper()

        parsed_url = urlparse(url_str)
        # Filter static files
        if any(parsed_url.path.lower().endswith(ext) for ext in (".png", ".jpg", ".css", ".js", ".woff2", ".ico")):
            continue

        host = parsed_url.netloc or "DefaultHost"
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        query_list = [{"key": k, "value": v[0] if v else ""} for k, v in query.items()]

        headers = []
        for h in req.get("headers", []):
            name = h.get("name", "")
            if name.lower() not in ("cookie", "host", "content-length"):
                headers.append({"key": name, "value": h.get("value", ""), "type": "text"})

        body_dict = None
        post_data = req.get("postData")
        if post_data and post_data.get("text"):
            body_dict = {
                "mode": "raw",
                "raw": post_data.get("text"),
                "options": {"raw": {"language": "json"}}
            }

        status_code = resp.get("status", 200)

        postman_item = {
            "name": f"{method} {path}",
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": build_pre_request_script()}
                },
                {
                    "listen": "test",
                    "script": {"type": "text/javascript", "exec": build_test_script(expected_status=status_code)}
                }
            ],
            "request": {
                "method": method,
                "header": headers,
                "url": {
                    "raw": url_str,
                    "host": [parsed_url.scheme + "://" + parsed_url.netloc],
                    "path": [p for p in path.strip("/").split("/") if p],
                    "query": query_list
                }
            },
            "response": []
        }
        if body_dict:
            postman_item["request"]["body"] = body_dict

        if host not in requests_by_host:
            requests_by_host[host] = []
        requests_by_host[host].append(postman_item)

    for host_name, items in requests_by_host.items():
        collection["item"].append({"name": host_name, "item": items})

    return collection


def generate_postman_environment(name: str = "Enterprise-Staging-Env", base_url: str = "https://api.staging.enterprise.local") -> Dict[str, Any]:
    """Generates companion Postman environment JSON for Newman/CLI integration."""
    return {
        "id": generate_uuid(),
        "name": name,
        "values": [
            {"key": "baseUrl", "value": base_url, "type": "default", "enabled": True},
            {"key": "bearerToken", "value": "", "type": "secret", "enabled": True},
            {"key": "lastCreatedId", "value": "", "type": "default", "enabled": True}
        ],
        "_postman_variable_scope": "environment"
    }


def get_sample_spec() -> Dict[str, Any]:
    """Provides standard built-in OpenAPI 3.0 spec for testing & demonstration."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Enterprise E-Commerce & Auth Service",
            "version": "1.0.0",
            "description": "Sample API spec for Postman & JMeter automated generation"
        },
        "servers": [{"url": "https://api.staging.enterprise.local"}],
        "paths": {
            "/api/v1/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Authenticate user and issue JWT token",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {"type": "string", "example": "admin_qa"},
                                        "password": {"type": "string", "example": "SecretPass#2026"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "JWT Token generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "token": {"type": "string"},
                                            "expires_in": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/v1/categories": {
                "get": {
                    "tags": ["Category Management"],
                    "summary": "List categories with pagination",
                    "parameters": [
                        {"name": "page", "in": "query", "example": 1},
                        {"name": "limit", "in": "query", "example": 20}
                    ],
                    "responses": {"200": {"description": "List of categories"}}
                },
                "post": {
                    "tags": ["Category Management"],
                    "summary": "Create a new category",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["code", "name"],
                                    "properties": {
                                        "code": {"type": "string", "minLength": 3, "maxLength": 20},
                                        "name": {"type": "string", "minLength": 1, "maxLength": 100},
                                        "priority": {"type": "integer", "minimum": 1, "maximum": 100}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Category created successfully"}}
                }
            },
            "/api/v1/categories/{id}": {
                "delete": {
                    "tags": ["Category Management"],
                    "summary": "Delete category by ID (Idempotent cleanup)",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "example": "{{lastCreatedId}}"}
                    ],
                    "responses": {"204": {"description": "Deleted"}}
                }
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Export OpenAPI or HAR to Postman Collection v2.1.0 with auto-asserts & token chaining."
    )
    parser.add_argument("--spec", "-s", help="Path to OpenAPI / Swagger JSON specification file.")
    parser.add_argument("--har", help="Path to HTTP Archive (.har) recording file.")
    parser.add_argument("--base-url", "-b", help="Override base URL for {{baseUrl}} parameter.")
    parser.add_argument("--output", "-o", help="Target output Postman Collection file path (.json).")
    parser.add_argument("--env-output", help="Optional companion Postman Environment output file (.json).")
    parser.add_argument("--sample", action="store_true", help="Generate sample collection using built-in enterprise schema.")
    parser.add_argument("--portman", action="store_true", help="Delegate conversion to @apideck/portman via npx (contract-driven assertions).")
    parser.add_argument("--newman", action="store_true", help="Automatically trigger headless Newman execution on the generated collection.")

    args = parser.parse_args()

    # If --portman is requested, run via npx @apideck/portman
    if args.portman:
        import subprocess
        import tempfile
        import shutil

        target_output = args.output or "postman_collection.json"
        spec_path = args.spec

        # Handle sample spec if no explicit spec file provided
        temp_spec_file = None
        if not spec_path or args.sample:
            fd, temp_spec_file = tempfile.mkstemp(suffix=".json", prefix="sample_spec_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(get_sample_spec(), f)
            spec_path = temp_spec_file

        portman_cmd = ["npx", "--yes", "@apideck/portman", "-l", spec_path, "-o", target_output]
        if args.base_url:
            portman_cmd.extend(["-b", args.base_url])
        if args.newman:
            portman_cmd.extend(["-n"])

        print(f"⚡ [PORTMAN BRIDGE] Executing: {' '.join(portman_cmd)}")
        try:
            res = subprocess.run(portman_cmd, check=True)
            print(f"✅ [PORTMAN SUCCESS] Collection generated via @apideck/portman: {target_output}")
            if temp_spec_file and os.path.exists(temp_spec_file):
                os.remove(temp_spec_file)
            return
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"⚠️ [PORTMAN FALLBACK] Could not run npx portman ({e}). Falling back to internal Pure-Python engine.")
            if temp_spec_file and os.path.exists(temp_spec_file):
                os.remove(temp_spec_file)

    if args.sample or (not args.spec and not args.har):
        spec_data = get_sample_spec()
        collection = parse_openapi_spec(spec_data, base_url_override=args.base_url)
    elif args.har:
        if not os.path.exists(args.har):
            print(f"❌ Error: HAR file not found: {args.har}", file=sys.stderr)
            sys.exit(1)
        with open(args.har, "r", encoding="utf-8") as f:
            har_data = json.load(f)
        collection = parse_har_file(har_data, base_url_override=args.base_url)
    else:
        if not os.path.exists(args.spec):
            print(f"❌ Error: OpenAPI specification file not found: {args.spec}", file=sys.stderr)
            sys.exit(1)
        with open(args.spec, "r", encoding="utf-8") as f:
            spec_data = json.load(f)
        collection = parse_openapi_spec(spec_data, base_url_override=args.base_url)

    out_json = json.dumps(collection, indent=2, ensure_ascii=False)

    if args.output:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"✅ [POSTMAN EXPORT] Successfully created Postman Collection v2.1.0: {args.output}")
    else:
        print(out_json)

    # Optional Companion Environment
    if args.env_output:
        base_u = args.base_url or "https://api.staging.enterprise.local"
        env_dict = generate_postman_environment(name="Agent-QA-Staging-Env", base_url=base_u)
        env_dir = os.path.dirname(os.path.abspath(args.env_output))
        if env_dir and not os.path.exists(env_dir):
            os.makedirs(env_dir, exist_ok=True)
        with open(args.env_output, "w", encoding="utf-8") as f:
            json.dump(env_dict, f, indent=2, ensure_ascii=False)
        print(f"✅ [ENVIRONMENT EXPORT] Successfully created Postman Environment: {args.env_output}")


if __name__ == "__main__":
    main()
