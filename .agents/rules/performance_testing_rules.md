# Performance & Load Testing Invariants (k6 · JMeter · Locust)

> **Scope:** Applies whenever designing, executing, or analyzing performance, load, stress, spike, or soak test workloads.  
> These invariants complement `AGENTS.md` and enforce enterprise safety, workload realism, and zero-hallucination analysis.

---

## 1. Safety Gate & Approval Invariants (Mandatory Pre-Flight)

1. **Explicit Authorization:**
   - Execute load tests **only** against pre-approved, dedicated environments (performance test environment or isolated sandbox).
   - **Strictly forbidden:** Running load tests against production, shared staging, public demo sites, or third-party APIs without formal written sign-off.
2. **Pre-Run Declaration:**
   - Prior to any execution above Smoke test, the agent must declare the run profile and wait for explicit confirmation:
     - Target host and environment owner
     - Test archetype (Smoke, Average Load, Stress, Spike, Soak)
     - Load profile (max VUs, target iterations/sec or requests/sec, duration, ramp-up/down phases)
     - Data volume created and teardown strategy
     - Kill-switch threshold (`abortOnFail`)
3. **Progressive Stepped Escalation:**
   - Always adhere to progressive ramp-up: **Smoke (1–5 VUs) → Baseline Average Load → Stress / Spike / Soak**.
   - Never initiate Stress, Spike, Soak, or Breakpoint runs autonomously.
4. **Hard Caps & Kill-Switch:**
   - Every script must enforce hard upper bounds on rate and VUs, finite duration, and an automatic abort condition (`abortOnFail` when error rate breaches acceptable thresholds, e.g., > 10%).
   - Unbounded loops or infinite duration scripts are strictly prohibited.
5. **Third-Party Isolation:**
   - Mock or stub third-party external dependencies (Payment Gateways, SMS providers, email senders, CAPTCHA, web analytics). Never send synthetic load to unisolated external partners.
6. **Data Safety & Idempotent Cleanup:**
   - Write traffic must use isolated, synthetic test data with recognizable prefixes (e.g., `PERF_AUTO_`, `PERF-`). Real customer credentials or PII must never be used.
   - Every creation run must be paired with an automated teardown or ephemeral DB rollback.

---

## 2. Workload Modeling Invariants

1. **Open vs. Closed Model:**
   - **Open Model (Arrival Rate):** Use arrival-rate executors for public web traffic or SLA requirements stated in rate (e.g., `N req/sec`). Real users arrive independently of system slowdown.
   - **Closed Model (Virtual Users):** Use VU-based executors only when modeling fixed concurrent sessions (e.g., internal enterprise portals).
2. **Realistic Think Time:**
   - Model user think time between journey steps using realistic distributions (e.g., Gaussian or uniform 1s–5s). Zero-think-time "hammer" testing is forbidden unless specifically requested for denial-of-service resilience audits.
3. **Data Realism & Cache Skew Prevention:**
   - Parameterize query parameters, identifiers, and payloads across realistic key spaces. Repeatedly querying identical records measures database cache hit rates rather than true backend capability.
4. **Phase-Based Evaluation:**
   - Structure tests into `Ramp-Up`, `Steady State`, and `Ramp-Down` phases.
   - Compute SLA thresholds and verdicts **strictly against the Steady State**, never against warm-up or cool-down transients.

---

## 3. k6 Script Engineering Standards

1. **Script Structure:**
   - `options` (profile, stages, thresholds) → `setup()` (one-time auth and shared state) → default function (user journey with `check()` calls) → `teardown()` (cleanup).
2. **Valid Threshold Syntax:**
   - Use standard k6 threshold syntax: `metric{tag:value}: ['p(95)<500']`. Braces contain tag filters only.
   - Latency thresholds must evaluate successful responses: `'http_req_duration{expected_response:true}': ['p(95)<500', 'p(99)<1000']`.
   - Always pair `check()` with a `checks` threshold (e.g., `'checks': ['rate>0.99']`), as unasserted check failures do not alter k6 exit codes.
3. **Generator Efficiency:**
   - Set `discardResponseBodies: true` when response bodies are not required for subsequent extractions, minimizing memory overhead on the load generator.
4. **Strict Credential Hygiene:**
   - Pass tokens, usernames, and base URLs via environment variables (`__ENV.BASE_URL`). Never hardcode secrets in test plans or committed repository scripts.

---

## 4. Truth Anchor & Performance Autopsy Protocol

1. **No Lowering Thresholds (Truth Anchor):**
   - If an SLA threshold is breached, report the failure with root causes. **Never loosen thresholds, truncate steady states, or drop samples to manufacture a false pass.**
2. **Structured Analysis Sequence:**
   - Analyze results in strict sequence:
     1. **Run Validity:** Confirm `dropped_iterations == 0` and generator CPU remained < 80%. If the generator was saturated, mark the run INVALID.
     2. **Error Rate:** Categorize HTTP 4xx, 5xx, timeouts, connection resets.
     3. **Latency Percentiles:** Report P50, P90, P95, P99, and Max. Never headline average latency.
     4. **Throughput:** Compare target requests/sec vs. achieved requests/sec.
     5. **Correlation:** Correlate breaches with backend APM traces (database slow queries, GC pauses, connection pool exhaustion) before attributing root causes.
