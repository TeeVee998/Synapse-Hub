---
name: backend-load-and-stress-patterns
description: "Orchestrate k6 and Locust backend load, stress, and SLA endurance test suites."
---

# Backend Load & Stress Testing Patterns (k6 & Locust Orchestrator)

> **Purpose:** Master backend performance, throughput, and scalability engineering. Directs AI agents to model concurrent Virtual User (VU) traffic, execute stress/soak test profiles, and enforce automated SLA gates (P95/P99 latency, error rate < 0.1%) to detect bottlenecks before production release.

---

## 1. Five Core Performance Test Archetypes

```mermaid
flowchart LR
    A["<b>1. Smoke Test</b><br/>1-5 VUs / 1 min<br/>Sanity check"] --> B["<b>2. Load Test</b><br/>50-200 VUs / 15m<br/>Expected daily peak"]
    B --> C["<b>3. Stress Test</b><br/>500-2000+ VUs<br/>Find breaking point"]
    C --> D["<b>4. Spike Test</b><br/>Instant surge 10->1000<br/>Traffic shocks"]
    D --> E["<b>5. Soak / Endurance</b><br/>Stable load / 2-12 hrs<br/>Memory leaks & OOM"]
```

| Test Archetype | Virtual Users (VUs) | Duration | Primary Objective | Failure Indicator |
| :--- | :--- | :--- | :--- | :--- |
| **Smoke Test** | 1 - 5 VUs | 1 - 2 mins | Script syntax & endpoint health sanity | Any HTTP 5xx or unhandled exceptions |
| **Load Test** | 50 - 200 VUs | 15 - 30 mins | Verify system SLA under standard peak traffic | P95 latency > 500ms or error rate > 0.1% |
| **Stress Test** | 200 -> 2,000+ VUs | 30 - 60 mins | Identify maximum throughput and degradation cliff | DB connection pool exhaustion, 503/504 errors |
| **Spike Test** | 10 -> 1,000 VUs in 10s | 5 - 10 mins | Test autoscaling latency and rate limiters | Gateway timeout (504), service unresponsiveness |
| **Soak Test** | 50 - 100 VUs | 2 - 12 hours | Detect slow memory leaks, disk fill, thread locks | Degraded throughput over time, JVM OOM |

---

## 2. Automated SLA Threshold Assertions

Every performance test execution must assert measurable SLA criteria. If thresholds fail, the CI/CD pipeline returns a non-zero exit code.

```javascript
// Enterprise SLA Gates (k6)
export const options = {
  thresholds: {
    // 95% of requests must complete under 500ms
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    // Request failure rate must stay under 0.1%
    http_req_failed: ['rate<0.001'],
    // Functional checks must maintain > 99.9% success
    checks: ['rate>0.999'],
  },
};
```

---

## 3. Production-Ready k6 Load Script (TypeScript / JavaScript)

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom Enterprise Metrics
const errorRate = new Rate('custom_error_rate');
const searchLatency = new Trend('search_latency');

export const options = {
  scenarios: {
    enterprise_workload: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp-up to 50 users
        { duration: '5m', target: 50 },   // Steady state peak
        { duration: '2m', target: 150 },  // Surge stress load
        { duration: '3m', target: 150 },  // Sustained stress
        { duration: '2m', target: 0 },    // Ramp-down to 0
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<400', 'p(99)<800'],
    custom_error_rate: ['rate<0.005'], // < 0.5% errors under stress
  },
};

const BASE_URL = __ENV.TARGET_URL || 'https://api.staging.enterprise.local';

export function setup() {
  // Pre-test Authentication & Seeding (Executed once)
  const authRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    username: __ENV.PERF_USER || 'perf_agent_01',
    password: __ENV.PERF_PASSWORD || 'SecretVault#2026',
  }), { headers: { 'Content-Type': 'application/json' } });

  check(authRes, { 'Auth 200 OK': (r) => r.status === 200 });
  const token = authRes.json('token');
  return { token };
}

export default function (data) {
  const params = {
    headers: {
      'Authorization': `Bearer ${data.token}`,
      'Content-Type': 'application/json',
      'X-Correlation-ID': `PERF-${__VU}-${__ITER}-${Date.now()}`,
    },
  };

  // 1. Transaction A: Fast Read API
  const resGet = http.get(`${BASE_URL}/api/v1/catalogs?limit=20`, params);
  const getOk = check(resGet, {
    'Catalog GET 200': (r) => r.status === 200,
    'Catalog Payload Valid': (r) => r.json('data.items') !== undefined,
  });
  errorRate.add(!getOk);
  searchLatency.add(resGet.timings.duration);

  sleep(1);

  // 2. Transaction B: Dynamic Mutation API
  const payload = JSON.stringify({
    code: `AUTO_PERF_${__VU}_${__ITER}_${Date.now()}`,
    name: 'Dynamic Synthetic Benchmark Item',
    active: true,
  });

  const resPost = http.post(`${BASE_URL}/api/v1/catalogs`, payload, params);
  const postOk = check(resPost, {
    'Catalog POST 201': (r) => r.status === 201 || r.status === 200,
  });
  errorRate.add(!postOk);

  sleep(2);
}

export function teardown(data) {
  // Clean up benchmark markers if required
}
```

---

## 4. Production-Ready Locust Load Script (Python)

```python
import os
import time
from locust import HttpUser, task, between, events

class EnterpriseBackendUser(HttpUser):
    wait_time = between(1.0, 2.5)  # Realistic user think-time

    def on_start(self):
        """Initial authentication handshake per Virtual User."""
        res = self.client.post("/api/v1/auth/login", json={
            "username": os.getenv("PERF_USER", "perf_tester"),
            "password": os.getenv("PERF_PWD", "SecretPass2026")
        })
        if res.status_code == 200:
            token = res.json().get("token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def query_search_index(self):
        """High-frequency read query."""
        with self.client.get("/api/v1/search?q=enterprise&page=1", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Search API failed with HTTP {response.status_code}")
            elif response.elapsed.total_seconds() > 0.5:
                response.failure(f"Search API SLA breached (>500ms): {response.elapsed.total_seconds():.3f}s")

    @task(1)
    def submit_order_transaction(self):
        """Mutation transaction with dynamic unique identifier."""
        order_id = f"ORDER_PERF_{time.time_ns()}"
        with self.client.post("/api/v1/orders", json={
            "orderCode": order_id,
            "items": [{"sku": "SKU-990", "quantity": 1}],
            "totalAmount": 150000
        }, catch_response=True) as response:
            if response.status_code not in (200, 201):
                response.failure(f"Order submission failed: {response.text}")
```

---

## 5. Execution Runbook & CI/CD Integration

### Run k6 Headless with JSON Summary
```bash
# Execute 100-user load test and export raw metrics
k6 run --out json=reports/k6_metrics.json tests/load/k6_catalog_load.js

# Assert exit code in CI/CD pipeline
if [ $? -ne 0 ]; then
  echo "❌ Performance SLA threshold breached!"
  exit 1
fi
```

### Run Locust Headless in CI/CD
```bash
locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 5m \
       --host https://api.staging.enterprise.local \
       --html reports/locust_report.html \
       --exit-code-on-error 1
```

### Autonomous Apache JMeter Plan Generation & Execution
Hub provides `tools/generate_jmx_plan.py` to auto-generate JMeter 5.x test plans (.jmx) directly from OpenAPI specs or Postman collections:
```bash
# 1. Generate JMeter Test Plan (100 VUs, 10 min, SLA < 500ms)
python tools/generate_jmx_plan.py --spec swagger.json -o perf_plan.jmx --vus 100 --duration 600

# 2. Convert existing Postman collection to JMeter Plan
python tools/generate_jmx_plan.py --postman postman_collection.json -o perf_plan.jmx --vus 50

# 3. Execute headless JMeter in CI/CD pipeline
jmeter -n -t perf_plan.jmx -l results.jtl -e -o ./html_report
```

---

## 6. Performance Engineering Checklist
- [ ] Authentication executed once per VU in `setup()` or `on_start()`, never in tight loops.
- [ ] Synthetic transactions use dynamic unique codes to eliminate DB primary key collisions.
- [ ] SLA thresholds include both latency (P95/P99) and availability (`error_rate < 0.1%`).
- [ ] Soak tests executed against isolated staging environments with active APM/DB monitoring.
- [ ] Teardown removes temporary benchmark data to prevent DB bloat.
