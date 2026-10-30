---
name: file-and-report-validator
description: "Validate downloaded and uploaded files (Excel, CSV, PDF) schemas and tabular integrity."
---

# File & Report Validator Skill

> **Target:** Eliminate superficial testing of file exports and imports by inspecting and asserting exact file contents, schemas, formulas, and values across Excel, CSV, and PDF formats.

---

## 1. Core Principles

1. **Verify Binary Contents, Not Just Download Events:**
   - Catching the browser `download` event is insufficient. The downloaded file must be opened, parsed, and its tabular records cross-referenced against expected database or UI table states.
2. **Schema & Header Conformance:**
   - Assert exact column headers, cell data formats (dates, currencies, numeric precision), and sheet names.
3. **Idempotent File Lifecycle:**
   - Store temporary test downloads in a sandboxed scratch folder and purge them during teardown.

---

## 2. Standard Playwright Download Handling

```typescript
import { test, expect } from '@playwright/test';
import path from 'path';

test('export and verify financial report', async ({ page }) => {
  const downloadPromise = page.waitForEvent('download');
  await page.click('button#export-excel');
  const download = await downloadPromise;

  const savePath = path.join('temp_downloads', download.suggestedFilename());
  await download.saveAs(savePath);

  expect(download.suggestedFilename()).toMatch(/^Report_\d{8}\.xlsx$/);
});
```

---

## 3. Deep Content Inspection Recipes (Python)

### Pattern A: Excel (.xlsx / .xls) Schema & Data Assertion
```python
import pandas as pd

def validate_excel_report(file_path: str, expected_min_rows: int = 1):
    df = pd.read_excel(file_path)
    
    # 1. Assert header schema
    expected_headers = ["ID", "Customer Name", "Total Amount", "Status"]
    assert list(df.columns) == expected_headers, f"Header mismatch: {df.columns}"
    
    # 2. Assert row counts and non-empty values
    assert len(df) >= expected_min_rows, f"Expected at least {expected_min_rows} rows, got {len(df)}"
    assert not df["ID"].isnull().any(), "Found NULL values in ID column"
    print(f"[PASS] Successfully verified {len(df)} rows in {file_path}")
```

### Pattern B: CSV Chunk Streaming (For Big Data Exports > 100k Rows)
```python
import csv

def validate_large_csv_stream(file_path: str, expected_header: list):
    row_count = 0
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == expected_header, f"CSV Header mismatch: {header}"
        for row in reader:
            row_count += 1
            assert len(row) == len(header), f"Malformed row at line {row_count}"
    print(f"[PASS] Verified {row_count} streamed CSV rows without memory overflow.")
```

### Pattern C: PDF Document Text & Metadata Extraction
```python
import pypdf

def assert_pdf_contains_text(pdf_path: str, expected_keywords: list):
    reader = pypdf.PdfReader(pdf_path)
    assert len(reader.pages) > 0, "PDF is empty (0 pages)!"

    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    for kw in expected_keywords:
        assert kw in full_text, f"PDF assertion failed: Keyword '{kw}' missing in {pdf_path}"
    print(f"[PASS] Verified keywords {expected_keywords} across {len(reader.pages)} PDF pages.")
```
