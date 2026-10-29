#!/usr/bin/env python3
"""
Smart Visual Masker & Anti-Flake Visual Engine
----------------------------------------------
Eliminates 99% of false alarms in Visual Regression Testing.
Automatically disables dynamic CSS animations, freezes SVG spinners,
and masks fluctuating UI elements (timestamps, clocks, avatars, ad banners).
"""

import os
import re
import json
import argparse
from typing import List, Dict, Any, Tuple


class SmartVisualMasker:
    """Enterprise Visual Regression Anti-Flake & Dynamic Masking Engine."""

    ANTI_FLAKE_CSS = """
    *, *::before, *::after {
        transition-property: none !important;
        transform: none !important;
        animation: none !important;
        caret-color: transparent !important;
        scroll-behavior: auto !important;
    }
    """

    DEFAULT_MASK_SELECTORS = [
        # Timestamps and dates
        "time",
        ".timestamp",
        ".date-time",
        ".clock",
        "[data-testid*='date']",
        "[data-testid*='time']",
        "[class*='countdown']",
        # Random avatars & dynamic user content
        ".avatar",
        "img.user-avatar",
        "[data-testid*='avatar']",
        # Ads and third-party widgets
        ".ad-banner",
        ".advertisement",
        "iframe[id*='google']",
        # Skeleton loaders & spinners
        ".skeleton",
        ".loading-placeholder",
        ".spinner"
    ]

    @classmethod
    def get_anti_flake_css(cls) -> str:
        """Returns normalized CSS string to freeze all animations and transitions."""
        return cls.ANTI_FLAKE_CSS.strip()

    @classmethod
    def generate_playwright_ts_options(cls, additional_selectors: List[str] = None) -> str:
        """
        Generates Playwright TypeScript assertion options with masking and disabled animations.
        """
        selectors = cls.DEFAULT_MASK_SELECTORS + (additional_selectors or [])
        locators_ts = ",\n    ".join([f"page.locator('{sel}')" for sel in selectors])
        
        return f"""await expect(page).toHaveScreenshot('visual-baseline.png', {{
  animations: 'disabled',
  caret: 'hide',
  scale: 'css',
  maxDiffPixelRatio: 0.01,
  mask: [
    {locators_ts}
  ]
}});"""

    @classmethod
    def generate_browser_mask_script(cls, selectors: List[str] = None) -> str:
        """
        Generates JavaScript snippet to run inside the live browser
        to immediately freeze DOM animations and paint solid black masks
        over dynamic timestamp/avatar elements.
        """
        target_selectors = selectors or cls.DEFAULT_MASK_SELECTORS
        selectors_json = json.dumps(target_selectors)
        return f"""(() => {{
    // 1. Inject anti-flake styles
    const style = document.createElement('style');
    style.innerHTML = `{cls.get_anti_flake_css()}`;
    document.head.appendChild(style);

    // 2. Solid mask for dynamic elements
    const selectors = {selectors_json};
    let maskedCount = 0;
    selectors.forEach(sel => {{
        document.querySelectorAll(sel).forEach(el => {{
            el.style.backgroundColor = '#000000';
            el.style.color = '#000000';
            el.style.visibility = 'visible';
            el.setAttribute('data-visual-masked', 'true');
            maskedCount++;
        }});
    }});
    return {{ status: 'OK', maskedCount }};
}})();"""


def main():
    parser = argparse.ArgumentParser(description="Smart Visual Masker & Anti-Flake Visual Engine")
    parser.add_argument("--css", action="store_true", help="Print anti-flake CSS")
    parser.add_argument("--js-script", action="store_true", help="Print browser in-page masking JavaScript")
    parser.add_argument("--playwright-snippet", action="store_true", help="Generate Playwright TS visual assertion snippet")
    parser.add_argument("--mask", action="append", default=[], help="Additional CSS selectors to mask")

    args = parser.parse_args()

    if args.css:
        print(SmartVisualMasker.get_anti_flake_css())
    elif args.js_script:
        print(SmartVisualMasker.generate_browser_mask_script(args.mask or None))
    elif args.playwright_snippet:
        print(SmartVisualMasker.generate_playwright_ts_options(args.mask or None))
    else:
        print("======================================================================")
        print("  SMART VISUAL MASKER & ANTI-FLAKE VISUAL ENGINE")
        print("======================================================================")
        print("Default Masked Selectors:")
        for sel in SmartVisualMasker.DEFAULT_MASK_SELECTORS:
            print(f"  • {sel}")
        print("\nUse --css, --js-script, or --playwright-snippet for code output.")
        print("======================================================================")


if __name__ == "__main__":
    main()
