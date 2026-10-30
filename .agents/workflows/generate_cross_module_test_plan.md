---
description: Analyze end-to-end user journeys traversing multiple interconnected modules, construct Data Flow Diagrams, and generate optimized Pairwise (All-Pairs) combinatorial test matrices.
skills:
  - clean-pom-crafter
  - e2e-testing-patterns
  - synthetic-test-data-generator
---

# /generate_cross_module_test_plan — Cross-Module Analysis & Pairwise Matrix

Use this workflow when a business feature spans across multiple sequential modules, where each module has distinct option dimensions and combinatorial outputs determine the final result.

---

## 1. Operational Modes

- **DOCUMENT Mode (Default):** Ingests functional specifications, user journey maps, or architecture documents.
- **BROWSER Mode:** Probes the live web application using headless Playwright to discover sequential UI modules and input dimensions.

---

## 2. Execution Pipeline

### Step 1: Sequential Module Mapping & Data Flow
1. Map the end-to-end workflow chain (e.g., Module 1: Customer Profile -> Module 2: Billing & Currency -> Module 3: Tax Profile -> Module 4: Invoice Generation).
2. Generate a Mermaid Data Flow Diagram illustrating data dependencies between modules.

### Step 2: Dimension Catalog & Constraints Extraction
1. List all configurable dimensions and allowed values per module.
2. Identify mutual exclusions, invalid business combinations, and hard constraints.

### Step 3: Combinatorial Matrix Synthesis (Pairwise / All-Pairs)
1. Apply **Pairwise Testing (All-Pairs)** reduction to compress multi-dimensional exponential combinations (e.g., reduce $3 \times 4 \times 3 \times 2 \times 4 = 288$ combinations down to ~20-25 optimal test sets covering 100% of two-way interactions).
2. Format the output matrix with columns: `#`, `Module 1`, `Module 2`, ..., `Expected Result`, `Priority`.

### Step 4: Verification Checkpoint
- Present the reduced Pairwise Matrix to the user for validation and sign-off before test case or test data synthesis.
