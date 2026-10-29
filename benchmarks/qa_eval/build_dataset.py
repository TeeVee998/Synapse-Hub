#!/usr/bin/env python3
"""
QA Eval Benchmark Dataset Generator
-----------------------------------
Generates 25 realistic, production-grade test failure challenges across 5 domains.
"""

import os
import sys
import json

# Enforce UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")

CHALLENGES = [
    # --- DOMAIN 1: LOCATOR DRIFT & DOM SHIFTS ---
    {
        "category_dir": "locator_drift",
        "data": {
            "id": "QA-CHALLENGE-01",
            "name": "Dynamic CSS-in-JS Hash Locator Shift",
            "category": "locator_drift",
            "difficulty": "MEDIUM",
            "description": "Button class changed from '.btn-submit' to dynamic hashed class '.btn-submit_a8f9x2'.",
            "failure_vector": {
                "type": "LOCATOR_DRIFT",
                "broken_locator": "button.btn-submit",
                "error_log": "ElementNotFoundException: Cannot locate element with selector 'button.btn-submit' within 5000ms",
                "dom_snapshot": "<button class='btn-submit_a8f9x2' data-testid='submit-order-btn' role='button' aria-label='Submit Order'>Submit Order</button>"
            },
            "expected_resolution": {
                "healed_locator": "[data-testid='submit-order-btn']",
                "fallback_locator": "button:has-text('Submit Order')",
                "strategy": "AOM_ROLE_OR_TESTID"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 350,
                "min_confidence_score": 0.85
            }
        }
    },
    {
        "category_dir": "locator_drift",
        "data": {
            "id": "QA-CHALLENGE-02",
            "name": "Nested Shadow DOM Component Piercing",
            "category": "locator_drift",
            "difficulty": "HARD",
            "description": "Input field moved inside Web Component with '#shadow-root (open)'.",
            "failure_vector": {
                "type": "SHADOW_DOM_ISOLATION",
                "broken_locator": "#customer-email",
                "error_log": "NoSuchElementException: Element '#customer-email' not found in document root",
                "dom_snapshot": "<user-profile-card><template shadowrootmode='open'><input id='customer-email' type='email' data-testid='user-email'/></template></user-profile-card>"
            },
            "expected_resolution": {
                "healed_locator": "user-profile-card >> internal:control=enter-shadow >> input#customer-email",
                "fallback_locator": "user-profile-card >> input[type='email']",
                "strategy": "SHADOW_DOM_PIERCING"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 3.0,
                "max_token_cost": 400,
                "min_confidence_score": 0.88
            }
        }
    },
    {
        "category_dir": "locator_drift",
        "data": {
            "id": "QA-CHALLENGE-03",
            "name": "Semantic Text Label Evolution",
            "category": "locator_drift",
            "difficulty": "EASY",
            "description": "CTA button label text changed from 'Submit Order' to 'Complete Purchase'.",
            "failure_vector": {
                "type": "LABEL_EVOLUTION",
                "broken_locator": "//button[text()='Submit Order']",
                "error_log": "TimeoutException: Timed out waiting for element with XPath //button[text()='Submit Order']",
                "dom_snapshot": "<button type='submit' class='p-button-success' id='order-cta'>Complete Purchase</button>"
            },
            "expected_resolution": {
                "healed_locator": "#order-cta",
                "fallback_locator": "button[type='submit']",
                "strategy": "ID_AND_SEMANTIC_INTENT"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 300,
                "min_confidence_score": 0.90
            }
        }
    },
    {
        "category_dir": "locator_drift",
        "data": {
            "id": "QA-CHALLENGE-04",
            "name": "Legacy ID Removed in Favor of data-testid",
            "category": "locator_drift",
            "difficulty": "EASY",
            "description": "Frontend framework removed legacy 'id=customer_name' during React refactor.",
            "failure_vector": {
                "type": "ID_REMOVAL",
                "broken_locator": "#customer_name",
                "error_log": "ElementNotFoundException: Cannot locate element '#customer_name'",
                "dom_snapshot": "<input type='text' name='customerName' data-testid='customer-name-field' class='form-control'/>"
            },
            "expected_resolution": {
                "healed_locator": "[data-testid='customer-name-field']",
                "fallback_locator": "input[name='customerName']",
                "strategy": "DATA_TESTID_UPGRADE"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 250,
                "min_confidence_score": 0.92
            }
        }
    },
    {
        "category_dir": "locator_drift",
        "data": {
            "id": "QA-CHALLENGE-05",
            "name": "HTML Tag Evolution: Anchor to ARIA Button",
            "category": "locator_drift",
            "difficulty": "MEDIUM",
            "description": "Navigation link <a href='#'> converted into accessible <button role='button'>.",
            "failure_vector": {
                "type": "TAG_MUTATION",
                "broken_locator": "a.nav-export",
                "error_log": "ElementNotInteractableException: Element <a class='nav-export'> is no longer attached or interactive",
                "dom_snapshot": "<button role='button' class='btn-export' aria-label='Export Report' data-action='export'>Export Report</button>"
            },
            "expected_resolution": {
                "healed_locator": "button[aria-label='Export Report']",
                "fallback_locator": "button:has-text('Export Report')",
                "strategy": "AOM_ROLE_MAPPING"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 300,
                "min_confidence_score": 0.88
            }
        }
    },

    # --- DOMAIN 2: API CONTRACT & BREAKING CHANGES ---
    {
        "category_dir": "api_contract_drift",
        "data": {
            "id": "QA-CHALLENGE-06",
            "name": "Numeric ID Serialized as String (Type Mutation)",
            "category": "api_contract_drift",
            "difficulty": "MEDIUM",
            "description": "Backend response changed 'invoice_id: 10423' (int) to 'invoice_id: \"10423\"' (string).",
            "failure_vector": {
                "type": "TYPE_MUTATION",
                "broken_assertion": "assert response.data.invoice_id == 10423",
                "error_log": "AssertionError: Expected integer 10423 but received string '10423'",
                "api_payload": "{\"status\": \"SUCCESS\", \"invoice_id\": \"10423\", \"amount\": 250.0}"
            },
            "expected_resolution": {
                "healed_assertion": "assert str(response.data.invoice_id) == '10423'",
                "strategy": "TYPE_COERCION_ASSERTION"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 280,
                "min_confidence_score": 0.90
            }
        }
    },
    {
        "category_dir": "api_contract_drift",
        "data": {
            "id": "QA-CHALLENGE-07",
            "name": "Payload Response Field Rename",
            "category": "api_contract_drift",
            "difficulty": "EASY",
            "description": "User profile endpoint renamed 'user_email' to 'email_address'.",
            "failure_vector": {
                "type": "FIELD_RENAME",
                "broken_assertion": "assert response.json()['user_email'] == 'qa@example.com'",
                "error_log": "KeyError: 'user_email' not found in response dictionary",
                "api_payload": "{\"id\": 42, \"email_address\": \"qa@example.com\", \"role\": \"QA\"}"
            },
            "expected_resolution": {
                "healed_assertion": "assert (response.json().get('email_address') or response.json().get('user_email')) == 'qa@example.com'",
                "strategy": "RESILIENT_FIELD_LOOKUP"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 260,
                "min_confidence_score": 0.95
            }
        }
    },
    {
        "category_dir": "api_contract_drift",
        "data": {
            "id": "QA-CHALLENGE-08",
            "name": "Nested Response Object Flattened",
            "category": "api_contract_drift",
            "difficulty": "MEDIUM",
            "description": "Backend flattened nested profile: 'data.profile.tier' changed to 'data.tier'.",
            "failure_vector": {
                "type": "STRUCTURE_FLATTEN",
                "broken_assertion": "assert response.json()['profile']['tier'] == 'GOLD'",
                "error_log": "TypeError: 'NoneType' or KeyError: 'profile'",
                "api_payload": "{\"tier\": \"GOLD\", \"points\": 1200}"
            },
            "expected_resolution": {
                "healed_assertion": "tier = response.json().get('tier') or response.json().get('profile', {}).get('tier'); assert tier == 'GOLD'",
                "strategy": "SCHEMA_PATH_FALLBACK"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 320,
                "min_confidence_score": 0.90
            }
        }
    },
    {
        "category_dir": "api_contract_drift",
        "data": {
            "id": "QA-CHALLENGE-09",
            "name": "HTTP Creation Status Code Shift (200 OK -> 201 Created)",
            "category": "api_contract_drift",
            "difficulty": "EASY",
            "description": "POST endpoint updated to RFC-compliant 201 Created instead of legacy 200 OK.",
            "failure_vector": {
                "type": "STATUS_CODE_SHIFT",
                "broken_assertion": "assert response.status_code == 200",
                "error_log": "AssertionError: Expected status code 200 but received 201",
                "api_payload": "{\"status\": 201, \"created\": true}"
            },
            "expected_resolution": {
                "healed_assertion": "assert response.status_code in (200, 201)",
                "strategy": "SUCCESS_STATUS_RANGE"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.0,
                "max_token_cost": 220,
                "min_confidence_score": 0.98
            }
        }
    },
    {
        "category_dir": "api_contract_drift",
        "data": {
            "id": "QA-CHALLENGE-10",
            "name": "Authentication Header Prefix Upgrade",
            "category": "api_contract_drift",
            "difficulty": "EASY",
            "description": "API gateway changed auth format from 'Authorization: Token <token>' to 'Bearer <token>'.",
            "failure_vector": {
                "type": "AUTH_HEADER_DRIFT",
                "broken_code": "headers = {'Authorization': f'Token {auth_token}'}",
                "error_log": "HTTP 401 Unauthorized: Invalid authorization scheme. Expected 'Bearer'.",
                "api_payload": "{\"error\": \"Unauthorized\", \"code\": 401}"
            },
            "expected_resolution": {
                "healed_code": "headers = {'Authorization': f'Bearer {auth_token}'}",
                "strategy": "STANDARD_BEARER_TOKEN"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 250,
                "min_confidence_score": 0.95
            }
        }
    },

    # --- DOMAIN 3: TIMING, ASYNCHRONY & RACE CONDITIONS ---
    {
        "category_dir": "timing_and_race",
        "data": {
            "id": "QA-CHALLENGE-11",
            "name": "Network Latency Spike (3,500ms Throttle) Breaking Static Sleep",
            "category": "timing_and_race",
            "difficulty": "MEDIUM",
            "description": "Microservice latency under load takes 3.5s; test had Thread.sleep(2000).",
            "failure_vector": {
                "type": "STATIC_SLEEP_TIMEOUT",
                "broken_code": "Thread.sleep(2000); assert WebUI.verifyElementPresent('#result')",
                "error_log": "ElementNotFoundException: Element '#result' not present after 2000ms delay",
                "environment_condition": "CDP Network Throttling 3500ms delay"
            },
            "expected_resolution": {
                "healed_code": "page.waitForSelector('#result', timeout: 10000); page.waitForLoadState('networkidle')",
                "strategy": "DYNAMIC_SMART_WAIT"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.5,
                "max_token_cost": 320,
                "min_confidence_score": 0.92
            }
        }
    },
    {
        "category_dir": "timing_and_race",
        "data": {
            "id": "QA-CHALLENGE-12",
            "name": "PrimeNG Modal Backdrop Fading Intercept",
            "category": "timing_and_race",
            "difficulty": "HARD",
            "description": "Modal backdrop takes 450ms CSS transition to fade out; click immediately triggers intercept.",
            "failure_vector": {
                "type": "CLICK_INTERCEPTED",
                "broken_code": "page.click('#confirm-btn')",
                "error_log": "ElementClickInterceptedException: <div class='p-component-overlay p-component-overlay-enter'> intercepts pointer-events",
                "environment_condition": "PrimeNG Modal Fade Transition"
            },
            "expected_resolution": {
                "healed_code": "page.waitForSelector('.p-component-overlay', state: 'detached'); BasePage.clickJS('#confirm-btn')",
                "strategy": "OVERLAY_SAFE_DISPATCH"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 3.0,
                "max_token_cost": 380,
                "min_confidence_score": 0.90
            }
        }
    },
    {
        "category_dir": "timing_and_race",
        "data": {
            "id": "QA-CHALLENGE-13",
            "name": "Debounced Search Input Autocomplete Race",
            "category": "timing_and_race",
            "difficulty": "MEDIUM",
            "description": "Search input debounces 400ms before sending query; test clicked dropdown item before query fired.",
            "failure_vector": {
                "type": "DEBOUNCE_RACE",
                "broken_code": "page.fill('#search-input', 'Invoice'); page.click('.dropdown-item:first-child')",
                "error_log": "TimeoutException: Timed out waiting for '.dropdown-item' to appear in DOM",
                "environment_condition": "Debounce Timer 400ms"
            },
            "expected_resolution": {
                "healed_code": "page.fill('#search-input', 'Invoice'); page.waitForResponse(r => r.url().includes('/search') && r.status() == 200); page.click('.dropdown-item:first-child')",
                "strategy": "CDP_RESPONSE_BARRIER"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.5,
                "max_token_cost": 350,
                "min_confidence_score": 0.88
            }
        }
    },
    {
        "category_dir": "timing_and_race",
        "data": {
            "id": "QA-CHALLENGE-14",
            "name": "Async Chart SVG Animation Race Condition",
            "category": "timing_and_race",
            "difficulty": "MEDIUM",
            "description": "Financial chart takes 1200ms to calculate series and render SVG paths.",
            "failure_vector": {
                "type": "ASYNC_RENDER_RACE",
                "broken_code": "page.click('.chart-bar:last-child')",
                "error_log": "ElementNotFoundException: Selector '.chart-bar:last-child' not found",
                "environment_condition": "Highcharts Rendering Animation"
            },
            "expected_resolution": {
                "healed_code": "page.waitForSelector('.highcharts-series path', state: 'visible'); page.click('.chart-bar:last-child')",
                "strategy": "SVG_VISIBILITY_SMART_WAIT"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 310,
                "min_confidence_score": 0.90
            }
        }
    },
    {
        "category_dir": "timing_and_race",
        "data": {
            "id": "QA-CHALLENGE-15",
            "name": "Infinite Scroll Lazy Loaded Chunk Detach",
            "category": "timing_and_race",
            "difficulty": "MEDIUM",
            "description": "Table rows 50-100 require viewport scroll to trigger network chunk download.",
            "failure_vector": {
                "type": "LAZY_LOAD_RACE",
                "broken_code": "page.locator('tr[data-id=\"75\"]').click()",
                "error_log": "TimeoutException: Timed out waiting for 'tr[data-id=\"75\"]' to be visible",
                "environment_condition": "Virtual Scrolling Table"
            },
            "expected_resolution": {
                "healed_code": "page.locator('tr[data-id=\"75\"]').scrollIntoViewIfNeeded(); page.locator('tr[data-id=\"75\"]').click()",
                "strategy": "VIRTUAL_SCROLL_INTO_VIEW"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 300,
                "min_confidence_score": 0.92
            }
        }
    },

    # --- DOMAIN 4: STALE REFERENCES & DOM RE-RENDERS ---
    {
        "category_dir": "stale_and_mutation",
        "data": {
            "id": "QA-CHALLENGE-16",
            "name": "WebSocket Table Auto-Refresh Stale Reference",
            "category": "stale_and_mutation",
            "difficulty": "HARD",
            "description": "WebSocket pushes live quotes every 1.5s, wiping and recreating <tr> elements.",
            "failure_vector": {
                "type": "STALE_ELEMENT",
                "broken_code": "def row = page.locator('#stocks tr').first(); page.waitForTimeout(1600); row.click();",
                "error_log": "StaleElementReferenceException: Element is no longer attached to DOM",
                "environment_condition": "WebSocket DOM Mutation"
            },
            "expected_resolution": {
                "healed_code": "page.locator('#stocks tr').first().click(); // Re-queries locator at moment of dispatch",
                "strategy": "DYNAMIC_LOCATOR_REQUERY"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.5,
                "max_token_cost": 340,
                "min_confidence_score": 0.90
            }
        }
    },
    {
        "category_dir": "stale_and_mutation",
        "data": {
            "id": "QA-CHALLENGE-17",
            "name": "Tab Switch Component Unmount Detach",
            "category": "stale_and_mutation",
            "difficulty": "MEDIUM",
            "description": "Switching active tabs unmounts previous panel component entirely from virtual DOM.",
            "failure_vector": {
                "type": "COMPONENT_UNMOUNT",
                "broken_code": "page.click('#tab-billing'); page.fill('#billing-tax-id', 'TAX-999');",
                "error_log": "ElementNotInteractableException: Target element '#billing-tax-id' is hidden or unmounted",
                "environment_condition": "Tab Component View Switching"
            },
            "expected_resolution": {
                "healed_code": "page.click('#tab-billing'); page.waitForSelector('#billing-tab-content[aria-hidden=\"false\"]'); page.fill('#billing-tax-id', 'TAX-999');",
                "strategy": "TAB_MOUNT_SYNCHRONIZATION"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 300,
                "min_confidence_score": 0.91
            }
        }
    },
    {
        "category_dir": "stale_and_mutation",
        "data": {
            "id": "QA-CHALLENGE-18",
            "name": "Pagination Replaces tbody (Stale Row Index)",
            "category": "stale_and_mutation",
            "difficulty": "MEDIUM",
            "description": "Navigating to page 2 updates table rows; old row references become detached.",
            "failure_vector": {
                "type": "PAGINATION_DETACH",
                "broken_code": "page.click('.p-paginator-next'); page.locator('tbody tr').nth(0).click();",
                "error_log": "StaleElementReferenceException: Stale element handle during click dispatch",
                "environment_condition": "Data Table Pagination"
            },
            "expected_resolution": {
                "healed_code": "page.click('.p-paginator-next'); page.waitForResponse(r => r.url().includes('page=2')); page.locator('tbody tr').first().click();",
                "strategy": "PAGINATION_NETWORK_SYNC"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 310,
                "min_confidence_score": 0.92
            }
        }
    },
    {
        "category_dir": "stale_and_mutation",
        "data": {
            "id": "QA-CHALLENGE-19",
            "name": "Reopened Modal Generates Fresh DOM Node",
            "category": "stale_and_mutation",
            "difficulty": "MEDIUM",
            "description": "Closing and reopening dialog instantiates new DOM element with same CSS selector.",
            "failure_vector": {
                "type": "FRESH_INSTANCE_STALE",
                "broken_code": "def modal = page.locator('#edit-dialog'); page.click('#close-btn'); page.click('#open-btn'); modal.fill('input', 'new');",
                "error_log": "ElementNotVisibleException: Cached element reference points to detached/hidden dialog instance",
                "environment_condition": "Modal Lifecycle Instantiation"
            },
            "expected_resolution": {
                "healed_code": "page.click('#close-btn'); page.click('#open-btn'); page.locator('#edit-dialog:visible input').fill('new');",
                "strategy": "VISIBLE_SELECTOR_REBIND"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 2.0,
                "max_token_cost": 290,
                "min_confidence_score": 0.94
            }
        }
    },
    {
        "category_dir": "stale_and_mutation",
        "data": {
            "id": "QA-CHALLENGE-20",
            "name": "Locale Swap Invalidates Hardcoded Text Selectors",
            "category": "stale_and_mutation",
            "difficulty": "EASY",
            "description": "Application language changed to French ('Enregistrer'); text selector 'Save' fails.",
            "failure_vector": {
                "type": "I18N_TEXT_MUTATION",
                "broken_locator": "button:has-text('Save')",
                "error_log": "TimeoutException: No element found matching text 'Save'",
                "dom_snapshot": "<button type='submit' data-action='save' class='btn-primary' aria-label='save-record'>Enregistrer</button>"
            },
            "expected_resolution": {
                "healed_locator": "button[data-action='save']",
                "fallback_locator": "button[aria-label='save-record']",
                "strategy": "LOCALE_AGNOSTIC_DATA_ATTRIBUTES"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 270,
                "min_confidence_score": 0.95
            }
        }
    },

    # --- DOMAIN 5: FAKE-PASS, MUTATION TRAPS & TAUTOLOGIES ---
    {
        "category_dir": "fake_pass_tautology",
        "data": {
            "id": "QA-CHALLENGE-21",
            "name": "Swallowed HTTP 500 Error in Empty Catch Block",
            "category": "fake_pass_tautology",
            "difficulty": "EASY",
            "description": "Test silently catches runtime exceptions in an empty catch, masking severe backend 500 crash.",
            "failure_vector": {
                "type": "SWALLOWED_EXCEPTION",
                "code_snippet": "try { page.click('#submit-payment') } catch (Exception e) {} // Test passes even on 500",
                "detection_rule": "EMPTY_CATCH_PATTERN"
            },
            "expected_resolution": {
                "healed_code": "page.click('#submit-payment'); assert page.locator('.success-toast').isVisible();",
                "strategy": "REMOVE_SWALLOWED_CATCH_AND_ASSERT"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.0,
                "max_token_cost": 200,
                "min_confidence_score": 0.99
            }
        }
    },
    {
        "category_dir": "fake_pass_tautology",
        "data": {
            "id": "QA-CHALLENGE-22",
            "name": "Zero-Assertion Smoke Test (Tautological Pass)",
            "category": "fake_pass_tautology",
            "difficulty": "EASY",
            "description": "Test executes form inputs and clicks submit but contains exactly 0 assertion statements.",
            "failure_vector": {
                "type": "ZERO_ASSERTION_PASS",
                "code_snippet": "page.fill('#username', 'admin'); page.fill('#password', 'secret'); page.click('#login-btn');",
                "detection_rule": "FAKE_PASS_NO_ASSERTION"
            },
            "expected_resolution": {
                "healed_code": "page.fill('#username', 'admin'); page.fill('#password', 'secret'); page.click('#login-btn'); expect(page.locator('#dashboard-header')).toBeVisible();",
                "strategy": "INJECT_POST_CONDITION_ASSERTION"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 240,
                "min_confidence_score": 0.97
            }
        }
    },
    {
        "category_dir": "fake_pass_tautology",
        "data": {
            "id": "QA-CHALLENGE-23",
            "name": "Tautological assert true == true",
            "category": "fake_pass_tautology",
            "difficulty": "EASY",
            "description": "Test asserts trivial identity 'assert true == true' instead of verifying business state.",
            "failure_vector": {
                "type": "TAUTOLOGY_ASSERTION",
                "code_snippet": "def response = api.createInvoice(); assert true == true;",
                "detection_rule": "TAUTOLOGY_PATTERN"
            },
            "expected_resolution": {
                "healed_code": "def response = api.createInvoice(); assert response.status == 201 && response.id != null;",
                "strategy": "MUTATION_TESTING_KILLS_TAUTOLOGY"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.0,
                "max_token_cost": 220,
                "min_confidence_score": 0.98
            }
        }
    },
    {
        "category_dir": "fake_pass_tautology",
        "data": {
            "id": "QA-CHALLENGE-24",
            "name": "Unawaited Async Assertion (Silent Green Trap)",
            "category": "fake_pass_tautology",
            "difficulty": "MEDIUM",
            "description": "Missing 'await' on expect(locator).toBeVisible(); Promise resolves ignored after test exit.",
            "failure_vector": {
                "type": "UNAWAITED_ASYNC_ASSERTION",
                "code_snippet": "page.click('#save'); expect(page.locator('.alert')).toBeVisible(); // Missing await!",
                "detection_rule": "UNAWAITED_ASYNC_EXPECT"
            },
            "expected_resolution": {
                "healed_code": "page.click('#save'); await expect(page.locator('.alert')).toBeVisible();",
                "strategy": "AST_ASYNC_AWAIT_ENFORCEMENT"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.5,
                "max_token_cost": 250,
                "min_confidence_score": 0.96
            }
        }
    },
    {
        "category_dir": "fake_pass_tautology",
        "data": {
            "id": "QA-CHALLENGE-25",
            "name": "Unbounded Relational Assertion (status >= 200)",
            "category": "fake_pass_tautology",
            "difficulty": "EASY",
            "description": "Assertion checks 'status >= 200' without ceiling, so HTTP 500 error causes false pass.",
            "failure_vector": {
                "type": "UNBOUNDED_STATUS_ASSERTION",
                "code_snippet": "def resp = client.send(); assert resp.statusCode >= 200; // Passes on 500!",
                "detection_rule": "MUTATION_BOUNDARY_SHIFT"
            },
            "expected_resolution": {
                "healed_code": "def resp = client.send(); assert resp.statusCode >= 200 && resp.statusCode < 300;",
                "strategy": "BOUNDED_INTERVAL_ASSERTION"
            },
            "benchmark_targets": {
                "max_heal_time_sec": 1.2,
                "max_token_cost": 230,
                "min_confidence_score": 0.98
            }
        }
    }
]


def build():
    total_written = 0
    for item in CHALLENGES:
        folder = os.path.join(DATASET_DIR, item["category_dir"])
        os.makedirs(folder, exist_ok=True)
        filename = f"{item['data']['id'].lower()}_{item['data']['category']}.json"
        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(item["data"], f, indent=2)
        total_written += 1

    print(f"✅ Generated {total_written} QA Benchmark Challenges in {DATASET_DIR}")


if __name__ == "__main__":
    build()
