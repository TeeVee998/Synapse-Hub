---
name: backend-load-and-stress-patterns
description: "Orchestrate k6, Locust, and JMeter backend load, stress, and SLA endurance test suites."
---

# Backend Load & Performance Testing Skill

> **Target:** Model concurrent Virtual User (VU) traffic, execute stress/soak test profiles, and enforce automated SLA gates (P95/P99 latency, error rate < 1.0%) to detect bottlenecks before production.

---

## 1. Test Archetypes & SLA Targets

| Archetype | VUs | Duration | Objective | SLA Assertion |
| :--- | :--- | :--- | :--- | :--- |
| **Smoke Test** | 1 - 5 | 1 - 2 min | Health sanity check | Error rate = 0%, P95 < 300ms |
| **Load Test** | 50 - 200 | 10 - 30 min | Standard peak capacity | Error rate < 0.5%, P95 < 500ms |
| **Stress Test** | 200 -> 2,000 | 20 - 45 min | Find degradation cliff | Graceful 429/503 (no JVM OOM) |
| **Spike Test** | 10 -> 1,000 | 5 - 10 min | Autoscaling & rate limiters | Gateway recovery < 30s |
| **Soak Test** | 50 - 100 | 2 - 12 hr | Memory leaks & connection leaks | Stable heap & steady latency |

---

## 2. Tooling Unified Runbook

### Option A: Apache JMeter (Headless CLI + JTL Analyzer)
```bash
# 1. Generate XML test plan from OpenAPI / Postman
python tools/generate_jmx_plan.py --spec api.json -o load_plan.jmx --vus 50 --duration 180 --sla-p95 500

# 2. Run headless benchmark
jmeter -n -t load_plan.jmx -l results.jtl -e -o ./html_report

# 3. Automated CI/CD Quality Gatekeeper
python tools/jtl_analyzer.py results.jtl --sla-p95 500 --max-error-rate 1.0
```

### Option B: k6 Modern Load Testing
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '3m', target: 50 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/api/v1/health`);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

---

## 3. Best Practices & Invariants

- **Isolated Test Data:** Always use dynamic runtime identifiers (`PERF_AUTO_${__time(HMS,)}`) to eliminate primary key collisions.
- **TearDown Hygiene:** Complement POST/creation load tests with automated teardown or ephemeral DB snapshots (`tools/db_sandbox.py`).
- **Telemetry Correlation:** Pair JTL/k6 metrics with server CPU/Memory traces via `tools/telemetry_correlator.py`.
