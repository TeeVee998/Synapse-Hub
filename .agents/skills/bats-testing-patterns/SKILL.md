---
name: bats-testing-patterns
description: "Test bash/sh scripts, CLI tools, and CI/CD pipelines with Bats. Use when writing Bash automation tests with the BATS framework."
---

# Bats Testing Patterns (Bash Automated Testing System)

Comprehensive test engineering standard for validating shell scripts, CI/CD scripts (`.sh`), CLI wrappers, and DevOps automation using Bats-core.

---

## 1. Core Principles

1. **Deterministic Exit Codes:** Every script assertion must explicitly assert `$status` (0 for success, non-zero for explicit failure vectors).
2. **Standard Output & Error Isolation:** Assert exact error strings in `${lines[@]}` or `$output`.
3. **Sandbox Filesystem:** Never mutate user home or production directories. Use `$BATS_TEST_TMPDIR` for all temporary files and fixtures.
4. **Mock External CLI Commands:** Intercept destructive CLI commands (`curl`, `docker`, `kubectl`, `git push`) by prepending a mock binary directory to `$PATH`.

---

## 2. Standard Test Architecture & Setup

```bash
#!/usr/bin/env bats

setup() {
  # Load bats helper libraries if available
  load 'test_helper/bats-support/load' || true
  load 'test_helper/bats-assert/load' || true

  # Create an isolated sandbox directory per test
  TEST_DIR="$(mktemp -d "${BATS_TMPDIR}/bats_test.XXXXXX")"
  export TEST_DIR
  cd "$TEST_DIR"
}

teardown() {
  # Ensure clean sandbox teardown
  rm -rf "$TEST_DIR"
}
```

---

## 3. Production Test Patterns

### Pattern A: Exit Code and Output Verification
```bash
@test "script fails gracefully when required parameter is missing" {
  run ./scripts/deploy.sh
  [ "$status" -eq 1 ]
  [[ "$output" =~ "ERROR: Missing --target environment" ]]
}

@test "script outputs version correctly on --version flag" {
  run ./scripts/deploy.sh --version
  [ "$status" -eq 0 ]
  [ "${lines[0]}" = "deploy.sh version 2.4.0" ]
}
```

### Pattern B: Mocking Destructive CLI Tools
```bash
@test "mock curl API failure triggers automatic retry loop" {
  MOCK_DIR="${TEST_DIR}/bin"
  mkdir -p "$MOCK_DIR"

  # Create mock curl returning HTTP 503
  cat << 'EOF' > "${MOCK_DIR}/curl"
#!/bin/bash
echo "HTTP/1.1 503 Service Unavailable" >&2
exit 22
EOF
  chmod +x "${MOCK_DIR}/curl"

  # Prepend mock path
  PATH="${MOCK_DIR}:${PATH}" run ./scripts/sync_data.sh --retries 2
  [ "$status" -ne 0 ]
  [[ "$output" =~ "Retry attempt 2 failed" ]]
}
```

### Pattern C: File Creation & Mutation Verification
```bash
@test "script generates valid JSON report on completion" {
  run ./scripts/generate_report.sh --output "${TEST_DIR}/summary.json"
  [ "$status" -eq 0 ]
  [ -f "${TEST_DIR}/summary.json" ]
  run jq '.status' "${TEST_DIR}/summary.json"
  [ "$output" = '"SUCCESS"' ]
}
```

---

## 4. CI/CD Pipeline Execution
```bash
# Execute full Bats test suite with JUnit report output for CI
bats test/*.bats --formatter junit > test-results.xml
```
