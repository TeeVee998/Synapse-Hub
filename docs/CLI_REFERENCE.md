# Agent-QA CLI & Tools Reference Manual

The `agent-skills` Hub provides a unified CLI utility `agent-qa` (and direct python scripts in `tools/`) to execute quality gates, linting, impact analysis, and log distillation.

---

## 1. Unified CLI Entrypoint (`agent-qa`)

When installed via `pip install -e .`, the `agent-qa` command is globally accessible:

```bash
agent-qa <command> [options]
```

### Supported Commands

| Command | Subsystem | Description | Example |
| :--- | :--- | :--- | :--- |
| `verify` | Quality Sentinel | Executes all 9 Quality Gates DoD validation | `agent-qa verify` |
| `lint` | Static Analysis | AST-level fake-pass and zero-assertion scanner | `agent-qa lint` |
| `heal` | Self-Healing | Queries zero-token semantic error memory cache | `agent-qa heal query "StaleElement"` |
| `distill` | Token Optimizer | Filters verbose CLI/Gradle logs by 95% | `agent-qa distill build.log` |
| `impact` | AST Knowledge | Analyzes impact of code changes | `agent-qa impact --git-diff` |
| `canary` | Resilience Arena | Injects failure vectors to test autonomous recovery | `agent-qa canary --run` |
| `version` | Hub Metadata | Displays installed Hub version and catalog summary | `agent-qa version` |

---

## 2. Direct Python Scripts Runbook

If running without global package installation, tools can be executed directly via Python:

### 2.1. Verify 9 Quality Gates (Gate 0 - Gate 8)
```bash
# Auto-detect mode (default: detects Hub vs Target Test Project)
python tools/verify_all.py

# Explicit mode selection
python tools/verify_all.py --mode hub      # QA Hub integrity validation
python tools/verify_all.py --mode target   # Target automation suite validation
```
- **Operational Modes:**
  - `--mode hub`: Validates QA Hub assets, skills, tools integrity, zero BOM, path portability, and universal credential security across repository files without requiring target test scripts.
  - `--mode target`: Enforces target automation suite standards including Clean POM across test scripts and credential encryption.
- **Gate 0:** Author Attribution & Provenance Guard (preserves MIT author notice).
- **Gate 1:** 100% UTF-8 No BOM check across all scripts, markdown, and config files.
- **Gate 2:** Path Portability (zero absolute host/machine directory paths).
- **Gate 3:** Clean POM & Flat Architecture (zero raw XPaths/CSS in test scripts).
- **Gate 4:** AI Docs & Artifacts Anti-Drift check (zero hallucinated tools/classes).
- **Gate 5:** Temporary file and properties artifact cleanup.
- **Gate 6:** Credential Security & Secret Scanner (zero hardcoded plaintext passwords or API tokens).
- **Gate 7:** Static Defect & AST Fake-Pass Sentinel.
- **Gate 8:** AST Micro-Mutation Sentinel (Requires Mutation Score >= 80%).

### 2.2. AST Fake-Pass Sentinel
```bash
python tools/infer_linter.py
```

### 2.3. Semantic Memory Cache & Negative Feedback Blacklist
```bash
# Initialize database with seed solutions and forbidden anti-patches
python tools/cache_resolver.py init

# Query pre-tested patches AND retrieve blacklisted anti-patches (0 tokens)
python tools/cache_resolver.py query --error "ElementClickInterceptedException"

# Learn a verified working solution (Positive Memory)
python tools/cache_resolver.py learn --error "Timeout" --cause "Slow API" --patch "waitForNetworkIdle()" --symptom "Spinner"

# Record a failed bug fix attempt into blacklist (Negative Memory)
python tools/cache_resolver.py record-failed --error "StaleElement" --patch "sleep(5000)" --reason "Still fails under network latency"
```

### 2.4. Log Distiller
```bash
python tools/distill_log.py execution.log
```
