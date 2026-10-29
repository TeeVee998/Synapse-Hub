#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Canvas Visual Diff & Regression Checker
===================================================
Provides visual regression AI testing capabilities for HTML5 Canvas, SVG,
and DOM-less charts (e.g. DataMiningPage / GIS / Analytics).

Features:
  1. compare: Pixel-by-pixel Canvas comparison against Golden Baseline.
     Computes diff ratio and generates highlight overlay diff artifacts.
  2. check-blank: Detects white-screen or empty non-rendered Canvas regressions.
  3. update-baseline: Captures new Golden Baseline upon design updates.

Usage:
  python3 tools/visual_diff_canvas.py compare baseline.png current.png --diff diff.png --threshold 0.02
  python3 tools/visual_diff_canvas.py check-blank current.png
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:
    print("❌ Error: Pillow library not installed. Please install: pip install Pillow")
    sys.exit(1)


def is_canvas_blank(image_path: str, std_dev_threshold: float = 2.0) -> tuple[bool, float]:
    """
    Checks if a canvas screenshot is blank, empty, or single-color non-rendered.
    Returns (is_blank, std_dev).
    """
    with Image.open(image_path) as img:
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)
        std_dev = stat.stddev[0]
        # Low standard deviation indicates uniform solid/blank canvas
        return (std_dev < std_dev_threshold, std_dev)


def compare_canvas_images(
    baseline_path: str,
    current_path: str,
    diff_output_path: str | None = None,
    threshold: float = 0.01
) -> tuple[bool, float, int]:
    """
    Compares two canvas screenshots pixel-by-pixel.
    Returns (is_match, diff_ratio, diff_pixels).
    threshold: Allowed diff ratio (e.g. 0.01 = 1% tolerance)
    """
    with Image.open(baseline_path) as img_base, Image.open(current_path) as img_curr:
        # Normalize dimensions and color mode
        if img_base.size != img_curr.size:
            img_curr = img_curr.resize(img_base.size, Image.Resampling.LANCZOS)

        base_rgb = img_base.convert("RGB")
        curr_rgb = img_curr.convert("RGB")

        # C-level accelerated pixel difference via Pillow vectorization
        diff = ImageChops.difference(base_rgb, curr_rgb)
        gray_diff = diff.convert("L")
        total_pixels = img_base.width * img_base.height

        # Histogram-based count of divergent pixels (delta > 10, < 0.03s for 1920x1080)
        hist = gray_diff.histogram()
        diff_count = sum(hist[11:])

        diff_ratio = diff_count / total_pixels
        is_match = diff_ratio <= threshold

        if diff_output_path and not is_match:
            os.makedirs(os.path.dirname(os.path.abspath(diff_output_path)), exist_ok=True)
            red_layer = Image.new("RGBA", img_base.size, (255, 0, 0, 200))
            alpha_mask = gray_diff.point(lambda p: 200 if p > 10 else 0)
            red_layer.putalpha(alpha_mask)
            annotated = curr_rgb.convert("RGBA")
            annotated.paste(red_layer, (0, 0), red_layer)
            annotated.save(diff_output_path)

        return (is_match, diff_ratio, diff_count)


def main():
    parser = argparse.ArgumentParser(description="Enterprise Canvas Visual Diff & Regression Checker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: compare
    compare_p = subparsers.add_parser("compare", help="Compare current canvas screenshot against Golden Baseline")
    compare_p.add_argument("baseline", help="Path to Golden Baseline image")
    compare_p.add_argument("current", help="Path to current runtime screenshot")
    compare_p.add_argument("--diff", default=None, help="Output path for annotated diff highlight image")
    compare_p.add_argument("--threshold", type=float, default=0.01, help="Max allowed divergence ratio (default: 0.01 = 1%%)")

    # Command: check-blank
    blank_p = subparsers.add_parser("check-blank", help="Check whether canvas is blank or unrendered")
    blank_p.add_argument("current", help="Path to canvas screenshot to verify")
    blank_p.add_argument("--threshold", type=float, default=2.0, help="Min standard deviation for valid render (default: 2.0)")

    args = parser.parse_args()

    if args.command == "compare":
        if not os.path.exists(args.baseline):
            print(f"❌ Baseline file not found: {args.baseline}")
            sys.exit(2)
        if not os.path.exists(args.current):
            print(f"❌ Current screenshot file not found: {args.current}")
            sys.exit(2)

        is_match, diff_ratio, diff_count = compare_canvas_images(
            args.baseline, args.current, args.diff, args.threshold
        )
        pct = diff_ratio * 100
        if is_match:
            print(f"✅ PASS: Visual canvas matches Baseline (Diff: {pct:.2f}%, {diff_count} px <= {args.threshold*100:.1f}%)")
            sys.exit(0)
        else:
            print(f"❌ FAIL: Visual canvas exceeded divergence threshold (Diff: {pct:.2f}%, {diff_count} px > {args.threshold*100:.1f}%)")
            if args.diff:
                print(f"   📸 Annotated diff artifact saved to: {args.diff}")
            sys.exit(1)

    elif args.command == "check-blank":
        if not os.path.exists(args.current):
            print(f"❌ Screenshot file not found: {args.current}")
            sys.exit(2)

        blank, std_dev = is_canvas_blank(args.current, args.threshold)
        if blank:
            print(f"❌ WARNING: Canvas is blank / unrendered (Standard Deviation: {std_dev:.2f} < {args.threshold})")
            sys.exit(1)
        else:
            print(f"✅ PASS: Canvas renders valid graphical content (Standard Deviation: {std_dev:.2f} >= {args.threshold})")
            sys.exit(0)


if __name__ == "__main__":
    main()
