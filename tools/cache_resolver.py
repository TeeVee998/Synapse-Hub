#!/usr/bin/env python3
"""
Universal Local Semantic Memory Cache & Self-Healing Resolver
-------------------------------------------------------------
Provides 100% Offline, Zero-Token diagnostic resolution for known test failures.
Saves solutions directly into an SQLite database (tools/memory_cache.db).
When identical failures occur, returns pre-tested patches with 0 LLM Tokens.

Features:
1. Positive Memory Cache (healing_cache): Pre-tested, verified code patches.
2. Negative Memory Cache (failed_fixes): Blacklist tracking incorrect patches,
   preventing AI Agents from falling into Blind Retry Loops.
"""

import sys
import os
import sqlite3
import json
import argparse
import re
import math
import time
import functools
from collections import Counter
from datetime import datetime

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

GLOBAL_DIR = os.path.expanduser("~/.agent_memory")
GLOBAL_DB = os.path.join(GLOBAL_DIR, "global_cache.db")
LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_cache.db")


def resolve_db_path(use_local=False):
    """Returns the SQLite database path. Defaults to Global Central Memory."""
    if use_local:
        return LOCAL_DB
    os.makedirs(GLOBAL_DIR, exist_ok=True)
    return GLOBAL_DB


DB_FILE = resolve_db_path()

SEED_SOLUTIONS = [
    {
        "error_signature": "ElementClickInterceptedException",
        "module_name": "GLOBAL",
        "symptom": "Modal backdrop or PrimeNG overlay (.p-component-overlay) blocks button click.",
        "root_cause": "Angular PrimeNG animation fade-out latency.",
        "groovy_patch": "((JavascriptExecutor) driver).executeScript(\"arguments[0].click();\", element);"
    },
    {
        "error_signature": "Save_Button_Disabled",
        "module_name": "GLOBAL",
        "symptom": "Save button [ Submit ] remains dimmed/disabled.",
        "root_cause": "Angular Reactive Form missing synthetic input/change event or required field empty.",
        "groovy_patch": "WebElement el = findElement(By.cssSelector(\"input[formcontrolname='code']\"));\njsSetInput(el, uniqueCode);"
    },
    {
        "error_signature": "StaleElementReferenceException",
        "module_name": "GLOBAL",
        "symptom": "Element is not attached to the DOM.",
        "root_cause": "Angular re-rendered DOM node after async API response.",
        "groovy_patch": "for (int i = 0; i < 3; i++) {\n    try {\n        findElement(by).click();\n        break;\n    } catch (StaleElementReferenceException e) {\n        sleep(500);\n    }\n}"
    },
    {
        "error_signature": "Duplicate_Code_Error",
        "module_name": "GLOBAL",
        "symptom": "Toast alert: 'Code already exists' or 'Data already exists'.",
        "root_cause": "Hardcoded or non-unique test identifier collided with existing record.",
        "groovy_patch": "String code = BasePage.uniqueCode(\"AUTO_\");"
    },
    {
        "error_signature": "PrimeNG_Dropdown_Empty",
        "module_name": "GLOBAL",
        "symptom": "Dropdown item not clicked or panel not visible.",
        "root_cause": "Overlay panel (.p-dropdown-panel) has not rendered when click dispatched.",
        "groovy_patch": "waitForElementVisible(By.cssSelector(\".p-dropdown-panel\"), 5);\nfindElement(By.xpath(\"//li[contains(., '\" + text + \"')]\")).click();"
    },
    {
        "error_signature": "BlockUI_TimeoutException",
        "module_name": "GLOBAL",
        "symptom": "Timeout waiting for table or form interaction.",
        "root_cause": "PrimeNG loading mask (.p-blockui, .p-progress-spinner) still active.",
        "groovy_patch": "waitForElementNotVisible(By.cssSelector(\".p-blockui, .p-progress-spinner\"), 10);"
    }
]

SEED_LESSONS_LEARNED = [
    {
        "page_context": "Checkout / Payment",
        "error_signature": "ElementClickInterceptedException",
        "root_cause": "Debounce 300ms hoặc PrimeNG overlay (.p-component-overlay) đang mờ dần.",
        "failed_attempt": "findElement(By.id('confirm-btn')).click();",
        "successful_fix": "waitForElementNotVisible('.p-component-overlay', 5); jsClick(btn);",
        "lesson_summary": "Tại Checkout/Payment, button Confirm bị debounce hoặc overlay animation; không click trực tiếp mà phải đợi overlay biến mất hoặc dùng clickJS/clickSafe."
    },
    {
        "page_context": "Auth / Reactive Forms",
        "error_signature": "Save_Button_Disabled / FormInvalid",
        "root_cause": "Angular Reactive Form không nhận native DOM value do thiếu Zone.js synthetic input event.",
        "failed_attempt": "input.sendKeys(uniqueCode); submitBtn.click();",
        "successful_fix": "jsSetInput(input, uniqueCode); qa.audit();",
        "lesson_summary": "Tại các form Angular/React, sendKeys chay không trigger validity; bắt buộc dispatch synthetic input/change event hoặc dùng qa.audit."
    },
    {
        "page_context": "Data Mining / Async Table",
        "error_signature": "StaleElementReferenceException",
        "root_cause": "Bảng dữ liệu re-render DOM node sau khi nhận API response bất đồng bộ.",
        "failed_attempt": "tableRows.get(0).click();",
        "successful_fix": "waitForElementNotVisible('.p-blockui, .p-progress-spinner', 10); retryClick(row);",
        "lesson_summary": "Tại bảng dữ liệu async, tuyệt đối không click row ngay lập tức; phải đợi BlockUI/Spinner biến mất hoàn toàn để tránh Stale Element."
    }
]

SEED_FAILED_FIXES = [
    {
        "error_signature": "StaleElementReferenceException",
        "attempted_patch": "Thread.sleep(3000); findElement(by).click();",
        "failure_reason": "Causes pipeline flakiness; fails whenever network lag or server response exceeds static sleep duration.",
        "agent_role": "pom-crafter"
    },
    {
        "error_signature": "ElementClickInterceptedException",
        "attempted_patch": "new Actions(driver).moveToElement(el).click().perform();",
        "failure_reason": "Still blocked by modal backdrop because backdrop element sits physically above target element in z-index.",
        "agent_role": "failure-analyst"
    },
    {
        "error_signature": "Save_Button_Disabled",
        "attempted_patch": "el.sendKeys(uniqueCode);",
        "failure_reason": "Standard Selenium sendKeys does not fire Angular Zone.js synthetic input/change events, leaving formControl invalid.",
        "agent_role": "pom-crafter"
    }
]


def retry_on_locked(max_retries=5, initial_delay=0.05, backoff=2.0):
    """Decorator to retry SQLite operations if database is locked or busy."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_err = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_err = e
                    err_msg = str(e).lower()
                    if "locked" in err_msg or "busy" in err_msg:
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        raise
            if last_err:
                raise last_err
        return wrapper
    return decorator


def get_db(db_path=None, timeout=30.0):
    """Returns a resilient SQLite connection configured with WAL mode and busy timeout."""
    target = db_path or DB_FILE
    conn = sqlite3.connect(target, timeout=timeout)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
    except Exception:
        pass
    return conn


@retry_on_locked()
def init_db(seed=True, target_db=None):
    current_db = target_db or DB_FILE
    with get_db(current_db) as conn:
        cursor = conn.cursor()
        # 1. Positive Memory Table (Verified Working Patches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS healing_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT NOT NULL,
                module_name TEXT DEFAULT 'GLOBAL',
                symptom TEXT,
                root_cause TEXT,
                groovy_patch TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(error_signature, module_name)
            )
        """)

        # 2. Negative Memory Table (Blacklist of Failed Fix Attempts)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failed_fixes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT NOT NULL,
                attempted_patch TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                agent_role TEXT DEFAULT 'pom-crafter',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Episodic Reflexion Table (Historical Lessons Learned)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons_learned (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_context TEXT DEFAULT 'GLOBAL',
                error_signature TEXT NOT NULL,
                root_cause TEXT,
                failed_attempt TEXT,
                successful_fix TEXT,
                lesson_summary TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Migrate existing solutions from local DB if initializing global DB for the first time
        if current_db == GLOBAL_DB and os.path.exists(LOCAL_DB):
            try:
                local_conn = get_db(LOCAL_DB)
                rows = local_conn.execute("SELECT * FROM healing_cache").fetchall()
                for r in rows:
                    cursor.execute("""
                        INSERT OR IGNORE INTO healing_cache 
                        (error_signature, module_name, symptom, root_cause, groovy_patch, hit_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (r["error_signature"], r["module_name"], r["symptom"], r["root_cause"], r["groovy_patch"], r["hit_count"]))
                conn.commit()
                local_conn.close()
            except Exception:
                pass

        if seed:
            for s in SEED_SOLUTIONS:
                cursor.execute("""
                    INSERT OR IGNORE INTO healing_cache 
                    (error_signature, module_name, symptom, root_cause, groovy_patch)
                    VALUES (?, ?, ?, ?, ?)
                """, (s["error_signature"], s["module_name"], s["symptom"], s["root_cause"], s["groovy_patch"]))

            for f in SEED_FAILED_FIXES:
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM failed_fixes 
                    WHERE error_signature = ? AND attempted_patch = ?
                """, (f["error_signature"], f["attempted_patch"]))
                if cursor.fetchone()["cnt"] == 0:
                    cursor.execute("""
                        INSERT INTO failed_fixes (error_signature, attempted_patch, failure_reason, agent_role)
                        VALUES (?, ?, ?, ?)
                    """, (f["error_signature"], f["attempted_patch"], f["failure_reason"], f["agent_role"]))

            for l in SEED_LESSONS_LEARNED:
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM lessons_learned 
                    WHERE error_signature = ? AND page_context = ?
                """, (l["error_signature"], l["page_context"]))
                if cursor.fetchone()["cnt"] == 0:
                    cursor.execute("""
                        INSERT INTO lessons_learned 
                        (page_context, error_signature, root_cause, failed_attempt, successful_fix, lesson_summary)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (l["page_context"], l["error_signature"], l["root_cause"], l["failed_attempt"], l["successful_fix"], l["lesson_summary"]))
            conn.commit()


# Stop-words list filtering generic stacktrace, code runtime & English grammar noise
STOP_WORDS = {
    # English stop words
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these",
    "they", "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "where",
    "which", "while", "who", "whom", "why", "with", "won't", "would", "wouldn't",
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",

    # Java / Groovy / Selenium / Katalon Stacktrace & Runtime Boilerplate Noise
    "org", "com", "net", "io", "java", "lang", "util", "reflect", "sun", "native",
    "impl", "accessor", "unknown", "source", "line", "method", "thread", "run",
    "call", "invoke", "invoker", "kms", "katalon", "core", "webui", "keyword",
    "builtin", "driver", "webdriver", "remote", "http", "internal", "client",
    "server", "session", "step", "tc", "test", "tests", "case", "suite", "runner",
    "element", "elements", "locator", "find", "finding", "found", "selenium",
    "openqa", "chrome", "firefox", "edge", "safari", "webkit",

    # Generic Error Noise (present in almost all failure traces)
    "exception", "error", "failed", "failure", "caused", "cause", "trace",
    "stacktrace", "message", "warning", "info", "debug", "null", "object"
}


def tokenize(text):
    """
    Extracts tokens with CamelCase decomposition and Stop-words stripping.
    Preserves specific domain identifiers while eliminating generic stacktrace noise.
    """
    if not text:
        return []
    words = re.findall(r'[a-zA-Z0-9_\-]+', text)
    tokens = []
    for w in words:
        w_lower = w.lower().strip("-_")
        # Filter Katalon / Framework built-in keyword class noise (e.g. ClickKeyword, SetTextKeyword)
        if w_lower.endswith("keyword"):
            continue
        if len(w_lower) >= 2 and w_lower not in STOP_WORDS:
            tokens.append(w_lower)
        # Split CamelCase: "ElementClickIntercepted" -> "click", "intercepted"
        camel_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', w)
        if len(camel_parts) > 1:
            for cp in camel_parts:
                cp_lower = cp.lower().strip("-_")
                if len(cp_lower) >= 2 and cp_lower not in STOP_WORDS and not cp_lower.endswith("keyword"):
                    tokens.append(cp_lower)
    return tokens


def compute_tfidf_similarities(query, documents):
    """
    Computes TF-IDF weighted cosine similarity between a query and a candidate document corpus.
    Applies inverse document frequency to dampen frequent boilerplate words and amplify
    rare diagnostic markers (e.g. 'stale', 'intercepted', 'ng-invalid').
    """
    query_tokens = tokenize(query)
    if not query_tokens or not documents:
        return [0.0] * len(documents)

    doc_tokens_list = [tokenize(doc) for doc in documents]
    all_docs = [query_tokens] + doc_tokens_list
    total_docs = len(all_docs)

    # Document Frequency across the combined corpus
    df = Counter()
    for doc in all_docs:
        for token in set(doc):
            df[token] += 1

    # Smoothed IDF: ln(1 + N / (1 + df)) + 1
    idf = {t: math.log(1.0 + total_docs / (1.0 + freq)) + 1.0 for t, freq in df.items()}

    def get_tfidf_vec(tokens):
        tf = Counter(tokens)
        vec = {}
        for t, count in tf.items():
            vec[t] = (1.0 + math.log(count)) * idf.get(t, 1.0)
        return vec

    def norm(vec):
        return math.sqrt(sum(val ** 2 for val in vec.values()))

    query_vec = get_tfidf_vec(query_tokens)
    query_norm = norm(query_vec)
    if not query_norm:
        return [0.0] * len(documents)

    scores = []
    for doc_tokens in doc_tokens_list:
        if not doc_tokens:
            scores.append(0.0)
            continue
        doc_vec = get_tfidf_vec(doc_tokens)
        doc_norm = norm(doc_vec)
        if not doc_norm:
            scores.append(0.0)
            continue
        dot = sum(query_vec[t] * doc_vec[t] for t in set(query_vec.keys()) & set(doc_vec.keys()))
        scores.append(float(dot) / (query_norm * doc_norm))

    return scores


def compute_cosine_similarity(text1, text2):
    """
    Computes tokenized Cosine Similarity between two texts with stop-words filtration.
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
    vec1 = Counter(tokens1)
    vec2 = Counter(tokens2)
    intersection = set(vec1.keys()) & set(vec2.keys())
    if not intersection:
        return 0.0
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([val**2 for val in vec1.values()])
    sum2 = sum([val**2 for val in vec2.values()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator


def get_failed_fixes(error_signature):
    """Retrieves all previously recorded failed fix attempts for this error signature."""
    init_db(seed=True)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM failed_fixes 
            WHERE error_signature = ? OR error_signature LIKE ?
            ORDER BY created_at DESC
        """, (error_signature, f"%{error_signature}%"))
        return [dict(r) for r in cursor.fetchall()]


@retry_on_locked()
def record_failed_fix(error_signature, attempted_patch, failure_reason, agent_role="pom-crafter"):
    """Records a failed bug fix attempt into negative memory so AI agents will never repeat it."""
    init_db(seed=True)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO failed_fixes (error_signature, attempted_patch, failure_reason, agent_role)
            VALUES (?, ?, ?, ?)
        """, (error_signature, attempted_patch, failure_reason, agent_role))
        conn.commit()
        return True


def query_solution(error_signature, module_name="GLOBAL", threshold=0.35):
    """
    Two-Way Query:
    1. Returns verified working patch from positive memory.
    2. Attaches blacklist of previously failed fixes from negative memory.
    """
    init_db(seed=True)
    with get_db() as conn:
        cursor = conn.cursor()
        # 1. Exact match with module
        cursor.execute("""
            SELECT * FROM healing_cache 
            WHERE error_signature = ? AND module_name = ?
        """, (error_signature, module_name))
        row = cursor.fetchone()
        match_type = "EXACT_MODULE"

        # 2. Fallback to GLOBAL match
        if not row:
            cursor.execute("""
                SELECT * FROM healing_cache 
                WHERE error_signature = ? AND module_name = 'GLOBAL'
            """, (error_signature,))
            row = cursor.fetchone()
            match_type = "GLOBAL_MATCH"

        # 3. Fuzzy search on symptom/error
        if not row:
            cursor.execute("""
                SELECT * FROM healing_cache 
                WHERE error_signature LIKE ? OR symptom LIKE ?
            """, (f"%{error_signature}%", f"%{error_signature}%"))
            row = cursor.fetchone()
            match_type = "FUZZY_SQL"

        # 4. Offline Semantic Vector TF-IDF Cosine Similarity
        confidence = 1.0
        if not row:
            cursor.execute("SELECT * FROM healing_cache")
            all_rows = cursor.fetchall()
            if all_rows:
                candidates_corpus = [
                    f"{c['error_signature']} {c['symptom']} {c['root_cause']}"
                    for c in all_rows
                ]
                scores = compute_tfidf_similarities(error_signature, candidates_corpus)
                best_idx = -1
                best_score = 0.0
                for idx, score in enumerate(scores):
                    if score > best_score:
                        best_score = score
                        best_idx = idx

                if best_idx >= 0 and best_score >= threshold:
                    row = all_rows[best_idx]
                    match_type = f"SEMANTIC_TFIDF ({best_score*100:.1f}%)"
                    confidence = best_score

        # Query negative memory for this error
        failed_fixes = get_failed_fixes(error_signature)

        if row:
            cursor.execute("""
                UPDATE healing_cache 
                SET hit_count = hit_count + 1 
                WHERE id = ?
            """, (row["id"],))
            conn.commit()
            result = dict(row)
            result["match_type"] = match_type
            result["confidence"] = confidence
            result["failed_fixes"] = failed_fixes
            return result
        elif failed_fixes:
            # No solution yet, but we have failed fixes recorded!
            return {
                "error_signature": error_signature,
                "module_name": module_name,
                "symptom": "Unknown solution",
                "root_cause": "Unknown",
                "groovy_patch": None,
                "match_type": "NEGATIVE_MEMORY_ONLY",
                "confidence": 0.0,
                "failed_fixes": failed_fixes
            }
        return None


@retry_on_locked()
def learn_solution(error_signature, module_name, symptom, root_cause, groovy_patch):
    """Saves a verified solution into positive memory."""
    init_db(seed=True)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO healing_cache (error_signature, module_name, symptom, root_cause, groovy_patch)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(error_signature, module_name) DO UPDATE SET
                symptom = excluded.symptom,
                root_cause = excluded.root_cause,
                groovy_patch = excluded.groovy_patch
        """, (error_signature, module_name or "GLOBAL", symptom, root_cause, groovy_patch))
        conn.commit()
        return True


@retry_on_locked()
def sync_db():
    """Bidirectional synchronization between Global Central Memory and Local Project Cache."""
    global DB_FILE
    # Initialize schemas for both Global and Local stores prior to sync
    DB_FILE = resolve_db_path(use_local=False)
    init_db(seed=True, target_db=GLOBAL_DB)
    DB_FILE = resolve_db_path(use_local=True)
    init_db(seed=False, target_db=LOCAL_DB)
    
    g_conn = get_db(GLOBAL_DB)
    l_conn = get_db(LOCAL_DB)
    
    # 1. Sync positive cache
    g_rows = g_conn.execute("SELECT * FROM healing_cache").fetchall()
    for r in g_rows:
        l_conn.execute("""
            INSERT INTO healing_cache (error_signature, module_name, symptom, root_cause, groovy_patch, hit_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(error_signature, module_name) DO UPDATE SET
                symptom = excluded.symptom,
                root_cause = excluded.root_cause,
                groovy_patch = excluded.groovy_patch
        """, (r["error_signature"], r["module_name"], r["symptom"], r["root_cause"], r["groovy_patch"], r["hit_count"]))
    l_conn.commit()

    l_rows = l_conn.execute("SELECT * FROM healing_cache").fetchall()
    for r in l_rows:
        g_conn.execute("""
            INSERT INTO healing_cache (error_signature, module_name, symptom, root_cause, groovy_patch, hit_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(error_signature, module_name) DO UPDATE SET
                symptom = excluded.symptom,
                root_cause = excluded.root_cause,
                groovy_patch = excluded.groovy_patch
        """, (r["error_signature"], r["module_name"], r["symptom"], r["root_cause"], r["groovy_patch"], r["hit_count"]))
    g_conn.commit()

    # 2. Sync negative failed fixes
    g_failed = g_conn.execute("SELECT * FROM failed_fixes").fetchall()
    for f in g_failed:
        l_conn.execute("""
            INSERT OR IGNORE INTO failed_fixes (error_signature, attempted_patch, failure_reason, agent_role)
            VALUES (?, ?, ?, ?)
        """, (f["error_signature"], f["attempted_patch"], f["failure_reason"], f["agent_role"]))
    l_conn.commit()

    # 3. Sync lessons learned
    g_lessons = g_conn.execute("SELECT * FROM lessons_learned").fetchall()
    for r in g_lessons:
        l_conn.execute("""
            INSERT OR IGNORE INTO lessons_learned 
            (page_context, error_signature, root_cause, failed_attempt, successful_fix, lesson_summary, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r["page_context"], r["error_signature"], r["root_cause"], r["failed_attempt"], r["successful_fix"], r["lesson_summary"], r["hit_count"]))
    l_conn.commit()

    l_conn.close()
    g_conn.close()
    return len(g_rows)


@retry_on_locked()
def record_lesson(page_context, error_signature, root_cause, failed_attempt, successful_fix, lesson_summary):
    """
    Episodic Reflexion Memory:
    Records a concise lesson learned (maximum 2 lines) into SQLite for cross-session reflection.
    """
    init_db(seed=True)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lessons_learned 
            (page_context, error_signature, root_cause, failed_attempt, successful_fix, lesson_summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (page_context or "GLOBAL", error_signature, root_cause, failed_attempt, successful_fix, lesson_summary.strip()))
        conn.commit()
        return True


def query_lessons(context_or_keyword, limit=2):
    """
    Episodic Reflexion Memory Query:
    Retrieves the top N (default: 2) most relevant historical lessons learned for a given page, flow, or error.
    Returns: List[Dict[str, Any]]
    """
    init_db(seed=True)
    if not context_or_keyword:
        context_or_keyword = "GLOBAL"

    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM lessons_learned").fetchall()
        if not rows:
            return []

        scored = []
        q_lower = context_or_keyword.lower()
        for r in rows:
            combined = f"{r['page_context']} {r['error_signature']} {r['lesson_summary']} {r['root_cause'] or ''}"
            sim_score = compute_cosine_similarity(context_or_keyword, combined)

            # Boost score for explicit matches in page_context or error_signature
            if r["page_context"] and r["page_context"].lower() in q_lower:
                sim_score += 0.40
            if r["error_signature"] and r["error_signature"].lower() in q_lower:
                sim_score += 0.35

            scored.append((sim_score, dict(r)))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_results = [item[1] for item in scored[:limit]]

        for item in top_results:
            cursor.execute("UPDATE lessons_learned SET hit_count = hit_count + 1 WHERE id = ?", (item["id"],))
        conn.commit()

        return top_results


def get_stats():
    init_db(seed=True)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total_solutions, SUM(hit_count) as total_hits FROM healing_cache")
        row = cursor.fetchone()
        total_sol = row["total_solutions"] or 0
        total_hits = row["total_hits"] or 0
        saved_tokens = total_hits * 2000

        cursor.execute("SELECT COUNT(*) as total_failed FROM failed_fixes")
        total_failed = cursor.fetchone()["total_failed"] or 0

        cursor.execute("SELECT COUNT(*) as total_lessons FROM lessons_learned")
        total_lessons = cursor.fetchone()["total_lessons"] or 0

        cursor.execute("SELECT error_signature, module_name, hit_count FROM healing_cache ORDER BY hit_count DESC")
        top_solutions = [dict(r) for r in cursor.fetchall()]

        return {
            "total_solutions": total_sol,
            "total_hits": total_hits,
            "total_failed_fixes": total_failed,
            "total_lessons_learned": total_lessons,
            "estimated_tokens_saved": saved_tokens,
            "solutions": top_solutions
        }


def main():
    global DB_FILE
    parser = argparse.ArgumentParser(description="Enterprise Central Agent Memory & Self-Healing Resolver")
    parser.add_argument("--local", action="store_true", help="Force local project memory_cache.db instead of Global Central Memory")
    subparsers = parser.add_subparsers(dest="command")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query solution & anti-patches for an error (Zero Token)")
    query_parser.add_argument("--error", required=True, help="Error signature or keyword")
    query_parser.add_argument("--module", default="GLOBAL", help="Module or Page Class name")

    # Learn command (Positive Memory)
    learn_parser = subparsers.add_parser("learn", help="Save verified solution into positive memory")
    learn_parser.add_argument("--error", required=True, help="Error signature")
    learn_parser.add_argument("--module", default="GLOBAL", help="Module or Page Class name")
    learn_parser.add_argument("--symptom", required=True, help="Symptom description")
    learn_parser.add_argument("--cause", required=True, help="Root cause")
    learn_parser.add_argument("--patch", required=True, help="Working patch code")

    # Record-Failed command (Negative Memory)
    failed_parser = subparsers.add_parser("record-failed", help="Record a failed fix attempt into negative memory blacklist")
    failed_parser.add_argument("--error", required=True, help="Error signature being diagnosed")
    failed_parser.add_argument("--patch", required=True, help="The failed patch code or attempted action")
    failed_parser.add_argument("--reason", required=True, help="Why this fix failed or regression caused")
    failed_parser.add_argument("--role", default="pom-crafter", help="Agent role that attempted the fix")

    # Record-Lesson command (Episodic Reflexion Memory)
    lesson_record_parser = subparsers.add_parser("record-lesson", help="Record a 2-line lesson learned into episodic memory")
    lesson_record_parser.add_argument("--context", default="GLOBAL", help="Page name or workflow context (e.g., 'Checkout', 'Login')")
    lesson_record_parser.add_argument("--error", required=True, help="Error signature or breaking symptom")
    lesson_record_parser.add_argument("--cause", default="", help="Root cause explanation")
    lesson_record_parser.add_argument("--failed", default="", help="Failed attempt or anti-pattern")
    lesson_record_parser.add_argument("--fix", default="", help="Successful fix pattern")
    lesson_record_parser.add_argument("--lesson", required=True, help="Short lesson summary (maximum 2 lines)")

    # Get-Lessons command (Episodic Reflexion Memory Query)
    lesson_get_parser = subparsers.add_parser("get-lessons", help="Retrieve top 2 historical lessons learned for context")
    lesson_get_parser.add_argument("--context", required=True, help="Page, flow, or error keyword to match")
    lesson_get_parser.add_argument("--limit", type=int, default=2, help="Number of lessons to retrieve (default: 2)")

    # Stats command
    subparsers.add_parser("stats", help="View memory cache statistics (Positive & Negative)")

    # Sync command
    subparsers.add_parser("sync", help="Synchronize Global Central Memory with Local Project Cache")

    # Init command
    subparsers.add_parser("init", help="Initialize and seed database")

    args = parser.parse_args()
    if args.local:
        DB_FILE = resolve_db_path(use_local=True)
    else:
        DB_FILE = resolve_db_path(use_local=False)

    if args.command == "query":
        sol = query_solution(args.error, args.module)
        if sol:
            print("==================================================")
            if sol.get("groovy_patch"):
                print(f"✅ [CACHE HIT - 0 TOKENS] Found pre-tested solution!")
                print(f"Database Scope  : {'LOCAL' if args.local else 'GLOBAL CENTRAL (~/.agent_memory)'}")
                print(f"Match Strategy  : {sol.get('match_type', 'EXACT')}")
                print(f"Error Signature : {sol['error_signature']}")
                print(f"Module Scope    : {sol['module_name']}")
                print(f"Root Cause      : {sol['root_cause']}")
                print(f"Hit Count       : {sol.get('hit_count', 0)}")
                print("--------------------------------------------------")
                print("💡 Recommended Healing Patch:")
                print(sol["groovy_patch"])
            else:
                print(f"⚠️ [NO VERIFIED SOLUTION YET] for error: '{args.error}'")

            failed_fixes = sol.get("failed_fixes", [])
            if failed_fixes:
                print("--------------------------------------------------")
                print(f"🚫 FORBIDDEN ANTI-PATCHES ({len(failed_fixes)} previously failed - DO NOT REPEAT):")
                for idx, ff in enumerate(failed_fixes, 1):
                    print(f"  {idx}. [FAILED ATTEMPT by {ff.get('agent_role', 'agent')}]:")
                    print(f"     Patch : {ff.get('attempted_patch')}")
                    print(f"     Reason: {ff.get('failure_reason')}")
            print("==================================================")
        else:
            print(f"❌ [CACHE MISS] No cached solution found for: '{args.error}'. Triggering LLM reasoning.")
            sys.exit(1)

    elif args.command == "learn":
        ok = learn_solution(args.error, args.module, args.symptom, args.cause, args.patch)
        if ok:
            print(f"✅ [POSITIVE MEMORY LEARNED] Solution for '{args.error}' ({args.module}) cached successfully.")

    elif args.command == "record-failed":
        ok = record_failed_fix(args.error, args.patch, args.reason, args.role)
        if ok:
            print(f"🚫 [NEGATIVE MEMORY RECORDED] Failed fix attempt for '{args.error}' added to blacklist.")
            print(f"   Agent Role : {args.role}")
            print(f"   Reason     : {args.reason}")

    elif args.command == "record-lesson":
        ok = record_lesson(args.context, args.error, args.cause, args.failed, args.fix, args.lesson)
        if ok:
            print(f"🧠 [EPISODIC REFLEXION RECORDED] Lesson for context '{args.context}' cached successfully.")
            print(f"   Error Signature : {args.error}")
            print(f"   Lesson (2 lines): {args.lesson.strip()}")

    elif args.command == "get-lessons":
        lessons = query_lessons(args.context, limit=args.limit)
        print("==================================================")
        print(f"🧠 [EPISODIC REFLEXION MEMORY] Top {len(lessons)} Lessons for: '{args.context}'")
        print("==================================================")
        if not lessons:
            print("  (Zero relevant lessons in cache yet. Proceeding with clean reasoning.)")
        else:
            for idx, l in enumerate(lessons, 1):
                print(f"📌 [Lesson {idx}] Context: {l['page_context']} | Trigger: {l['error_signature']}")
                print(f"   💡 Rule: {l['lesson_summary']}")
                if l.get("failed_attempt") or l.get("successful_fix"):
                    print(f"   ⚠️ Anti-Pattern: {l.get('failed_attempt') or 'N/A'}")
                    print(f"   ✅ Proven Fix  : {l.get('successful_fix') or 'N/A'}")
        print("==================================================")

    elif args.command == "stats":
        stats = get_stats()
        print("==================================================")
        print(f"📊 AGENT MEMORY CACHE STATISTICS ({'LOCAL' if args.local else 'GLOBAL CENTRAL'})")
        print(f"Database Path           : {DB_FILE}")
        print(f"Verified Solutions (✅)  : {stats['total_solutions']}")
        print(f"Failed Fixes Blacklist (🚫): {stats['total_failed_fixes']}")
        print(f"Lessons Learned (🧠)      : {stats.get('total_lessons_learned', 0)}")
        print(f"Total Cache Hits        : {stats['total_hits']}")
        print(f"Estimated Tokens Saved  : ~{stats['estimated_tokens_saved']:,} tokens")
        print("--------------------------------------------------")
        print("Top Solutions by Hit Count:")
        for s in stats["solutions"]:
            print(f" - [{s['hit_count']} hits] {s['error_signature']} ({s['module_name']})")
        print("==================================================")

    elif args.command == "sync":
        count = sync_db()
        print(f"✅ [MEMORY SYNC] Bidirectional sync completed ({count} solutions synchronized between Global & Local).")

    elif args.command == "init" or args.command is None:
        init_db(seed=True)
        print(f"✅ Central Agent Memory initialized at: {DB_FILE}")


if __name__ == "__main__":
    main()
