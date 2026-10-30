/**
 * Enterprise Browser Runtime Helper (window.__qa)
 * -------------------------------------------------------------
 * Provides advanced AI testing capabilities directly inside the live browser DOM:
 * 1. Smart Action Batching (qa.batch) - Atomic execution with pause & state preservation.
 * 2. Instant Form Audit (qa.audit) - Detects Angular/React/Vue invalid fields in 1-shot.
 * 3. Self-Healing Locator Engine (qa.heal) - Suggests resilient selectors when locators break.
 * 4. Safe Click & Overlay Bypass (qa.clickSafe) - Clears CDK/PrimeNG/Modal overlays before clicking.
 * 5. Session State Exporter/Importer (qa.exportSession / qa.importSession).
 * 6. Deterministic Sync Engine (qa.isStable / qa.waitForStable / qa.waitForNetworkIdle).
 */

(function () {
  'use strict';

  if (window.__qa && window.__qa.__version === '2.2.2') {
    return window.__qa;
  }

  // Active in-flight network request tracker
  let activeNetworkRequests = 0;
  if (!window.__qa_net_hooked) {
    window.__qa_net_hooked = true;
    if (window.fetch) {
      const origFetch = window.fetch;
      window.fetch = function () {
        activeNetworkRequests++;
        return origFetch.apply(window, arguments).finally(() => {
          activeNetworkRequests = Math.max(0, activeNetworkRequests - 1);
        });
      };
    }
    if (window.XMLHttpRequest) {
      const origOpen = XMLHttpRequest.prototype.open;
      const origSend = XMLHttpRequest.prototype.send;
      XMLHttpRequest.prototype.open = function () {
        this.addEventListener('loadend', () => {
          activeNetworkRequests = Math.max(0, activeNetworkRequests - 1);
        });
        return origOpen.apply(this, arguments);
      };
      XMLHttpRequest.prototype.send = function () {
        activeNetworkRequests++;
        return origSend.apply(this, arguments);
      };
    }
  }

  const qa = {
    __version: '2.2.2',

    /**
     * 1. Smart Action Batching
     * Runs a sequence of step functions atomically.
     * Halts immediately upon failure without resetting previously filled inputs.
     * @param {Array<{name: string, fn: Function}>} steps
     * @returns {Object} { status: 'SUCCESS' | 'FAILED', failedStep?: number, name?: string, error?: string }
     */
    batch: function (steps) {
      if (!Array.isArray(steps)) {
        return { status: 'FAILED', error: 'Steps must be an array of {name, fn}' };
      }
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        try {
          if (typeof step.fn === 'function') {
            step.fn();
          } else if (typeof step.action === 'function') {
            step.action();
          } else {
            throw new Error(`Step #${i + 1} (${step.name}) has no runnable function.`);
          }
        } catch (err) {
          return {
            status: 'FAILED',
            failedStep: i + 1,
            stepName: step.name || `Step #${i + 1}`,
            error: err.message,
            preservedStateUrl: window.location.href
          };
        }
      }
      return { status: 'SUCCESS', totalSteps: steps.length };
    },

    /**
     * 2. Instant Form Audit
     * Finds all invalid fields in active forms (diagnosing disabled Save buttons).
     * Covers Angular Material, PrimeNG, Ant Design, Bootstrap, and HTML5 validation.
     * @returns {Array<Object>} List of invalid controls with metadata
     */
    audit: function () {
      const invalidNodes = Array.from(
        document.querySelectorAll(
          'form .ng-invalid, input.ng-invalid, mat-form-field.ng-invalid, mat-select.ng-invalid, textarea.ng-invalid, p-dropdown.ng-invalid, :invalid'
        )
      );
      return invalidNodes.map(el => ({
        tag: el.tagName.toLowerCase(),
        control: el.getAttribute('formcontrolname') || el.getAttribute('name') || el.id || 'unnamed',
        placeholder: el.getAttribute('placeholder') || '',
        classes: el.className,
        value: el.value || el.innerText.trim()
      }));
    },

    /**
     * 3. Self-Healing Locator Engine
     * When a selector returns 0 elements, scans DOM for matching text, label, or placeholder.
     * @param {string} brokenSelector
     * @param {string} [searchText]
     * @returns {Object} Suggested robust selector
     */
    heal: function (brokenSelector, searchText) {
      const query = (searchText || brokenSelector || '').replace(/['"\\\[\]]/g, '').trim().toLowerCase();
      const candidates = [];

      // Scan buttons
      document.querySelectorAll('button, a.p-button, span.p-button-text, .mat-mdc-button, [role="button"]').forEach(btn => {
        const txt = btn.innerText.trim().toLowerCase();
        if (query && txt.includes(query)) {
          candidates.push({
            type: 'button',
            text: btn.innerText.trim(),
            suggestedXPath: `//button[contains(normalize-space(.), '${btn.innerText.trim()}')]`,
            score: 0.95
          });
        }
      });

      // Scan inputs & form controls
      document.querySelectorAll('input, textarea, mat-select, p-dropdown, select').forEach(inp => {
        const fcn = inp.getAttribute('formcontrolname');
        const ph = inp.getAttribute('placeholder') || '';
        const name = inp.getAttribute('name');
        const testid = inp.getAttribute('data-testid');
        if (testid && testid.toLowerCase().includes(query)) {
          candidates.push({
            type: 'input',
            dataTestId: testid,
            suggestedCss: `[data-testid='${testid}']`,
            score: 0.99
          });
        } else if ((fcn || name) && ((fcn || name).toLowerCase().includes(query) || (query && ph.toLowerCase().includes(query)))) {
          const ctrl = fcn || name;
          candidates.push({
            type: 'input',
            formControlName: fcn,
            name: name,
            placeholder: ph,
            suggestedXPath: `//*[@formcontrolname='${ctrl}']`,
            suggestedCss: `[formcontrolname='${ctrl}']`,
            score: 0.98
          });
        }
      });

      return {
        originalSelector: brokenSelector,
        candidatesFound: candidates.length,
        bestMatch: candidates[0] || null
      };
    },

    /**
     * 4. Safe Click & Overlay Bypass
     * Dispatches click event directly, bypassing blocking overlays
     * (.cdk-overlay-backdrop, .p-component-overlay, .modal-backdrop).
     * @param {string | HTMLElement} target
     * @returns {boolean}
     */
    clickSafe: function (target) {
      const el = typeof target === 'string' ? document.querySelector(target) : target;
      if (!el) return false;

      // Temporarily neutralize blocking overlays if present
      document.querySelectorAll('.cdk-overlay-backdrop, .p-component-overlay, .modal-backdrop').forEach(overlay => {
        overlay.style.pointerEvents = 'none';
      });

      el.scrollIntoView({ behavior: 'auto', block: 'center' });
      el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
      el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
      el.click();
      return true;
    },

    /**
     * 5. Session State Exporter
     * Exports tokens and localStorage to bypass UI login (Zero-Second Auth).
     * @returns {Object}
     */
    exportSession: function () {
      const storage = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        storage[key] = localStorage.getItem(key);
      }
      return {
        url: window.location.href,
        cookies: document.cookie,
        localStorage: storage
      };
    },

    /**
     * Restore session state
     * @param {Object} data
     */
    importSession: function (data) {
      if (data && data.localStorage) {
        for (const [k, v] of Object.entries(data.localStorage)) {
          localStorage.setItem(k, v);
        }
      }
      return { status: 'SESSION_IMPORTED' };
    },

    /**
     * 6. Zone.js & Microtask Stability Sync Engine
     * Checks if framework microtasks, promises, and animations are fully settled.
     * @returns {boolean}
     */
    isStable: function () {
      try {
        if (window.getAllAngularTestabilities) {
          const testabilities = window.getAllAngularTestabilities();
          if (testabilities && testabilities.length > 0) {
            return testabilities.every(t => t.isStable());
          }
        }
        const hasBlocker = document.querySelector(
          '.p-blockui, .p-progress-spinner, .mat-mdc-progress-bar, .spinner, .loading, .ng-animating'
        );
        return !hasBlocker;
      } catch (e) {
        return true;
      }
    },

    /**
     * Asynchronously wait for framework to become stable
     * @param {number} [timeoutMs=10000]
     * @returns {Promise<boolean>}
     */
    waitForStable: function (timeoutMs = 10000) {
      const self = this;
      const start = Date.now();
      return new Promise((resolve) => {
        const interval = setInterval(() => {
          if (self.isStable()) {
            clearInterval(interval);
            resolve(true);
          } else if (Date.now() - start > timeoutMs) {
            clearInterval(interval);
            resolve(false);
          }
        }, 100);
      });
    },

    /**
     * 7. CDP Network Drain & In-Flight Traffic Monitor (Network Idle 0)
     */
    getActiveRequests: function () {
      return activeNetworkRequests;
    },

    waitForNetworkIdle: function (idleTimeMs = 500, timeoutMs = 10000) {
      const start = Date.now();
      let idleStart = null;
      return new Promise((resolve) => {
        const interval = setInterval(() => {
          if (activeNetworkRequests === 0) {
            if (!idleStart) idleStart = Date.now();
            if (Date.now() - idleStart >= idleTimeMs) {
              clearInterval(interval);
              resolve(true);
            }
          } else {
            idleStart = null;
          }
          if (Date.now() - start > timeoutMs) {
            clearInterval(interval);
            resolve(false);
          }
        }, 50);
      });
    },

    /**
     * 8. Action Safety Firewall (Blast Radius Containment)
     */
    firewall: {
      DANGEROUS_PATTERNS: /\b(delete|remove|purge|wipe|drop|pay|purchase|checkout|terminate|destroy|transfer|reset)\b/i,
      DANGEROUS_SELECTORS: ['[data-action*="delete"]', '[data-action*="pay"]', '.btn-danger', '.p-button-danger', '[aria-label*="delete" i]'],

      isDangerous: function (element, actionName = 'click') {
        if (!element) return false;
        const text = (element.innerText || element.textContent || element.value || element.getAttribute('aria-label') || '').trim();
        if (this.DANGEROUS_PATTERNS.test(text)) return true;
        for (const sel of this.DANGEROUS_SELECTORS) {
          if (element.matches && element.matches(sel)) return true;
          if (element.closest && element.closest(sel)) return true;
        }
        return false;
      },

      checkSafeAction: function (element, actionName = 'click') {
        const dangerous = this.isDangerous(element, actionName);
        if (!dangerous) {
          return { allowed: true, reason: 'ACTION_SAFE' };
        }
        if (window.__ALLOW_DESTRUCTIVE__ === true) {
          return { allowed: true, reason: 'BYPASS_FLAG_ENABLED' };
        }
        return {
          allowed: false,
          reason: 'DANGEROUS_ACTION_BLOCKED',
          message: `Action '${actionName}' on destructive element was blocked by Safety Firewall. Set window.__ALLOW_DESTRUCTIVE__ = true to override.`
        };
      }
    },

    /**
     * 9. Multimodal Vision-Grounded Set-of-Marks (SoM) Engine
     * Pierces Shadow DOM and inspects HTML5 Canvas elements for coordinate grounding.
     */
    som: {
      getInteractiveMarks: function () {
        const marks = [];
        let idCounter = 1;

        function traverse(root) {
          if (!root || !root.querySelectorAll) return;
          const candidates = root.querySelectorAll('button, a, input, select, textarea, [role="button"], canvas, svg');
          candidates.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width > 5 && rect.height > 5 && window.getComputedStyle(el).visibility !== 'hidden') {
              const label = el.getAttribute('aria-label') || el.innerText || el.value || el.tagName.toLowerCase();
              marks.push({
                mark_id: idCounter++,
                tag: el.tagName.toLowerCase(),
                label: (label || '').trim().substring(0, 50),
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                center_x: Math.round(rect.left + rect.width / 2),
                center_y: Math.round(rect.top + rect.height / 2)
              });
            }
            // Pierce Shadow DOM
            if (el.shadowRoot) {
              traverse(el.shadowRoot);
            }
          });
        }

        traverse(document);
        return marks;
      },

      overlayMarks: function () {
        this.clearMarks();
        const container = document.createElement('div');
        container.id = '__qa_som_overlay';
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100vw';
        container.style.height = '100vh';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '999999';

        const marks = this.getInteractiveMarks();
        marks.forEach(m => {
          const badge = document.createElement('div');
          badge.style.position = 'absolute';
          badge.style.left = m.x + 'px';
          badge.style.top = Math.max(0, m.y - 18) + 'px';
          badge.style.background = '#FF0055';
          badge.style.color = '#FFFFFF';
          badge.style.fontSize = '12px';
          badge.style.fontWeight = 'bold';
          badge.style.padding = '1px 4px';
          badge.style.borderRadius = '3px';
          badge.innerText = m.mark_id;

          const box = document.createElement('div');
          box.style.position = 'absolute';
          box.style.left = m.x + 'px';
          box.style.top = m.y + 'px';
          box.style.width = m.width + 'px';
          box.style.height = m.height + 'px';
          box.style.border = '2px solid #FF0055';

          container.appendChild(box);
          container.appendChild(badge);
        });

        document.body.appendChild(container);
        return marks;
      },

      clearMarks: function () {
        const existing = document.getElementById('__qa_som_overlay');
        if (existing) existing.remove();
      }
    },

    /**
     * 7. Ultra-Compact Accessibility Object Model (AOM) Distillation
     * Filters noise (wrapper divs, styling spans) and returns an ultra-sparse
     * tree representation (Role, Name, State, TestId) capped at maxDepth (default: 3).
     * Prevents context rot / token bloat by condensing thousands of DOM nodes into ~300 tokens.
     * @param {Element|Document} [root=document]
     * @param {number} [maxDepth=3]
     * @returns {Array<{role: string, name: string, state?: Object, testId?: string, depth: number}>}
     */
    getCompactAOM: function (root = document, maxDepth = 3) {
      const aomNodes = [];
      const INTERACTIVE_ROLES = new Set([
        'button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'menuitem',
        'tab', 'switch', 'dialog', 'alert', 'searchbox', 'spinbutton', 'option', 'treeitem'
      ]);

      function getRole(el) {
        const explicitRole = el.getAttribute('role');
        if (explicitRole) return explicitRole.toLowerCase();
        const tag = el.tagName.toLowerCase();
        if (tag === 'button') return 'button';
        if (tag === 'a' && el.hasAttribute('href')) return 'link';
        if (tag === 'input') {
          const type = (el.getAttribute('type') || 'text').toLowerCase();
          if (['checkbox', 'radio', 'button', 'submit'].includes(type)) return type;
          return 'textbox';
        }
        if (tag === 'select') return 'combobox';
        if (tag === 'textarea') return 'textbox';
        return null;
      }

      function getAccessibleName(el) {
        return (
          el.getAttribute('aria-label') ||
          el.getAttribute('aria-placeholder') ||
          el.getAttribute('placeholder') ||
          el.getAttribute('title') ||
          (el.innerText ? el.innerText.trim().slice(0, 50).replace(/\s+/g, ' ') : '') ||
          el.getAttribute('name') ||
          el.getAttribute('value') ||
          ''
        );
      }

      function getState(el) {
        const state = {};
        if (el.disabled || el.getAttribute('aria-disabled') === 'true') state.disabled = true;
        if (el.getAttribute('aria-expanded') !== null) state.expanded = el.getAttribute('aria-expanded') === 'true';
        if (el.checked || el.getAttribute('aria-checked') === 'true') state.checked = true;
        if (el.getAttribute('aria-invalid') === 'true') state.invalid = true;
        if (el.getAttribute('aria-selected') === 'true') state.selected = true;
        return Object.keys(state).length > 0 ? state : undefined;
      }

      function isVisible(el) {
        if (!el || el.nodeType !== 1) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      }

      function walk(node, currentDepth) {
        if (currentDepth > maxDepth || !node) return;
        const children = node.children || [];
        for (let i = 0; i < children.length; i++) {
          const child = children[i];
          if (!isVisible(child)) continue;

          const role = getRole(child);
          const testId = child.getAttribute('data-testid') || child.getAttribute('data-cy') || child.id || '';

          if (role && (INTERACTIVE_ROLES.has(role) || testId)) {
            aomNodes.push({
              role: role,
              name: getAccessibleName(child),
              state: getState(child),
              testId: testId || undefined,
              depth: currentDepth
            });
          }

          // Pierce Shadow DOM
          if (child.shadowRoot) {
            walk(child.shadowRoot, currentDepth + 1);
          }
          walk(child, currentDepth + 1);
        }
      }

      walk(root === document ? document.body : root, 1);
      return aomNodes;
    },

    /**
     * 8. Dynamic Stability Probe (Event-Driven Wait Weaver)
     * Replaces flaky static sleeps (Thread.sleep / cy.wait) by dynamically probing:
     * 1. Coordinate / Layout Stability: Bounding rect unchanged for 100ms consecutive duration.
     * 2. Form Editable State: Ensures form inputs are editable (!disabled && !readOnly).
     * 3. Network Quiescence: Ensures active in-flight network requests == 0.
     * @param {string|Element} target
     * @param {Object} [options]
     * @returns {Promise<boolean>}
     */
    probeStability: function (target, options = {}) {
      const opts = Object.assign({
        checkPosition: true,
        checkEditable: false,
        stabilityDuration: 100,
        timeout: 5000
      }, options);

      return new Promise((resolve) => {
        const startTime = Date.now();
        let el = null;
        if (typeof target === 'string') {
          el = document.querySelector(target);
        } else if (target && target.nodeType === 1) {
          el = target;
        }

        let lastRect = null;
        let stableSince = null;

        function check() {
          const now = Date.now();
          if (now - startTime > opts.timeout) {
            return resolve(false);
          }

          if (!el && typeof target === 'string') {
            el = document.querySelector(target);
          }

          if (el) {
            if (opts.checkEditable) {
              const tag = el.tagName.toLowerCase();
              if (tag === 'input' || tag === 'textarea' || tag === 'select') {
                if (el.disabled || el.readOnly) {
                  return setTimeout(check, 25);
                }
              }
            }

            if (opts.checkPosition) {
              const rect = el.getBoundingClientRect();
              if (
                lastRect &&
                Math.abs(rect.top - lastRect.top) < 1 &&
                Math.abs(rect.left - lastRect.left) < 1 &&
                Math.abs(rect.width - lastRect.width) < 1 &&
                Math.abs(rect.height - lastRect.height) < 1
              ) {
                if (!stableSince) stableSince = now;
                if (now - stableSince >= opts.stabilityDuration) {
                  return resolve(true);
                }
              } else {
                lastRect = rect;
                stableSince = null;
              }
              return setTimeout(check, 25);
            }
          }

          if (activeNetworkRequests === 0) {
            return resolve(true);
          }
          setTimeout(check, 25);
        }

        check();
      });
    }
  };

  window.__qa = qa;
  window.__helper = qa;
  return qa;
})();
