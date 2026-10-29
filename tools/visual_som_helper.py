#!/usr/bin/env python3
"""
Enterprise Vision-Grounded Fallback & Set-of-Marks (SoM) Engine
--------------------------------------------------------------
Provides multimodal coordinate grounding when standard DOM locators fail
(HTML5 Canvas, WebGL financial charts, deeply nested Shadow DOM, cross-origin iframes).

Features:
  1. Set-of-Marks (SoM) Overlay Generation:
     - Detects interactive visual regions (or accepts DOM bounding boxes).
     - Renders high-contrast colored bounding boxes with numeric IDs (1, 2, 3...) on screenshots.
  2. Coordinate Resolution & Physical Mouse Dispatch:
     - Maps Mark IDs and visual targets to exact center coordinates (x, y).
     - Generates direct Playwright physical mouse actions: await page.mouse.click(x, y).
  3. Visual Perceptual Caching & Token Economy:
     - Generates difference hash (dHash) fingerprints for visual components.
     - Caches coordinates in SQLite (memory_cache.db). If visual similarity > 98%,
       instantly retrieves cached coordinates without expensive Vision LLM calls (Zero-Token).
  4. Compact Vision Prompt Formatter:
     - Formats token-efficient briefs for Multimodal Vision Models (Gemini / Claude / GPT-4o).
"""

import os
import sys
import json
import sqlite3
import argparse
from typing import Dict, Any, List, Optional, Tuple, Union
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PIL = True
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageFilter = None
    HAS_PIL = False

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QA_HUB_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_CACHE_DB = os.path.join(SCRIPT_DIR, "memory_cache.db")

MARK_COLORS = [
    "#FF0055",  # Vibrant Red/Pink
    "#00CCFF",  # Cyan
    "#00FF66",  # Neon Green
    "#FFCC00",  # Bright Yellow
    "#9933FF",  # Purple
    "#FF6600",  # Orange
]


def compute_visual_hash(image_source: Union[Image.Image, str], bbox: Optional[List[int]] = None, hash_size: int = 8) -> str:
    """
    Computes a 64-bit difference hash (dHash) for an image or cropped component.
    Fast, deterministic, and 100% offline.
    """
    if isinstance(image_source, str):
        if not os.path.exists(image_source):
            raise FileNotFoundError(f"Image not found: {image_source}")
        img = Image.open(image_source)
    else:
        img = image_source

    if bbox and len(bbox) == 4:
        img = img.crop(bbox)

    # Resize to (hash_size + 1, hash_size) in grayscale
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(resized.tobytes())

    diff = []
    for row in range(hash_size):
        row_start = row * (hash_size + 1)
        for col in range(hash_size):
            left = pixels[row_start + col]
            right = pixels[row_start + col + 1]
            diff.append("1" if left > right else "0")

    return "".join(diff)


def calculate_visual_similarity(hash1: str, hash2: str) -> float:
    """Calculates normalized Hamming similarity between two binary hashes (0.0 to 1.0)."""
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 0.0
    hamming_dist = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    return round(1.0 - (hamming_dist / len(hash1)), 4)


class VisualSoMHelper:
    """Manages visual grounding, bounding box marking, visual caching, and coordinate dispatch."""

    def __init__(self, viewport_width: int = 1920, viewport_height: int = 1080, db_path: Optional[str] = None):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.db_path = db_path or DEFAULT_CACHE_DB
        self.init_cache_table()

    def init_cache_table(self):
        """Initializes the visual_som_cache SQLite table if not already present."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS visual_som_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component_name TEXT NOT NULL,
                        visual_hash TEXT NOT NULL,
                        center_x INTEGER NOT NULL,
                        center_y INTEGER NOT NULL,
                        rel_x REAL DEFAULT 0.0,
                        rel_y REAL DEFAULT 0.0,
                        hit_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(component_name, visual_hash)
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_som_component ON visual_som_cache (component_name);")
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

    def lookup_cached_coordinates(
        self,
        component_name: str,
        image_source: Union[Image.Image, str],
        bbox: Optional[List[int]] = None,
        threshold: float = 0.98,
        db_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Looks up cached coordinates for a component if visual similarity exceeds threshold (default 98%).
        Returns resolved coordinate data if cache hit, None if cache miss.
        """
        current_hash = compute_visual_hash(image_source, bbox=bbox)
        db = db_path or self.db_path

        try:
            conn = sqlite3.connect(db, timeout=10.0)
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, component_name, visual_hash, center_x, center_y, hit_count FROM visual_som_cache WHERE component_name = ?",
                    (component_name,)
                )
                rows = cursor.fetchall()

                best_match = None
                best_sim = -1.0

                for row in rows:
                    cached_hash = row["visual_hash"]
                    sim = calculate_visual_similarity(current_hash, cached_hash)
                    if sim >= threshold and sim > best_sim:
                        best_sim = sim
                        best_match = row

                if best_match:
                    match_id = best_match["id"]
                    cursor.execute(
                        "UPDATE visual_som_cache SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (match_id,)
                    )
                    conn.commit()

                    cx = best_match["center_x"]
                    cy = best_match["center_y"]
                    return {
                        "component_name": component_name,
                        "center_x": cx,
                        "center_y": cy,
                        "visual_similarity": best_sim,
                        "visual_hash": current_hash,
                        "cached": True,
                        "hit_count": best_match["hit_count"] + 1,
                        "playwright_action": f"await page.mouse.click({cx}, {cy});"
                    }
            finally:
                conn.close()
        except Exception:
            pass

        return None

    def save_cached_coordinates(
        self,
        component_name: str,
        image_source: Union[Image.Image, str],
        center_x: int,
        center_y: int,
        bbox: Optional[List[int]] = None,
        db_path: Optional[str] = None
    ) -> str:
        """
        Saves resolved coordinates and visual hash into SQLite cache.
        """
        visual_hash = compute_visual_hash(image_source, bbox=bbox)
        db = db_path or self.db_path

        try:
            conn = sqlite3.connect(db, timeout=10.0)
            try:
                conn.execute("""
                    INSERT INTO visual_som_cache (component_name, visual_hash, center_x, center_y, hit_count)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(component_name, visual_hash) DO UPDATE SET
                        center_x = excluded.center_x,
                        center_y = excluded.center_y,
                        hit_count = visual_som_cache.hit_count + 1,
                        updated_at = CURRENT_TIMESTAMP;
                """, (component_name, visual_hash, center_x, center_y))
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

        return visual_hash

    def detect_canvas_interactive_regions(
        self,
        image_path: str,
        stride: int = 16,
        edge_threshold: int = 28,
        min_pixels_per_cell: int = 6,
        min_w: int = 16,
        min_h: int = 16,
        max_ratio: float = 0.88
    ) -> List[Dict[str, Any]]:
        """
        Standalone Computer Vision Contour / Active Blob Detector for Canvas/GIS.
        Detects interactive visual components (buttons, polygon nodes, markers, sliders, chart icons)
        without requiring DOM elements or accessibility nodes.
        Uses pure PIL edge filtering and connected-grid component clustering (Zero-Dependency).
        """
        if not os.path.exists(image_path) or not HAS_PIL:
            return []

        img = Image.open(image_path).convert("L")
        w, h = img.size
        max_allowed_w = int(w * max_ratio)
        max_allowed_h = int(h * max_ratio)

        # Detect high-contrast edges & contours
        edges = img.filter(ImageFilter.FIND_EDGES)
        edges = edges.point(lambda p: 255 if p > edge_threshold else 0)
        pixels = edges.load()

        # Identify active cells with high edge density
        active_cells = set()
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                count = 0
                for cy in range(y, min(h, y + stride)):
                    for cx in range(x, min(w, x + stride)):
                        if pixels[cx, cy] > 0:
                            count += 1
                if count >= min_pixels_per_cell:
                    active_cells.add((x // stride, y // stride))

        # 8-direction BFS clustering to group connected components
        visited = set()
        detected_elements = []
        cluster_id = 1

        for cell in sorted(active_cells):
            if cell in visited:
                continue
            queue = [cell]
            visited.add(cell)
            cluster = [cell]

            while queue:
                curr = queue.pop(0)
                cx, cy = curr
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nb = (cx + dx, cy + dy)
                        if nb in active_cells and nb not in visited:
                            visited.add(nb)
                            queue.append(nb)
                            cluster.append(nb)

            min_x = max(0, min(c[0] for c in cluster) * stride - 4)
            min_y = max(0, min(c[1] for c in cluster) * stride - 4)
            box_w = min(w - min_x, (max(c[0] for c in cluster) + 1) * stride - min_x + 8)
            box_h = min(h - min_y, (max(c[1] for c in cluster) + 1) * stride - min_y + 8)

            # Filter out whole-canvas background borders or tiny noise
            if box_w >= min_w and box_h >= min_h and (box_w < max_allowed_w or box_h < max_allowed_h):
                detected_elements.append({
                    "x": min_x,
                    "y": min_y,
                    "width": box_w,
                    "height": box_h,
                    "label": f"Canvas_Target_{cluster_id}",
                    "tag": "canvas_interactive_node"
                })
                cluster_id += 1

        return detected_elements

    def generate_som_overlay(
        self,
        image_path: str,
        elements: Optional[List[Dict[str, Any]]] = None,
        output_path: Optional[str] = None
    ) -> Tuple[str, Dict[int, Dict[str, Any]]]:
        """
        Draws high-contrast numbered badges (Set-of-Marks) over each element bounding box.
        If elements is omitted, autonomously runs detect_canvas_interactive_regions.
        Returns (marked_image_path, marks_map).
        """
        if not os.path.exists(image_path):
            img = Image.new("RGB", (self.viewport_width, self.viewport_height), color="#1E1E2E")
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "Mock Financial Dashboard (HTML5 Canvas)", fill="#FFFFFF")
            draw.rectangle([100, 150, 220, 190], outline="#00CCFF", width=2)
            draw.rectangle([240, 150, 360, 190], outline="#FF0055", width=2)
            draw.rectangle([500, 300, 700, 350], outline="#00FF66", width=2)
            img.save(image_path)

        if not elements:
            detected = self.detect_canvas_interactive_regions(image_path)
            elements = detected if detected else [
                {"x": 100, "y": 150, "width": 120, "height": 40, "label": "TradingView Zoom In", "tag": "canvas_control"},
                {"x": 240, "y": 150, "width": 120, "height": 40, "label": "TradingView Zoom Out", "tag": "canvas_control"},
                {"x": 500, "y": 300, "width": 200, "height": 50, "label": "Execute Trade Order", "tag": "shadow_button"},
                {"x": 720, "y": 300, "width": 150, "height": 50, "label": "Cancel Order", "tag": "shadow_button"}
            ]

        img = Image.open(image_path).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        marks_map = {}
        for idx, el in enumerate(elements, start=1):
            x = el.get("x", 0)
            y = el.get("y", 0)
            w = el.get("width", 80)
            h = el.get("height", 35)

            center_x = round(x + w / 2)
            center_y = round(y + h / 2)
            color = MARK_COLORS[(idx - 1) % len(MARK_COLORS)]

            # Draw bounding box
            draw.rectangle([x, y, x + w, y + h], outline=color, width=3)

            # Draw badge label (e.g. [1])
            badge_w, badge_h = 24, 20
            badge_x = max(0, x)
            badge_y = max(0, y - badge_h)
            draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=color)
            draw.text((badge_x + 6, badge_y + 3), str(idx), fill="#000000")

            marks_map[idx] = {
                "mark_id": idx,
                "label": el.get("label") or el.get("text") or el.get("role") or f"Element_{idx}",
                "tag": el.get("tag", "element"),
                "bounds": [x, y, x + w, y + h],
                "center_x": center_x,
                "center_y": center_y,
                "playwright_action": f"await page.mouse.click({center_x}, {center_y});"
            }

        combined = Image.alpha_composite(img, overlay).convert("RGB")
        out_file = output_path or image_path.replace(".png", "_som_marked.png")
        combined.save(out_file)

        return out_file, marks_map

    def resolve_mark_coordinates(
        self,
        marks_map: Dict[int, Dict[str, Any]],
        target_mark_id: Optional[int] = None,
        target_label: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolves the exact (x, y) coordinates for a given Mark ID or fuzzy label.
        """
        if target_mark_id and target_mark_id in marks_map:
            return marks_map[target_mark_id]

        if target_label:
            target_clean = target_label.strip().lower()
            for mark in marks_map.values():
                if target_clean in mark.get("label", "").lower():
                    return mark

        return None

    def format_vision_prompt(self, marks_map: Dict[int, Dict[str, Any]], goal: str) -> str:
        """
        Formats a compact Vision brief for multimodal models (Gemini / Claude).
        """
        lines = [
            f"GOAL: {goal}",
            f"SET-OF-MARKS (SoM) CANDIDATE REGIONS DETECTED: {len(marks_map)}",
            "",
            "Inspect the attached marked screenshot and identify the target Mark ID:",
        ]
        for m_id, data in marks_map.items():
            lines.append(f"  [{m_id}] '{data['label']}' -> Center ({data['center_x']}, {data['center_y']})")
        lines.append("")
        lines.append("RESPOND WITH FORMAT: CLICK_MARK: <ID>")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Multimodal Vision Grounding & Set-of-Marks Engine")
    parser.add_argument("--image", default="screenshot.png", help="Path to input screenshot image")
    parser.add_argument("--output", default="", help="Path to output marked image")
    parser.add_argument("--elements-json", default="", help="JSON string or file of candidate bounding boxes")
    parser.add_argument("--mark-id", type=int, default=None, help="Target Mark ID to resolve")
    parser.add_argument("--label", default="", help="Target semantic label to resolve")
    parser.add_argument("--component", default="", help="Target component name for visual cache lookup/save")
    parser.add_argument("--cache-lookup", action="store_true", help="Attempt zero-token visual cache resolution first")
    parser.add_argument("--cache-save", action="store_true", help="Save resolved coordinates to visual cache")
    parser.add_argument("--threshold", type=float, default=0.98, help="Visual similarity threshold for cache hit (default: 0.98)")
    parser.add_argument("--detect-only", action="store_true", help="Run pure contour/blob detector and print detected bounding boxes")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    helper = VisualSoMHelper()

    # Step 1: Zero-Token Visual Cache Lookup
    if (args.cache_lookup or args.component) and args.component and os.path.exists(args.image):
        cached_result = helper.lookup_cached_coordinates(
            component_name=args.component,
            image_source=args.image,
            threshold=args.threshold
        )
        if cached_result:
            if args.json:
                print(json.dumps({"status": "CACHE_HIT", "data": cached_result}, indent=2))
            else:
                print(f"\n⚡ [CACHE HIT - ZERO VISION TOKEN] Component '{args.component}' matched ({cached_result['visual_similarity']*100:.1f}% Similarity)")
                print(f"   Coordinates : ({cached_result['center_x']}, {cached_result['center_y']})")
                print(f"   Hit Count   : {cached_result['hit_count']}")
                print(f"   Action      : {cached_result['playwright_action']}\n")
            return 0

    # Auto-generate mock canvas if image doesn't exist
    if not os.path.exists(args.image):
        img = Image.new("RGB", (helper.viewport_width, helper.viewport_height), color="#1E1E2E")
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "Mock GIS & Financial Dashboard (HTML5 Canvas)", fill="#FFFFFF")
        draw.rectangle([100, 150, 220, 190], fill="#00CCFF", outline="#FFFFFF", width=2)
        draw.rectangle([240, 150, 360, 190], fill="#FF0055", outline="#FFFFFF", width=2)
        draw.rectangle([500, 300, 700, 350], fill="#00FF66", outline="#FFFFFF", width=2)
        img.save(args.image)

    # Detect Only
    if args.detect_only:
        blobs = helper.detect_canvas_interactive_regions(args.image)
        if args.json:
            print(json.dumps(blobs, indent=2))
        else:
            print(f"\n🔍 [CANVAS CONTOURS DETECTED] Found {len(blobs)} interactive regions:")
            for b in blobs:
                print(f"   • {b['label']}: Bounds {b['x']},{b['y']} ({b['width']}x{b['height']} px)")
        return 0

    # Load elements
    elements = []
    if args.elements_json:
        if os.path.exists(args.elements_json):
            with open(args.elements_json, "r", encoding="utf-8") as f:
                elements = json.load(f)
        else:
            try:
                elements = json.loads(args.elements_json)
            except Exception:
                pass

    if not elements:
        detected = helper.detect_canvas_interactive_regions(args.image)
        elements = detected if detected else [
            {"x": 100, "y": 150, "width": 120, "height": 40, "label": "TradingView Zoom In", "tag": "canvas_control"},
            {"x": 240, "y": 150, "width": 120, "height": 40, "label": "TradingView Zoom Out", "tag": "canvas_control"},
            {"x": 500, "y": 300, "width": 200, "height": 50, "label": "Execute Trade Order", "tag": "shadow_button"},
            {"x": 720, "y": 300, "width": 150, "height": 50, "label": "Cancel Order", "tag": "shadow_button"}
        ]

    marked_img, marks_map = helper.generate_som_overlay(args.image, elements, output_path=args.output)

    resolved = None
    target_query = args.label or args.component
    if args.mark_id is not None or target_query:
        resolved = helper.resolve_mark_coordinates(marks_map, target_mark_id=args.mark_id, target_label=target_query)

    # Cache Save if requested or if component is specified and resolved
    if resolved and (args.cache_save or args.component):
        comp_name = args.component or resolved["label"]
        helper.save_cached_coordinates(
            component_name=comp_name,
            image_source=args.image,
            center_x=resolved["center_x"],
            center_y=resolved["center_y"]
        )

    if args.json:
        result = {
            "marked_image": marked_img,
            "total_marks": len(marks_map),
            "marks": marks_map,
            "resolved_target": resolved
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n🎨 [SET-OF-MARKS GENERATED] Marked image: {marked_img}")
        print(f"   Candidate Visual Regions: {len(marks_map)}")
        for mid, data in marks_map.items():
            print(f"   [{mid}] {data['label']} at ({data['center_x']}, {data['center_y']})")
        if resolved:
            print(f"\n🎯 [COORDINATE GROUNDED] Target '{resolved['label']}' -> Mark #{resolved['mark_id']}")
            print(f"   Playwright Mouse Action: {resolved['playwright_action']}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
