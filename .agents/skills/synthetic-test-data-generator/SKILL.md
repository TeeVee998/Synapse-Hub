---
name: synthetic-test-data-generator
description: "Generate idempotent, boundary-value synthetic test data with unique runtime timestamps."
---

# Synthetic Test Data Generator & Edge-Case Fuzzing Skill

> **Target:** Eliminate database collisions, race conditions in parallel testing, and stale fixture dependencies by dynamically generating valid, boundary-value, and edge-case fuzzing datasets.

---

## 1. Core Principles

1. **Idempotence & Unique Prefixing:**
   - Every generated string or identifier must contain an execution timestamp or UUID prefix (`AUTO_1719500000_...`) to allow parallel test executions without unique-key database collisions.
2. **Boundary Value Testing (BVT):**
   - Automatically cover equivalence partitions:
     - Null / Empty / Whitespace-only strings.
     - Max length limits (e.g. 255 chars, 1,024 chars, 10,000 chars text blocks).
     - Special characters, emojis, SQL injection probe strings (`' OR '1'='1' -- `), XSS polyglots (`<img src=x onerror=console.warn('qa_xss')>`).
     - Negative numbers, extreme floats, zero, boundary integer limits (`2^31 - 1`, `2^63 - 1`, `Number.MAX_SAFE_INTEGER`).
3. **Domain-Specific Constraints:**
   - Tax IDs, phone numbers, email RFC formats, and GIS coordinates (e.g., non-overlapping closed polygons).

---

## 2. Standard Generation Recipes

### Recipe A: Dynamic Unique Entity Names
```typescript
export class TestDataFactory {
  static uniqueName(prefix: string = 'AUTO'): string {
    const timestamp = Date.now().toString(36).toUpperCase();
    const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `${prefix}_${timestamp}_${randomSuffix}`;
  }

  static validEmail(prefix: string = 'tester'): string {
    return `${prefix}.${Date.now()}@example-testing.com`;
  }
}
```

### Recipe B: Boundary Value String Suite
```json
{
  "boundaryStrings": [
    "",
    "   ",
    "A",
    "A".repeat(255),
    "A".repeat(1024),
    "Tiếng Việt có dấu: Cà phê sữa đá & Trắc nghiệm chất lượng",
    "Special chars: !@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./",
    "Unicode emojis: 🚀🔥⚡🧪✨",
    "XSS probe: <img src=x onerror=alert('qa')>",
    "SQLi probe: ' OR '1'='1' -- "
  ]
}
```

### Recipe C: GeoJSON / GIS Valid Non-Overlapping Polygons
```typescript
export function generateValidPolygon(centerLat = 21.0285, centerLng = 105.8542, offset = 0.005) {
  // Generates closed 5-point polygon bounding box
  return [
    [centerLng - offset, centerLat - offset],
    [centerLng + offset, centerLat - offset],
    [centerLng + offset, centerLat + offset],
    [centerLng - offset, centerLat + offset],
    [centerLng - offset, centerLat - offset] // Close ring
  ];
}
```

---

## 3. Edge-Case Fuzzing & Input Sanitization Suite (`tools/fuzz_payloads.py`)

Transform functional tests into input sanitization and robustness validation by executing edge-case fuzzing vectors:

```bash
# Query CLI catalog for specific field vectors
python3 ~/.zcode/synapse-hub/tools/fuzz_payloads.py --field username --type string
python3 ~/.zcode/synapse-hub/tools/fuzz_payloads.py --category sqli --json
```

### Recipe D: Harmless SQLi Polyglot Sanity
```typescript
export const SQLI_FUZZ_PROBES = [
  "' OR '1'='1' -- ",
  "SLEEP(0)/*'/*\"/*--",
  "1' UNION SELECT NULL, NULL, NULL -- ",
  "admin' -- ",
  "'; WAITFOR DELAY '0:0:0'--"
];
// Assertion: Application must return HTTP 400 or sanitize safely; MUST NEVER throw 500 SQLException.
```

### Recipe E: Unicode BiDi & RTL Trojan Source Vectors
```typescript
export const BIDI_FUZZ_PROBES = [
  "\u202E\u0041\u0042\u0043_AUTO_TX", // Right-to-Left Override (RLO)
  "AUTO\u200B\u200C\u200D_DATA",       // Zero-Width Space & Joiner
  "\uFEFFAUTO_USER",                   // In-string Byte Order Mark (BOM)
  "USER_مرحبا_بالعالم_2026"            // Mixed Latin/Arabic BiDi text
];
// Assertion: Database persistence and frontend display must not corrupt visual hierarchy or inject Trojan Source spoofing.
```

### Recipe F: Multi-Byte Emoji Surrogate Pairs & ZWJ Sequences
```typescript
export const EMOJI_FUZZ_PROBES = [
  "👨‍👩‍👧‍👦_QA_RECORD",      // Complex Zero-Width Joiner family sequence
  "🏳️‍🌈_FLAG_TAG",          // Multi-code point flag sequence
  "\uD83D\uDE00\uD83D",     // Unpaired surrogate boundary test
  "🔥🚀⚡🧪✨"               // 4-byte high-plane UTF-8 characters
];
// Assertion: Backend UTF-8 MB4 column encoding must persist without truncation or 1366 Incorrect string value error.
```

### Recipe G: Extreme Length Buffer Stress ($10^4$ Characters)
```typescript
export const BUFFER_STRESS_PAYLOADS = [
  "A".repeat(10000),         // 10,000 chars text block
  "X".repeat(1024),          // Standard 1KB boundary
  '{"test": [' + Array(500).fill('1').join(',') + ']}' // Repetitive JSON nesting
];
// Assertion: API must reject with 400/413 Payload Too Large; frontend form controls must enforce max-length clipping.
```

---

## 4. Teardown & Lifecycle Integration
- Every test generating persistent records with `synthetic-test-data-generator` **MUST** register the generated ID into a teardown queue to clean up after test execution completes.
