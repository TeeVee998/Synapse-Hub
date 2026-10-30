---
description: Convert a Markdown Test Case table into a corporate-styled, formatted Excel spreadsheet (.xlsx) using the native tools/md_to_xlsx.py engine.
skills:
  - rbt-manual-testing
---

# /export_testcases_excel — Markdown to Styled Excel Converter

Converts any Markdown Test Case document or artifact into an enterprise-ready, professional Excel workbook (`.xlsx`) using the native Python openpyxl engine.

---

## Execution Command

```bash
# Export with default name (input.xlsx)
agent-qa export-excel path/to/test_cases.md

# Export with custom destination and worksheet title
agent-qa export-excel path/to/test_cases.md -o output_name.xlsx --sheet-name "Regression Suite"
```

## Features of Exported Workbooks

- **Navy Blue Header:** Dark blue fill (`#1F4E78`), bold white text, vertically centered.
- **Frozen Header:** Top row frozen (`A2`) for continuous scrolling.
- **AutoFilter:** Filter dropdowns automatically enabled on all columns.
- **Color-Coded Status Badges:**
  - `Risk Level`: High (Soft Red), Medium (Soft Yellow), Low (Soft Green).
  - `Priority`: Critical/High (Soft Red/Orange), Medium (Soft Yellow), Low (Soft Green).
  - `Automatable`: Yes (Soft Green), Partial (Soft Yellow), No (Soft Gray).
- **Auto-Formatting:** Multi-line `<br>` tags converted to true Excel newlines with text wrapping and optimized column widths.
