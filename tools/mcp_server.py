#!/usr/bin/env python3
"""
Enterprise Model Context Protocol (MCP) Standard Server
-------------------------------------------------------
Exposes centralized tools/ capabilities as standardized JSON-RPC 2.0 MCP Tools
compatible with Google Antigravity, Cursor, Claude Desktop, Windsurf, and any MCP client.
Communicates via standard JSON-RPC stdio.
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, List

# Enforce UTF-8 stdio encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, SCRIPT_DIR)

import verify_all
import analyze_project
import setup_project
import auto_heal
import safety_firewall
import api_drift_sentinel
import cache_resolver
import distill_log
import micro_mutator
import heal_pr_automator
import matrix_sharder
import tms_sync_bridge
import db_sandbox
import traffic_session_converter
import visual_som_helper

SERVER_NAME = "enterprise-agent-qa"
SERVER_VERSION = "2.0.0"

MCP_TOOLS = [
    {
        "name": "verify_all_gates",
        "description": "Validates the 8 Quality Gates Definition of Done (UTF-8, paths, Clean POM, AI docs, blacklist, security, infer linter, micro-mutator).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Absolute or relative path to the target repository. Defaults to CWD."}
            }
        }
    },
    {
        "name": "analyze_project",
        "description": "Executes 5-in-1 project health and AST intelligence analysis, creating PROJECT_HEALTH_REPORT.md and repo_map.txt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Target project repository directory to audit."}
            }
        }
    },
    {
        "name": "setup_project",
        "description": "Autonomous 1-click bootstrap of any test project: detects stack, generates PROJECT_AI_GUIDE.md, installs Git hook, and maps AST.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Path to target project to bootstrap."}
            }
        }
    },
    {
        "name": "auto_heal_failure",
        "description": "Diagnoses test failures in 0.1s from JUnit XML and queries semantic memory cache for proven patches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_dir": {"type": "string", "description": "Target project root directory."},
                "junit_xml_path": {"type": "string", "description": "Optional direct path to failing JUnit XML report."}
            }
        }
    },
    {
        "name": "check_action_safety",
        "description": "Action Safety Firewall: verifies whether an intended UI action (click, fill) touches destructive elements (Delete, Pay, Drop).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "description": "Action type (e.g. click, fill, submit)."},
                "element_text": {"type": "string", "description": "Text or label of target DOM element."},
                "selector": {"type": "string", "description": "CSS or XPath selector of element."},
                "force": {"type": "boolean", "description": "Force bypass firewall."}
            }
        }
    },
    {
        "name": "check_contract_drift",
        "description": "Compares two OpenAPI / Swagger specifications and detects breaking changes (removed endpoints, changed types, newly required params).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "old_spec_path": {"type": "string", "description": "Path to baseline OpenAPI JSON file."},
                "new_spec_path": {"type": "string", "description": "Path to current OpenAPI JSON file."}
            },
            "required": ["old_spec_path", "new_spec_path"]
        }
    },
    {
        "name": "query_memory_cache",
        "description": "Queries the 0-token SQLite semantic memory cache for known UI exceptions and proven repair patches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_signature": {"type": "string", "description": "Exception trace or error message to lookup."}
            },
            "required": ["error_signature"]
        }
    },
    {
        "name": "distill_log",
        "description": "Filters verbose CLI or Gradle build logs by 95%, retaining only actionable stacktraces and pointers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_log_text": {"type": "string", "description": "Raw terminal log output to compress."}
            },
            "required": ["raw_log_text"]
        }
    },
    {
        "name": "run_micro_mutation",
        "description": "Injects AST micro-mutants (flipping operators, booleans) to verify that AI-generated test assertions are robust.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_path": {"type": "string", "description": "Path to test script or directory to mutate."}
            }
        }
    },
    {
        "name": "plan_healing_pr",
        "description": "Calculates composite confidence score for healed locators and formats an automated Pull Request draft.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_file": {"type": "string", "description": "Page Class path."},
                "old_locator": {"type": "string", "description": "Original stale selector."},
                "new_locator": {"type": "string", "description": "Healed replacement selector."},
                "aom_score": {"type": "number", "description": "AOM match score 0.0-1.0."},
                "spatial_score": {"type": "number", "description": "Spatial score 0.0-1.0."},
                "visual_score": {"type": "number", "description": "Visual SSIM score 0.0-1.0."}
            },
            "required": ["page_file", "old_locator", "new_locator"]
        }
    },
    {
        "name": "shard_test_matrix",
        "description": "Distributes test cases evenly across N parallel CI/CD runners using Duration-Balanced Bin-Packing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_dir": {"type": "string", "description": "Target project root directory."},
                "num_shards": {"type": "integer", "description": "Number of parallel workers (default 4)."}
            }
        }
    },
    {
        "name": "pull_alm_story",
        "description": "Pulls User Story and Acceptance Criteria (Given-When-Then) from Jira, Xray, or TestRail for test generation context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "ALM Issue Key (e.g. PROJ-1042)."}
            },
            "required": ["issue_key"]
        }
    },
    {
        "name": "report_alm_defect",
        "description": "Creates an automated Bug Ticket in Jira/TMS with full diagnostic reproduction steps, stack trace, and screenshot attachments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_key": {"type": "string", "description": "Target project key (e.g. PROJ)."},
                "test_case_id": {"type": "string", "description": "Failing test case ID."},
                "summary": {"type": "string", "description": "Defect summary."},
                "error_message": {"type": "string", "description": "Exact failure error message."},
                "stack_trace": {"type": "string", "description": "Exception stack trace."},
                "screenshot_path": {"type": "string", "description": "Path to FAILED screenshot image."}
            },
            "required": ["project_key", "test_case_id", "summary", "error_message"]
        }
    },
    {
        "name": "manage_db_sandbox",
        "description": "Zero-pollution ephemeral database manager: creates baseline snapshot, restores pristine DB state, or executes transaction savepoints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["snapshot", "restore", "audit_and_purge"], "description": "Sandbox operation to execute."},
                "db_path": {"type": "string", "description": "Path to database file (optional for SQLite)."},
                "snapshot_id": {"type": "string", "description": "Snapshot identifier (default: pristine_baseline)."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "convert_traffic_session",
        "description": "Shift-Right Replay: Transforms recorded HTTP Archive (.har) or RUM session into PII-sanitized Playwright test suite.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "string", "description": "Path to .har or JSON network session file."},
                "test_name": {"type": "string", "description": "Generated test suite name."}
            },
            "required": ["input_file"]
        }
    },
    {
        "name": "resolve_visual_som_coordinates",
        "description": "Multimodal Vision Grounding: Resolves click coordinates (x, y) on HTML5 Canvas or Shadow DOM using Set-of-Marks (SoM).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to screenshot image."},
                "target_label": {"type": "string", "description": "Target element label or text."},
                "mark_id": {"type": "integer", "description": "Specific Mark ID to click."}
            }
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> str:
    """Executes the corresponding internal tool function and returns text response."""
    if name == "verify_all_gates":
        repo = arguments.get("repo_path") or os.getcwd()
        mode = verify_all.detect_repo_mode(repo)
        passed = True
        gates = [
            ("Gate 1: UTF-8 No BOM", verify_all.gate_1_bom_check),
            ("Gate 2: Path Portability", verify_all.gate_2_path_portability),
            ("Gate 3: Clean POM", verify_all.gate_3_clean_pom),
            ("Gate 4: AI Docs Linter", verify_all.gate_4_ai_docs_lint),
            ("Gate 5: Temp Blacklist", verify_all.gate_5_cleanup_blacklist),
            ("Gate 6: Credential Security", verify_all.gate_6_credential_security),
            ("Gate 7: Infer Linter", verify_all.gate_7_infer_linter),
            ("Gate 8: AST Mutation Sentinel", verify_all.gate_8_micro_mutator),
        ]
        results = []
        for g_name, g_fn in gates:
            res = g_fn(repo, mode=mode)
            results.append(f"{g_name}: {'PASS' if res else 'FAIL'}")
            if not res:
                passed = False
        summary = "100% ALL 8 GATES PASSED" if passed else "VERIFICATION FAILED"
        return f"[{summary}]\n" + "\n".join(results)

    elif name == "analyze_project":
        repo = arguments.get("repo_path") or os.getcwd()
        code = analyze_project.run_full_analysis(repo)
        return f"Project Analysis finished with exit code {code}. Report saved at {os.path.join(repo, 'PROJECT_HEALTH_REPORT.md')}."

    elif name == "setup_project":
        repo = arguments.get("repo_path") or os.getcwd()
        code = setup_project.run_setup(repo)
        return f"Project Setup finished with exit code {code}."

    elif name == "auto_heal_failure":
        target = arguments.get("target_dir") or os.getcwd()
        xml = arguments.get("junit_xml_path")
        plan = auto_heal.diagnose_and_plan_heal(target, xml)
        return json.dumps(plan, indent=2)

    elif name == "check_action_safety":
        auth = safety_firewall.inspect_and_authorize(
            action_type=arguments.get("action_type", "click"),
            text=arguments.get("element_text", ""),
            selector=arguments.get("selector", ""),
            force=arguments.get("force", False)
        )
        return json.dumps(auth, indent=2)

    elif name == "check_contract_drift":
        old_data = api_drift_sentinel.load_spec(arguments["old_spec_path"])
        new_data = api_drift_sentinel.load_spec(arguments["new_spec_path"])
        analysis = api_drift_sentinel.compare_specs(old_data, new_data)
        return api_drift_sentinel.generate_markdown_report(analysis, arguments["old_spec_path"], arguments["new_spec_path"])

    elif name == "query_memory_cache":
        res = cache_resolver.query_cache(arguments["error_signature"])
        return json.dumps(res, indent=2) if res else "No matching solution found in memory cache."

    elif name == "distill_log":
        distilled = distill_log.distill_log_content(arguments["raw_log_text"])
        return distilled

    elif name == "run_micro_mutation":
        target = arguments.get("target_path") or os.getcwd()
        mutants = micro_mutator.scan_directory_for_mutants(target) if os.path.isdir(target) else micro_mutator.generate_mutants_for_code(open(target).read(), target)
        return json.dumps({"total_mutants": len(mutants), "sample_mutants": mutants[:5]}, indent=2)

    elif name == "plan_healing_pr":
        conf = heal_pr_automator.calculate_healing_confidence(
            arguments.get("aom_score", 0.95),
            arguments.get("spatial_score", 0.90),
            arguments.get("visual_score", 0.92)
        )
        pr = heal_pr_automator.generate_pr_draft(arguments["page_file"], arguments["old_locator"], arguments["new_locator"], conf)
        return json.dumps({"confidence": conf, "pr": pr}, indent=2)

    elif name == "shard_test_matrix":
        target = arguments.get("target_dir") or os.getcwd()
        num_shards = arguments.get("num_shards", 4)
        files = matrix_sharder.find_test_files(target)
        shards = matrix_sharder.shard_tests_lpt(files, target, num_shards)
        return json.dumps({"total_tests": len(files), "shards": shards}, indent=2)

    elif name == "pull_alm_story":
        bridge = tms_sync_bridge.TMSBridge()
        story = bridge.pull_story_acceptance_criteria(arguments["issue_key"])
        return json.dumps(story, indent=2)

    elif name == "report_alm_defect":
        bridge = tms_sync_bridge.TMSBridge()
        ticket = bridge.report_defect(
            project_key=arguments["project_key"],
            test_case_id=arguments["test_case_id"],
            summary=arguments["summary"],
            error_message=arguments["error_message"],
            stack_trace=arguments.get("stack_trace", ""),
            screenshot_path=arguments.get("screenshot_path", "")
        )
        return json.dumps(ticket, indent=2)

    elif name == "manage_db_sandbox":
        action = arguments["action"]
        sandbox = db_sandbox.DBSandbox(db_path=arguments.get("db_path", ""))
        if action == "snapshot":
            res = sandbox.create_snapshot(arguments.get("snapshot_id", "pristine_baseline"))
        elif action == "restore":
            res = sandbox.restore_snapshot(arguments.get("snapshot_id", "pristine_baseline"))
        elif action == "audit_and_purge":
            res = sandbox.audit_and_purge_pollution()
        else:
            raise ValueError(f"Unknown sandbox action: {action}")
        return json.dumps(res, indent=2)

    elif name == "convert_traffic_session":
        input_file = arguments["input_file"]
        test_name = arguments.get("test_name", "ProductionTrafficReplay")
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        converter = traffic_session_converter.TrafficConverter(sanitize_pii=True)
        requests = converter.parse_har(data)
        test_code = converter.generate_playwright_test(requests, test_name=test_name)
        return json.dumps({"total_requests": len(requests), "generated_test": test_code}, indent=2)

    elif name == "resolve_visual_som_coordinates":
        helper = visual_som_helper.VisualSoMHelper()
        img = arguments.get("image_path", "screenshot.png")
        lbl = arguments.get("target_label")
        mid = arguments.get("mark_id")
        marked_img, marks_map = helper.generate_som_overlay(img, [])
        resolved = helper.resolve_mark_coordinates(marks_map, target_mark_id=mid, target_label=lbl)
        return json.dumps({"marked_image": marked_img, "resolved_target": resolved}, indent=2)

    raise ValueError(f"Unknown MCP tool: {name}")


def process_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Processes an incoming JSON-RPC 2.0 message."""
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION
                }
            }
        }

    elif method in ("notifications/initialized", "initialized"):
        return None  # No response needed for notification

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": MCP_TOOLS
            }
        }

    elif method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            output_text = handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": output_text
                        }
                    ],
                    "isError": False
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing {tool_name}: {str(e)}\n{traceback.format_exc()}"
                        }
                    ],
                    "isError": True
                }
            }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }


def run_stdio_server():
    """Runs the MCP server over standard input/output."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            response = process_message(msg)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
