---
description: Generate concrete combinatorial test data sets (JSON, CSV, Markdown) covering all parameter combinations from a cross-module dimension matrix or Pairwise specification.
skills:
  - synthetic-test-data-generator
---

# /generate_combinatorial_test_data — Combinatorial Test Data Synthesis

Converts an abstract dimension matrix or Pairwise specification into concrete, idempotent synthetic test data fixtures ready for automation or manual execution.

---

## 1. Input Requirements

Provide either:
- A Markdown table of dimensions/values from `/generate_cross_module_test_plan`.
- A list of parameters with allowed values, boundaries, and negative test values.

---

## 2. Output Modes

1. **GENERATE Mode (File Export):**
   - Synthesizes formatted data records in JSON, CSV, or Markdown.
   - Enforces unique dynamic prefixes (`AUTO_<timestamp>`) to prevent database unique-constraint collisions.
2. **PIPELINE Mode (Live Seeding):**
   - Dispatches browser actions or API seeders (`tools/db_sandbox.py`) to create records directly in the target environment.
   - Automatically pairs each creation step with a teardown cleanup action.
