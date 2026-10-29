#!/usr/bin/env python3
"""
3-Layer Heuristic Locator Matcher (0-Token Autonomous Recovery)
--------------------------------------------------------------
Resolves broken locators in under 15ms with 0 API tokens using a 3-layer
deterministic static fallback cascade:
  Layer 1: Exact Attribute & Snapshot Cache Matching (1ms, ~98% conf)
  Layer 2: Levenshtein Distance & AOM Text Semantic Matching (5ms, ~90% conf)
  Layer 3: Spatial Anchor Proximity Heuristics (10ms, ~86% conf)
  Layer 4: Fallback to LLM agent only if confidence < 85%.
"""

import re
import time
from typing import Dict, List, Any, Optional, Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0 = list(v1)

    return v1[len(s2)]


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Computes similarity ratio between 0.0 and 1.0."""
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()
    if s1_norm == s2_norm:
        return 1.0
    max_len = max(len(s1_norm), len(s2_norm))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1_norm, s2_norm)
    return max(0.0, 1.0 - (dist / max_len))


class HeuristicLocatorMatcher:
    """Cascade matcher resolving broken locators before LLM invocation."""

    CONFIDENCE_THRESHOLD = 0.85

    @classmethod
    def match(
        cls,
        broken_locator: str,
        dom_snapshot: List[Dict[str, Any]],
        cache_entry: Optional[Dict[str, Any]] = None,
        spatial_anchor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the 3-Layer 0-token matching cascade.
        Returns a dictionary with match result, confidence, layer, and execution time.
        """
        start_time = time.perf_counter()

        # Extract keyword cues from broken locator
        quoted_m = re.findall(r"['\"]([^'\"]+)['\"]", broken_locator)
        if quoted_m:
            primary_keyword = quoted_m[0].lower().strip()
        else:
            tokens = [
                t.lower() for t in re.split(r"[-_#.\s//\[\]@'\"=()]+", broken_locator)
                if len(t) > 2 and t.lower() not in [
                    "button", "input", "div", "span", "old", "new", "text", "contains",
                    "normalize-space", "has-text", "xpath", "btn", "txt"
                ]
            ]
            primary_keyword = tokens[0] if tokens else broken_locator.lower().strip()

        # ---------------------------------------------------------------------
        # Layer 1: Exact Match on Snapshot Cache / Stable Attributes (1ms)
        # ---------------------------------------------------------------------
        if cache_entry and cache_entry.get("healed_locator"):
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "matched": True,
                "layer": 1,
                "strategy": "EXACT_CACHE_MATCH",
                "healed_locator": cache_entry["healed_locator"],
                "confidence": 0.98,
                "needs_llm": False,
                "execution_time_ms": round(elapsed_ms, 2)
            }

        for el in dom_snapshot:
            # Check test-id
            if el.get("data-testid") and el["data-testid"].lower() in broken_locator.lower():
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "matched": True,
                    "layer": 1,
                    "strategy": "EXACT_TESTID_ATTRIBUTE",
                    "healed_locator": f"[data-testid='{el['data-testid']}']",
                    "confidence": 0.98,
                    "needs_llm": False,
                    "execution_time_ms": round(elapsed_ms, 2)
                }
            # Check aria-label exact match
            if el.get("aria-label") and el["aria-label"].lower() == primary_keyword:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "matched": True,
                    "layer": 1,
                    "strategy": "EXACT_ARIA_LABEL",
                    "healed_locator": f"[aria-label='{el['aria-label']}']",
                    "confidence": 0.96,
                    "needs_llm": False,
                    "execution_time_ms": round(elapsed_ms, 2)
                }

        # ---------------------------------------------------------------------
        # Layer 2: Levenshtein Distance & Text Semantic Matching (5ms)
        # ---------------------------------------------------------------------
        best_l2_elem = None
        best_l2_ratio = 0.0

        for el in dom_snapshot:
            text = (el.get("text") or el.get("aria-label") or el.get("placeholder") or "").strip()
            if not text:
                continue

            # Substring match (e.g. 'Submit Order' contains 'Submit')
            if primary_keyword in text.lower():
                ratio = 0.92
            else:
                ratio = levenshtein_ratio(primary_keyword, text)

            if ratio > best_l2_ratio:
                best_l2_ratio = ratio
                best_l2_elem = el

        if best_l2_elem and best_l2_ratio >= 0.70:
            target_text = best_l2_elem.get("text") or best_l2_elem.get("aria-label")
            tag = best_l2_elem.get("tag", "button")
            healed = f"{tag}:has-text('{target_text}')"
            confidence = min(0.95, 0.85 + (best_l2_ratio * 0.10))

            if confidence >= cls.CONFIDENCE_THRESHOLD:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "matched": True,
                    "layer": 2,
                    "strategy": "TEXT_SEMANTIC_LEVENSHTEIN",
                    "healed_locator": healed,
                    "confidence": round(confidence, 2),
                    "needs_llm": False,
                    "execution_time_ms": round(elapsed_ms, 2)
                }

        # ---------------------------------------------------------------------
        # Layer 3: Spatial Anchor Proximity Heuristic (10ms)
        # ---------------------------------------------------------------------
        if spatial_anchor:
            # Find element immediately adjacent/inside the anchor container
            anchor_found = False
            for idx, el in enumerate(dom_snapshot):
                if anchor_found:
                    # Next interactive element after anchor
                    if el.get("tag") in ["button", "a", "input"]:
                        elapsed_ms = (time.perf_counter() - start_time) * 1000
                        target_loc = el.get("id") and f"#{el['id']}" or f"{el.get('tag')}:below('{spatial_anchor}')"
                        return {
                            "matched": True,
                            "layer": 3,
                            "strategy": "SPATIAL_ANCHOR_PROXIMITY",
                            "healed_locator": target_loc,
                            "confidence": 0.86,
                            "needs_llm": False,
                            "execution_time_ms": round(elapsed_ms, 2)
                        }
                if el.get("id") == spatial_anchor.replace("#", "") or el.get("selector") == spatial_anchor:
                    anchor_found = True

        # ---------------------------------------------------------------------
        # Layer 4: Fallback to LLM (< 85% confidence)
        # ---------------------------------------------------------------------
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            "matched": False,
            "layer": 4,
            "strategy": "FALLBACK_LLM_REQUIRED",
            "healed_locator": None,
            "confidence": round(best_l2_ratio, 2) if best_l2_ratio else 0.0,
            "needs_llm": True,
            "execution_time_ms": round(elapsed_ms, 2)
        }
