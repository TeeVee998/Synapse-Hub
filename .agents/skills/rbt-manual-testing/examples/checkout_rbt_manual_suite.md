# Example AI-RBT Manual Test Suite: E-Commerce Checkout

## 1. Risk Assessment Matrix (P x I)

| Feature / Journey | Probability (1-5) | Impact (1-5) | Risk Score (P x I) | Tier | Testing Focus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Payment Gateway Integration (Stripe/PayPal) | 4 | 5 | 20 | Critical (P1) | Idempotency, 3D Secure, Network timeout, Webhook retry |
| Promo Code & Discount Application | 3 | 4 | 12 | High (P2) | Boundary dates, Concurrent usage, Negative cart values |
| Shipping Address Form & Validation | 2 | 3 | 6 | Medium (P3) | XSS, Max length, International postal formats |

## 2. Requirement Clarification & Ambiguity Log

| ID | Ambiguity / Gap | Question to Product Owner | Impact / Default Assumption |
| :--- | :--- | :--- | :--- |
| AMB-01 | Discount expiration timezone not specified | Does promo code expire at 23:59 UTC or local user time? | Assumed UTC midnight to prevent premature expiration errors. |
| AMB-02 | Handling partial payment failure during multi-card checkout | Should the entire order roll back or allow secondary payment? | Assumed atomic rollback: no charge without full authorization. |

## 3. Comprehensive Manual Test Case Matrix (12-Column Standard)

| TC ID | Module | Risk Tier | Scenario / Title | Pre-Conditions | Test Data | Test Steps | Expected Result | Actual Result | Status | Priority | Traceability / AC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-CHK-001` | Checkout | Critical (P1) | Successful Credit Card payment with 3DS authorization | User logged in, Cart has 1 item (\$45.00) | Valid Visa test card with 3DS challenge | 1. Navigate to /checkout<br>2. Fill shipping details<br>3. Enter 3DS card<br>4. Click 'Place Order'<br>5. Authorize OTP popup | Order confirmed, receipt email queued, cart emptied | As expected | PASS | P1 | AC-01, AC-04 |
| `TC-CHK-002` | Checkout | Critical (P1) | Idempotency under double-submit click on 'Place Order' | User on final payment step | Valid payment details | 1. Rapidly double-click 'Place Order' button within 100ms | Button disables on first click; exactly 1 payment transaction charged | As expected | PASS | P1 | NFR-SEC-02 |
| `TC-CHK-003` | Checkout | High (P2) | Expired coupon code validation | User on payment step with \$100 cart | Coupon: `SUMMER2020` (Expired) | 1. Enter coupon `SUMMER2020`<br>2. Click 'Apply' | Inline error: 'Coupon code has expired', total remains \$100 | As expected | PASS | P2 | AC-05 |
| `TC-CHK-004` | Checkout | Medium (P3) | XSS payload injection in Delivery Instructions field | User on shipping step | Notes: `<script>alert('xss')</script>` | 1. Enter payload in notes<br>2. Complete order<br>3. View order history | Payload safely HTML-escaped; no script execution in UI | As expected | PASS | P3 | OWASP-A03 |
