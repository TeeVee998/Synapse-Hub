---
name: backend-load-and-stress-patterns
description: "Orchestrate k6, Locust, and JMeter backend load, stress, and SLA endurance test suites. Use when designing load, stress, or spike test patterns for backend systems."
---

# Backend Load & Performance Testing Skill

> **Target:** Model concurrent Virtual User (VU) and arrival-rate traffic, execute stress/soak test profiles, and enforce automated SLA gates (P95/P99 latency, error rate < 1.0%) to detect bottlenecks before production.  
> **Mandatory Rule:** Adhere strictly to [.agents/rules/performance_testing_rules.md](file://.agents/rules/performance_testing_rules.md) for safety approvals, hard caps, and truth-anchor reporting.

---

## 1. Test Archetypes & SLA Targets

| Archetype | VUs / Rate | Duration | Objective | SLA Assertion |
| :--- | :--- | :--- | :--- | :--- |
| **Smoke Test** | 1 - 5 VUs | 1 - 2 min | Health sanity check | Error rate = 0%, P95 < 300ms |
| **Average Load** | 50 - 200 VUs | 10 - 30 min | Standard peak capacity | Error rate < 0.5%, P95 < 500ms |
| **Stress Test** | 200 -> 2,000 VUs | 20 - 45 min | Find degradation cliff | Graceful 429/503 (no JVM OOM) |
| **Spike Test** | 10 -> 1,000 VUs | 5 - 10 min | Autoscaling & rate limiters | Gateway recovery < 30s |
| **Soak Test** | 50 - 100 VUs | 2 - 12 hr | Memory leaks & connection leaks | Stable heap & steady latency |

---

## 2. Tooling Unified Runbook

### Option A: Apache JMeter (Headless CLI + JTL Analyzer)
```bash
# 1. Generate XML test plan from OpenAPI / Postman
synapse generate-jmx --spec api.json -o load_plan.jmx --vus 50 --duration 180 --sla-p95 500

# 2. Run headless benchmark
jmeter -n -t load_plan.jmx -l results.jtl -e -o ./html_report

# 3. Automated CI/CD Quality Gatekeeper
synapse analyze-jtl results.jtl --sla-p95 500 --max-error-rate 1.0
```

### Option B: k6 Production Load Testing (with Kill-Switch & Arrival Rate)
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  discardResponseBodies: true,
  scenarios: {
    steady_load: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 200,
      stages: [
        { duration: '2m', target: 50 },  // Ramp-up
        { duration: '10m', target: 50 }, // Steady state (SLA measured here)
        { duration: '2m', target: 0 },   // Ramp-down
      ],
    },
  },
  thresholds: {
    // 1. Steady state SLA thresholds
    'http_req_failed{scenario:steady_load}': ['rate<0.01'],
    'http_req_duration{scenario:steady_load,expected_response:true}': ['p(95)<500', 'p(99)<1000'],
    'checks{scenario:steady_load}': ['rate>0.99'],
    'dropped_iterations{scenario:steady_load}': ['count==0'],
    // 2. Kill-switch: abort test if system fails catastrophically
    http_req_failed: [{ threshold: 'rate<0.10', abortOnFail: true, delayAbortEval: '30s' }],
  },
};

// 1. One-time setup: authenticate and obtain auth token
export function setup() {
  const loginRes = http.post(`${__ENV.BASE_URL}/api/v1/auth/login`, JSON.stringify({
    username: __ENV.PERF_USER,
    password: __ENV.PERF_PASSWORD,
  }), { headers: { 'Content-Type': 'application/json' } });
  
  return { token: loginRes.json('token') };
}

// 2. Virtual User journey
export default function (data) {
  const params = {
    headers: {
      'Authorization': `Bearer ${data.token}`,
      'Content-Type': 'application/json',
    },
    tags: { name: 'GET /api/v1/items' },
  };

  const res = http.get(`${__ENV.BASE_URL}/api/v1/items?page=1&limit=20`, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  // Realistic think time between actions (uniform 1s to 3s)
  sleep(Math.random() * 2 + 1);
}

// 3. Ephemeral teardown cleanup
export function teardown(data) {
  // Execute teardown API calls for created PERF_ entities
}
```

---

## 3. Best Practices & Safety Invariants

- **Isolated Test Data:** Always use dynamic runtime identifiers (`PERF_AUTO_${Date.now()}`) to eliminate primary key collisions.
- **TearDown Hygiene:** Complement POST/creation load tests with automated teardown or ephemeral DB snapshots (`tools/db_sandbox.py`).
- **Telemetry Correlation:** Pair JTL/k6 metrics with server CPU/Memory traces via `tools/telemetry_correlator.py`.
- **Truth Anchor:** Never loosen thresholds to manufacture a false pass. A failing threshold indicates a system capacity limit to be investigated.

---

## 4. Code-as-Code Load Model (Locust)

> *Borrowed and adapted from the Locust load-testing model (MIT license, locustio/locust).*

When version-controlled, reviewable load tests matter more than XML tooling,
generate a runnable locustfile from the same API ingestion used for JMeter:

```bash
synapse generate-jmx --spec swagger.json --emit-locust locustfile.py \
  --weighted-mix "70,20,10" --think-time-min 500 --think-time-max 1500
locust -f locustfile.py --host=https://api.staging.enterprise.local
```

The generated file follows the Locust shape — one `HttpUser` class, one
`@task(weight)` method per endpoint, `wait_time` from think-time — so QA
engineers can hand-tune scenarios in pure Python and commit them next to the
test suite.

1. **Weights are the traffic mix** — the same `--weighted-mix` percentages that
   drive JMeter `ThroughputController`s drive `@task` weights; keep both exports
   in sync from one spec.
2. **Prefer code-as-code for logic-heavy journeys** — conditional flows
   (login → create → assert → delete) are Python, not XML; use the JMX export
   for protocol breadth (JDBC/Kafka/gRPC/WS) and Locust for flow logic.
3. **Same SLA gates** — run `agent-qa analyze-jtl` semantics on Locust stats:
   fail CI when P95 breaches the SLA budget.
