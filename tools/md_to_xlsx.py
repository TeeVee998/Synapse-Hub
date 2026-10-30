#!/usr/bin/env python3
"""
Markdown to Excel (.xlsx) Enterprise Converter
------------------------------------------------
Parses Markdown Test Case tables and converts them into professional,
styled Excel workbooks with:
  - Corporate header styling (Navy Blue, bold, centered)
  - Color-coded Risk Level (High=Red, Med=Yellow, Low=Green)
  - Color-coded Priority (Critical/High/Med/Low) and Automatable badges
  - Frozen top header row (A2 freeze pane)
  - AutoFilter enabled across all columns
  - Smart column widths and multi-line text wrapping (replaces <br> with newlines)
"""

import os
import sys
import re
import argparse
from typing import List, Dict, Any, Tuple

# UTF-8 terminal encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def clean_cell_content(cell: str) -> str:
    """Cleans Markdown cell formatting: replaces <br> with newlines, strips backticks."""
    text = cell.strip()
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # Strip leading/trailing pipes if present in split artifact
    text = text.strip()
    return text


def parse_markdown_tables(content: str) -> List[Tuple[List[str], List[List[str]]]]:
    """
    Parses all Markdown tables in a string.
    Returns a list of tuples: (headers, rows).
    """
    lines = content.splitlines()
    tables = []
    
    current_header = None
    current_rows = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            if in_table and current_header and current_rows:
                tables.append((current_header, current_rows))
                current_header = None
                current_rows = []
                in_table = False
            continue
            
        # Split cells
        raw_cells = [c.strip() for c in stripped[1:-1].split('|')]
        
        # Check if separator row (|---|---|)
        if all(re.match(r'^\s*:?-+:?\s*$', c) for c in raw_cells if c):
            in_table = True
            continue
            
        if not in_table:
            # First line with pipes is potential header
            current_header = [clean_cell_content(c) for c in raw_cells]
        else:
            # Data row
            cleaned_row = [clean_cell_content(c) for c in raw_cells]
            # Ensure row length matches header
            if current_header:
                if len(cleaned_row) < len(current_header):
                    cleaned_row.extend([''] * (len(current_header) - len(cleaned_row)))
                elif len(cleaned_row) > len(current_header):
                    cleaned_row = cleaned_row[:len(current_header)]
            current_rows.append(cleaned_row)
            
    if in_table and current_header and current_rows:
        tables.append((current_header, current_rows))
        
    return tables


def create_styled_excel(tables: List[Tuple[List[str], List[List[str]]]], output_path: str, sheet_title: str = "Test Cases") -> int:
    """Builds and styles the Excel workbook using openpyxl."""
    if not OPENPYXL_AVAILABLE:
        raise RuntimeError("openpyxl is not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]  # Excel limits sheet names to 31 chars

    # Palette
    NAVY_BLUE = "1F4E78"
    WHITE = "FFFFFF"
    BORDER_COLOR = "D9D9D9"
    
    # Styles
    header_fill = PatternFill(start_color=NAVY_BLUE, end_color=NAVY_BLUE, fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color=WHITE)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    cell_border = Border(
        left=Side(style='thin', color=BORDER_COLOR),
        right=Side(style='thin', color=BORDER_COLOR),
        top=Side(style='thin', color=BORDER_COLOR),
        bottom=Side(style='thin', color=BORDER_COLOR)
    )
    
    # Status badges
    fill_high = PatternFill(start_color="FCE4D6", fill_type="solid")     # Soft Red
    font_high = Font(name="Calibri", size=10, bold=True, color="C00000")
    
    fill_med = PatternFill(start_color="FFF2CC", fill_type="solid")      # Soft Yellow
    font_med = Font(name="Calibri", size=10, bold=True, color="B25900")
    
    fill_low = PatternFill(start_color="E2EFDA", fill_type="solid")      # Soft Green
    font_low = Font(name="Calibri", size=10, bold=True, color="375623")
    
    fill_yes = PatternFill(start_color="E2EFDA", fill_type="solid")
    font_yes = Font(name="Calibri", size=10, color="276A3C", bold=True)
    
    fill_no = PatternFill(start_color="F2F2F2", fill_type="solid")
    font_no = Font(name="Calibri", size=10, color="595959")

    # Combine tables if multiple or take the primary table
    primary_headers = tables[0][0]
    all_rows = []
    for h, rows in tables:
        # If headers match, stack rows; otherwise keep all
        all_rows.extend(rows)

    # 1. Write Header
    ws.append(primary_headers)
    ws.row_dimensions[1].height = 28

    for col_idx in range(1, len(primary_headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = cell_border

    # Standard Column Width Presets
    width_map = {
        "tc id": 16,
        "id": 14,
        "module": 18,
        "requirement": 24,
        "feature": 24,
        "risk": 12,
        "risk level": 12,
        "test title": 36,
        "title": 36,
        "scenario": 36,
        "pre-condition": 28,
        "test steps": 45,
        "steps": 45,
        "expected result": 45,
        "expected": 45,
        "priority": 12,
        "test data": 28,
        "data": 28,
        "automatable": 14,
        "auto type": 12,
        "tags": 22
    }

    # Identify column types by header name
    col_types = {}
    for idx, header in enumerate(primary_headers, 1):
        h_lower = header.lower().strip()
        col_types[idx] = h_lower

    # 2. Write Data Rows
    current_row_idx = 2
    for row_data in all_rows:
        ws.append(row_data)
        ws.row_dimensions[current_row_idx].height = None  # Auto height for wrapped text
        
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=current_row_idx, column=col_idx)
            cell.border = cell_border
            cell.font = Font(name="Calibri", size=10)
            
            h_name = col_types.get(col_idx, "")
            val_str = str(val).strip()
            val_lower = val_str.lower()
            
            # Alignments & Styling based on column semantic
            if any(k in h_name for k in ["steps", "expected", "title", "scenario", "pre-condition"]):
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            elif any(k in h_name for k in ["risk", "priority", "automatable", "auto type", "id"]):
                cell.alignment = Alignment(horizontal="center", vertical="top")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="top")

            # Badges
            if "risk" in h_name or "priority" in h_name:
                if "high" in val_lower or "critical" in val_lower:
                    cell.fill = fill_high
                    cell.font = font_high
                elif "med" in val_lower:
                    cell.fill = fill_med
                    cell.font = font_med
                elif "low" in val_lower:
                    cell.fill = fill_low
                    cell.font = font_low
            elif "automatable" in h_name:
                if val_lower in ["yes", "true"]:
                    cell.fill = fill_yes
                    cell.font = font_yes
                elif val_lower in ["no", "false"]:
                    cell.fill = fill_no
                    cell.font = font_no
                elif "partial" in val_lower:
                    cell.fill = fill_med
                    cell.font = font_med

        current_row_idx += 1

    total_rows = len(all_rows)

    # 3. Freeze Header Row
    ws.freeze_panes = "A2"

    # 4. Enable AutoFilter
    last_col_letter = get_column_letter(len(primary_headers))
    ws.auto_filter.ref = f"A1:{last_col_letter}{total_rows + 1}"

    # 5. Set Optimal Column Widths
    for col_idx, header in enumerate(primary_headers, 1):
        h_lower = header.lower().strip()
        col_letter = get_column_letter(col_idx)
        
        # Check presets
        target_width = None
        for key, width in width_map.items():
            if key in h_lower:
                target_width = width
                break
                
        if not target_width:
            # Dynamic max calculation
            max_len = len(header)
            for r in all_rows:
                if col_idx - 1 < len(r):
                    lines = str(r[col_idx - 1]).split('\n')
                    for l in lines:
                        if len(l) > max_len:
                            max_len = len(l)
            target_width = min(max(max_len + 3, 12), 45)

        ws.column_dimensions[col_letter].width = target_width

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    wb.save(output_path)
    return total_rows


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown Test Cases into Styled Excel (.xlsx)")
    parser.add_argument("input", help="Path to input Markdown file (.md)")
    parser.add_argument("-o", "--output", help="Path to output Excel file (.xlsx). Defaults to same name as input.")
    parser.add_argument("--sheet-name", default="Test Cases", help="Worksheet title (default: Test Cases)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
        
    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(args.input)
        output_path = base + ".xlsx"

    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()

    tables = parse_markdown_tables(content)
    if not tables:
        print(f"❌ Error: No valid Markdown tables found in {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"📖 Found {len(tables)} table(s) in: {args.input}")
    total = create_styled_excel(tables, output_path, args.sheet_name)
    print(f"✅ Successfully converted {total} test case(s) to styled Excel: {output_path}")


if __name__ == "__main__":
    main()
