---
name: graphify-impact-analyzer
description: >-
  AST Knowledge Graph exploration, Architecture Navigation, and Zero-Waste Test Impact Analysis
  across multi-module test cases using Graphify and tools/test_impact.py.
---

# Graphify Impact Analyzer — AST Knowledge Graph Navigation & Zero-Waste Impact Analysis

Specialized skill for navigating the codebase's AST Knowledge Graph (`graphify-out/graph.json`), executing sub-second dependency queries, and performing **Zero-Waste Test Impact Analysis** to execute only tests affected by code modifications.

---

## 1. Core Capabilities

1. **Deterministic AST Parsing (Zero API Cost):**
   - Automatically maps files, classes, methods, and test scripts into `graphify-out/graph.json`.
   - Replaces blind, expensive full-corpus grepping with targeted graph traversals.

2. **Automated Test Impact Analysis (Zero Waste):**
   - When any Page Class in `Keywords/<project>/pages/` or `pages/*.ts` is modified, the impact analyzer computes reverse dependencies in `graph.json`.
   - Pinpoints the exact subset of Test Cases affected, reducing CI/CD execution time by up to 90+%.

3. **God Node & Technical Debt Detection:**
   - Detects over-coupled classes and guides safe, modular refactoring.

---

## 2. Test Impact Analysis Workflow (`tools/test_impact.py`)

Run impact analysis before dispatching test suites:

### 2.1. Check Impact of Modified Page Class
```bash
python3 tools/test_impact.py -f Keywords/pages/CategoryPage.groovy
```
*Output:*
- Target File: `Keywords/pages/CategoryPage.groovy`
- Directly Impacted: **12 / 250 TCs**
- Skipped: **238 TCs**
- Time Saved: **95.2%**

### 2.2. Automatically Analyze Git Changes
```bash
python3 tools/test_impact.py --git-diff
```

### 2.3. Output Machine-Readable JSON (For CI/CD Pipelines)
```bash
python3 tools/test_impact.py --git-diff --json
```

---

## 3. Knowledge Graph CLI Navigation Commands

| Command | Purpose | Example |
|---|---|---|
| `graphify explain "<Node>"` | Explain a Page Class or Script and its connections | `graphify explain "UserAdminPage"` |
| `graphify path "<A>" "<B>"` | Find shortest path between two classes/scripts | `graphify path "LoginPage" "BasePage"` |
| `graphify query "<Concept>"` | Query a concept or test case subgraph | `graphify query "TC-101"` |
| `graphify update .` | Refresh AST graph after code modifications (No LLM needed) | `graphify update .` |

---

## 4. Visual Artifacts

- **2D/3D Interactive Visualizer:** `graphify-out/graph.html`
- **Call-flow & Mermaid Diagrams:** `graphify-out/callflow.html`
- **Architectural Summary Report:** `graphify-out/GRAPH_REPORT.md`

---

## 5. Agent Operational Guardrails

1. **Before modifying any Page Class:** Run `python3 tools/test_impact.py -f <path>` to identify dependent Test Cases.
2. **After modifying code:** Run `graphify update .` to keep the knowledge graph synchronized.
3. **DoD Compliance:** Always verify that all changes pass `python3 tools/verify_all.py`.
