#!/usr/bin/env python3
"""
3-Layer Heuristic Locator Matcher (0-Token Autonomous Recovery)
--------------------------------------------------------------
Resolves broken locators in under 15ms with 0 API tokens using a 3-layer
deterministic static fallback cascade:
  Layer 1: Exact Attribute & Snapshot Cache Matching (1ms, ~98% conf)
  Layer 2: Levenshtein Distance & AOM Text Semantic Matching (5ms, ~90% conf)
  Layer 3: Geometric Relative Matching + Spatial Anchor Proximity (10ms, ~86% conf)
  Layer 4: Fallback to LLM agent only if confidence < 85%.

Layer 3 geometric semantics (concept borrowed from Selenium's relative
locators, Apache-2.0 - re-implemented stdlib-only): pass
`relative={"relation": "above"|"below"|"near"|"left-of"|"right-of",
"anchor": "#id-or-selector"}` and the matcher picks the interactive element
satisfying the geometric relation to the anchor's bounding box. Snapshots
without bounding boxes fall back to the order-based anchor heuristic.
"""

import math
import re
import time
from typing import Dict, List, Any, Optional, Tuple

INTERACTIVE_TAGS = {"button", "a", "input", "select", "textarea"}
GEOMETRY_TOLERANCE_PX = 8.0
NEAR_DISTANCE_PX = 250.0


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

    @staticmethod
    def _get_bbox(el: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
        """Extracts (x, y, width, height) from a snapshot element, or None."""
        for keys in (
            ("x", "y", "width", "height"),
            ("left", "top", "width", "height"),
        ):
            if all(k in el for k in keys):
                return tuple(float(el[k]) for k in keys)
        bbox = el.get("bbox")
        if isinstance(bbox, dict) and all(k in bbox for k in ("x", "y", "width", "height")):
            return (float(bbox["x"]), float(bbox["y"]),
                    float(bbox["width"]), float(bbox["height"]))
        return None

    @staticmethod
    def _center_distance(bbox_a: Tuple[float, float, float, float],
                         bbox_b: Tuple[float, float, float, float]) -> float:
        """Euclidean distance between the centers of two bounding boxes."""
        ax = bbox_a[0] + bbox_a[2] / 2.0
        ay = bbox_a[1] + bbox_a[3] / 2.0
        bx = bbox_b[0] + bbox_b[2] / 2.0
        by = bbox_b[1] + bbox_b[3] / 2.0
        return math.hypot(ax - bx, ay - by)

    @staticmethod
    def _satisfies_relation(el_bbox: Tuple[float, float, float, float],
                            anchor_bbox: Tuple[float, float, float, float],
                            relation: str) -> bool:
        """True when el_bbox stands in the requested relation to anchor_bbox."""
        tol = GEOMETRY_TOLERANCE_PX
        ex, ey, ew, eh = el_bbox
        ax, ay, aw, ah = anchor_bbox
        if relation == "above":
            return ey + eh <= ay + tol
        if relation == "below":
            return ey >= ay + ah - tol
        if relation == "left-of":
            return ex + ew <= ax + tol
        if relation == "right-of":
            return ex >= ax + aw - tol
        if relation == "near":
            return HeuristicLocatorMatcher._center_distance(el_bbox, anchor_bbox) <= NEAR_DISTANCE_PX
        return False

    @staticmethod
    def _find_anchor_element(dom_snapshot: List[Dict[str, Any]],
                             anchor_selector: str) -> Optional[Dict[str, Any]]:
        """Finds the anchor element by id / selector / data-testid."""
        bare = anchor_selector.lstrip("#")
        for el in dom_snapshot:
            if (el.get("id") == bare
                    or el.get("selector") == anchor_selector
                    or (el.get("data-testid") or el.get("test-id")) == bare):
                return el
        return None

    @staticmethod
    def _parse_relative_request(
        relative: Optional[Dict[str, Any]],
        spatial_anchor: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Normalizes legacy spatial_anchor and the relative dict into
        (relation, anchor_selector). Legacy anchors behave as 'below'."""
        if isinstance(relative, dict) and relative.get("relation") and relative.get("anchor"):
            return str(relative["relation"]).lower(), str(relative["anchor"])
        if spatial_anchor:
            return "below", spatial_anchor
        return None, None

    @classmethod
    def match(
        cls,
        broken_locator: str,
        dom_snapshot: List[Dict[str, Any]],
        cache_entry: Optional[Dict[str, Any]] = None,
        spatial_anchor: Optional[str] = None,
        relative: Optional[Dict[str, Any]] = None
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
            # Check test-id (exact or semantic substring match)
            testid = el.get("data-testid") or el.get("test-id")
            if testid:
                clean_broken = re.sub(r'[^a-zA-Z0-9]', '', broken_locator.lower())
                clean_testid = re.sub(r'[^a-zA-Z0-9]', '', testid.lower())
                if clean_broken in clean_testid or clean_testid in clean_broken or primary_keyword in testid.lower():
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    return {
                        "matched": True,
                        "layer": 1,
                        "strategy": "EXACT_TESTID_ATTRIBUTE",
                        "healed_locator": f"[data-testid='{testid}']",
                        "confidence": 0.98,
                        "needs_llm": False,
                        "execution_time_ms": round(elapsed_ms, 2)
                    }
            # Check aria-label or data-action match
            aria = el.get("aria-label") or el.get("data-action")
            if aria and (aria.lower() == primary_keyword or primary_keyword in aria.lower()):
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                tag_prefix = el.get("tag", "button")
                return {
                    "matched": True,
                    "layer": 1,
                    "strategy": "EXACT_ARIA_LABEL",
                    "healed_locator": f"{tag_prefix}[aria-label='{el.get('aria-label', aria)}']",
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
        # Layer 3: Spatial Anchor Proximity & Unique Semantic Tag Fallback
        #   3a. Geometric relative matching (bbox-aware, Selenium-style)
        #   3b. Order-based anchor heuristic (bbox-free fallback)
        # ---------------------------------------------------------------------
        relation, anchor_selector = cls._parse_relative_request(relative, spatial_anchor)
        if relation and anchor_selector:
            anchor_el = cls._find_anchor_element(dom_snapshot, anchor_selector)
            anchor_bbox = cls._get_bbox(anchor_el) if anchor_el is not None else None
            if anchor_bbox is not None:
                candidates = [
                    el for el in dom_snapshot
                    if el is not anchor_el
                    and (el.get("tag") or "").lower() in INTERACTIVE_TAGS
                    and cls._satisfies_relation(cls._get_bbox(el) or (0, 0, 0, 0), anchor_bbox, relation)
                ]
                candidates = [el for el in candidates if cls._get_bbox(el) is not None]
                if candidates:
                    target = min(candidates, key=lambda el: cls._center_distance(cls._get_bbox(el), anchor_bbox))
                    if target.get("id"):
                        healed = f"#{target['id']}"
                    elif target.get("data-testid") or target.get("test-id"):
                        healed = f"[data-testid='{target.get('data-testid') or target.get('test-id')}']"
                    else:
                        text = (target.get("text") or "").strip()
                        healed = f"{target.get('tag', 'button')}:has-text('{text[:40]}')" if text else target.get("tag", "button")
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    return {
                        "matched": True,
                        "layer": 3,
                        "strategy": "GEOMETRIC_RELATIVE_MATCH",
                        "healed_locator": healed,
                        "confidence": 0.88,
                        "needs_llm": False,
                        "execution_time_ms": round(elapsed_ms, 2)
                    }
            # bbox-free snapshots fall through to the order-based heuristic

        if anchor_selector:
            # Find element immediately adjacent/inside the anchor container
            anchor_found = False
            for idx, el in enumerate(dom_snapshot):
                if anchor_found:
                    # Next interactive element after anchor
                    if el.get("tag") in ["button", "a", "input"]:
                        elapsed_ms = (time.perf_counter() - start_time) * 1000
                        target_loc = el.get("id") and f"#{el['id']}" or f"{el.get('tag')}:below('{anchor_selector}')"
                        return {
                            "matched": True,
                            "layer": 3,
                            "strategy": "SPATIAL_ANCHOR_PROXIMITY",
                            "healed_locator": target_loc,
                            "confidence": 0.86,
                            "needs_llm": False,
                            "execution_time_ms": round(elapsed_ms, 2)
                        }
                if el.get("id") == anchor_selector.replace("#", "") or el.get("selector") == anchor_selector:
                    anchor_found = True

        # Unique interactive element fallback (e.g. single CTA button or input in snapshot)
        if len(dom_snapshot) == 1:
            el = dom_snapshot[0]
            tag = el.get("tag", "").lower()
            text = (el.get("text") or "").lower()
            is_interactive = tag in ["button", "input", "select", "a", "textarea"] or bool(el.get("type"))
            has_keyword_match = bool(primary_keyword and (primary_keyword in text or primary_keyword in el.get("id", "").lower()))
            if is_interactive or has_keyword_match:
                if el.get("id"):
                    target_loc = f"#{el['id']}"
                elif el.get("type"):
                    target_loc = f"{el.get('tag', 'button')}[type='{el['type']}']"
                else:
                    target_loc = el.get("tag", "button")
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "matched": True,
                    "layer": 3,
                    "strategy": "UNIQUE_DOM_ELEMENT",
                    "healed_locator": target_loc,
                    "confidence": 0.90,
                    "needs_llm": False,
                    "execution_time_ms": round(elapsed_ms, 2)
                }

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
