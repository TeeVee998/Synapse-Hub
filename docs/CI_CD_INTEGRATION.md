# CI/CD Integration Guide — Synapse-Hub Enterprise QA

This guide explains how to integrate Synapse-Hub quality gates (`verify_all.py`, `infer_linter`, AST mutator, Clean POM checks) directly into target project CI/CD pipelines without local filesystem dependencies.

---

## 1. Zero-Install NPX Integration (Recommended)

Since `synapse-hub` is distributed via NPM Registry and GitHub Packages, target CI pipelines do not need to clone the hub repository manually. `npx` dynamically fetches and executes the CLI engine.

### GitHub Actions Workflow (`.github/workflows/synapse_qa.yml`)

```yaml
name: Synapse QA Quality Gate

on:
  push:
    branches: [ main, develop, master ]
  pull_request:
    branches: [ main, develop, master ]

jobs:
  quality-gate:
    name: 9 Quality Gates DoD Verification
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Project Source
        uses: actions/checkout@v4

      - name: Setup Node.js & Python
        uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Verify 9 Quality Gates
        run: npx synapse-hub verify
```

### GitLab CI (`.gitlab-ci.yml`)

```yaml
synapse-qa-gate:
  stage: test
  image: node:20-bookworm
  before_script:
    - apt-get update && apt-get install -y python3 python3-pip
  script:
    - npx synapse-hub verify
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## 2. Git Submodule Integration (For Air-Gapped / Private SCM)

If your enterprise network restricts public NPM registry access, mount `Synapse-Hub` as a Git Submodule inside the target repository:

```bash
# Add submodule into target project
git submodule add https://github.com/TeeVee998/Synapse-Hub.git .synapse-hub
```

In your CI pipeline:
```bash
git submodule update --init --recursive
python .synapse-hub/tools/verify_all.py
```

---

## 3. Python Git / Pip Package Integration

Target runners with Python 3.9+ can install `synapse-hub` directly from git:

```bash
pip install git+https://github.com/TeeVee998/Synapse-Hub.git
agent-qa verify
```

---

## 4. Available CI Subcommands

| Command | Purpose | SLA / Exit Code |
| :--- | :--- | :--- |
| `npx synapse-hub verify` | Executes all 9 Quality Gates DoD | Exits `0` if all PASS; non-zero if any FAIL. |
| `npx synapse-hub lint` | Meta Infer-style static defect and fake-pass scan | Fails if 0-assert tests or empty catches exist. |
| `npx synapse-hub mutate --min-score 80` | AST Micro-Mutation verification | Fails if test assertion score < 80%. |
| `npx synapse-hub analyze` | Comprehensive 5-in-1 health audit | Outputs health score and JSON/Markdown artifacts. |
