## [SportyQAD-018][API] Reset balance reports the wrong balance

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. Read the balance: `GET /api/balance` -> `{"balance": 120.0, "currency": "EUR"}`.
2. POST `/api/reset-balance`.
3. Read the `balance` field in the response body.
4. Read the balance again with `GET /api/balance`.
5. Compare the value from step 3 with the value from step 4.

### Expected Result

The endpoint restores the account to its opening balance and reports that same
figure. The value in the response must equal the value a follow-up
`GET /api/balance` returns.

### Observed Result

The response **always** reports `125.50`:

```json
{"message": "Balance reset successfully", "balance": 125.5, "currency": "EUR"}
```

but the actual restored balance is **`120.00`**. The two never agree.

The reset itself does work. Confirmed on 2026-10-12: a free suite run began with a
balance of `133.50`, called reset twice, placed no bets, and finished at `120.00`.
So the endpoint restores EUR 120.00 correctly and only the number it reports is
wrong.

This is easy to misread, and it was misread once. When the balance already happens
to be `120.00`, a reset changes nothing visible, which makes the endpoint look like
a silent no-op. It is not - the value it reports is simply not the value it stores.
Any conclusion about the reset mechanism drawn from a 120.00 balance is unreliable.

Not a caching problem: the balance responses report `X-Vercel-Cache: MISS` and
`Cache-Control: public, max-age=0, must-revalidate`, and a cache-busted request
returns the same figure.

### Business Impact

The endpoint lies about its own result, and a client that trusts the response will
be wrong. The practical damage:

- Any test or script that sets its baseline from the reset response rather than
  re-reading `GET /api/balance` works from a figure that does not exist.
- A tester investigating a balance discrepancy resets, sees `125.50` returned, and
  concludes the account is healthy when it is not.
- The error is off by a fixed amount, which is the hardest kind to spot. It looks
  like a plausible balance rather than an obviously broken one.

Severity is Medium rather than High, and downgraded from the original High on
2026-10-12: no money moves incorrectly and the reset genuinely works, so nothing is
lost. It is a reporting defect that corrupts test evidence, not a financial one.

### Evidence

- `tests/api_tests/test_api_business_rules.py::test_reset_reports_actual_balance`
  (strict XFAIL, SportyQAD-018) - reports 125.50, actual 120.00.
- Re-check 2026-10-12, three consecutive resets: reported `125.5` each time, actual
  `120.0` each time.
- Persistence confirmed 2026-10-12 by a free suite run: balance `133.50` before,
  two reset calls, zero bets placed, balance `120.00` after.
- Response headers: `Age: 0`, `X-Vercel-Cache: MISS`,
  `Cache-Control: public, max-age=0, must-revalidate`.

### Fix direction

Return the balance that was actually persisted, not a constant. If the opening
balance is EUR 120.00 for this account, the response should say `120.0`.