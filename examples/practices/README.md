# Industry QA Practice Corpus & Benchmarks

This directory contains real-world enterprise requirements specifications and test case artifacts across diverse domains (CRM, E-Commerce, Project Management, and REST APIs).

## Structure

```text
examples/practices/
├── requirements/
│   ├── crm/                 # Modular CRM functional specs (Auth, Customers, Projects, Contracts, Tasks)
│   ├── ecommerce/           # Category, catalog, and brand management business rules
│   └── jira/                # Jira epic/story export samples with user story attachments
└── testcases/
    ├── crm/                 # Standard enterprise UI manual test cases (AI-RBT format)
    └── api/                 # OpenAPI / REST API acceptance matrices
```

## Purpose

1. **Benchmark AI Test Generation:** Serves as golden inputs to evaluate prompt engineering and AI-RBT generation workflows (`/generate_manual_testcases_rbt`, `/generate_testcases_from_requirements`).
2. **Offline Few-Shot Learning:** Realistic domain context for model fine-tuning and in-context learning without leaking proprietary customer data.
3. **Excel Export Validation:** Source markdown tables for verifying `agent-qa export-excel` / `tools/md_to_xlsx.py`.
