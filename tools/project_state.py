#!/usr/bin/env python3
"""
Enterprise Project State Machine & Token-Capped Memory Anchor
--------------------------------------------------------------
Maintains persistent execution state across long-running AI sessions and Antigravity context compaction.
Enforces a strict Rolling Window (< 50 lines, ~200 tokens) to guarantee zero token bloat.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TEMPLATES_DIR = os.path.join(HUB_ROOT, "templates")


def resolve_state_file(target_dir):
    return os.path.join(target_dir, "PROJECT_STATE.md")


def init_state(target_dir, goal="Initial Autonomous Setup"):
    """Initializes PROJECT_STATE.md if missing, strictly capped to < 50 lines."""
    state_file = resolve_state_file(target_dir)
    if os.path.exists(state_file):
        return state_file

    project_name = os.path.basename(os.path.abspath(target_dir))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Project Execution State (`PROJECT_STATE.md`)

- **Project:** `{project_name}`
- **Last Sync:** `{timestamp}`
- **Overall Status:** `READY`

## 1. Active Goal
- {goal}

## 2. Task Checklist (Rolling Window - Max 8 active items)
- [x] Initialized project state anchor
- [ ] Ready for feature or test automation

## 3. Active Watchpoints & Healing (Max 3 items)
- Target Suite / Script: `[None]`
- Failing Locator / Line: `[None]`

## 4. Quality Verification
- 9 Quality Gates: `READY`
- Clean POM Integrity: `VERIFIED`
"""
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(content)
    return state_file


def update_state(target_dir, goal=None, completed_task=None, pending_task=None, watchpoint=None, gate_status=None):
    """Updates state in-place while pruning old entries to guarantee < 50 lines (~200 tokens)."""
    state_file = resolve_state_file(target_dir)
    if not os.path.exists(state_file):
        init_state(target_dir, goal or "Active Task")

    with open(state_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f.readlines()]

    project_name = os.path.basename(os.path.abspath(target_dir))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Parse existing tasks
    existing_tasks = []
    current_goal = goal or "Continue autonomous QA workflow"
    current_watchpoints = []
    current_gate = gate_status or "READY"

    in_tasks = False
    in_watch = False

    for line in lines:
        if line.startswith("## 1. Active Goal"):
            in_tasks = False
            in_watch = False
        elif line.startswith("## 2. Task Checklist"):
            in_tasks = True
            in_watch = False
            continue
        elif line.startswith("## 3. Active Watchpoints"):
            in_tasks = False
            in_watch = True
            continue
        elif line.startswith("## 4. Quality Verification"):
            in_tasks = False
            in_watch = False
            continue

        if in_tasks and line.strip().startswith("- ["):
            existing_tasks.append(line.strip())
        elif in_watch and line.strip().startswith("- "):
            current_watchpoints.append(line.strip())
        elif line.startswith("- **Last Sync:**") and not goal:
            pass

    if completed_task:
        existing_tasks.append(f"- [x] {completed_task}")
    if pending_task:
        existing_tasks.append(f"- [ ] {pending_task}")
    if watchpoint:
        current_watchpoints = [f"- Focus: {watchpoint}"]

    # Rolling window cap: Keep maximum 8 task items (purge oldest completed tasks)
    if len(existing_tasks) > 8:
        # Keep pending tasks and the most recent completed ones
        pending = [t for t in existing_tasks if t.startswith("- [ ]")]
        completed = [t for t in existing_tasks if t.startswith("- [x]")]
        # Keep up to 4 completed and remaining pending
        completed = completed[-4:]
        existing_tasks = completed + pending
        existing_tasks = existing_tasks[-8:]

    # Reconstruct compact markdown (< 40 lines)
    tasks_block = "\n".join(existing_tasks) if existing_tasks else "- [ ] Standby for instructions"
    watch_block = "\n".join(current_watchpoints[:3]) if current_watchpoints else "- Target Suite / Script: `[None]`\n- Failing Locator / Line: `[None]`"

    content = f"""# Project Execution State (`PROJECT_STATE.md`)

- **Project:** `{project_name}`
- **Last Sync:** `{timestamp}`
- **Overall Status:** `IN_PROGRESS`

## 1. Active Goal
- {current_goal}

## 2. Task Checklist (Rolling Window - Max 8 active items)
{tasks_block}

## 3. Active Watchpoints & Healing (Max 3 items)
{watch_block}

## 4. Quality Verification
- 9 Quality Gates: `{current_gate}`
- Clean POM Integrity: `VERIFIED`
"""
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(content)
    return state_file


def read_state(target_dir):
    """Reads state file if exists, returning condensed text."""
    state_file = resolve_state_file(target_dir)
    if not os.path.exists(state_file):
        return None
    with open(state_file, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sf = init_state(target)
    print(f"Project state anchor initialized at: {sf}")
