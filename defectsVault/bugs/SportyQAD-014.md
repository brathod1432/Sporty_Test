## [SportyQAD-014][API] Double submit charges twice - 409 concurrency guard not implemented

- **Severity:** Critical
- **Type:** Bug

### Reproduction Steps
1. Read balance via `GET /api/balance` (was 120.50).
2. Fire two `POST /api/place-bet` requests back-to-back for the same user, same
   UPCOMING match, selection HOME, stake 1.00, valid `x-user-id`.
3. Observe: both return 200 "Bet placed successfully".
4. Read balance: 118.50 - EUR 2.00 deducted for what the user intended as one bet.

### Expected Result
The first request succeeds and the second is refused with 409 "bet already in progress (same user)"; exactly one EUR 1.00 deduction.

### Observed Result
Both requests are accepted and charged; no concurrency guard of any kind is present server-side.

### Business Impact
A double-click (or any client retry, flaky network, or
duplicate tab) silently takes double the intended stake - direct money loss and
the exact scenario the spec's 409 rule exists to prevent.

### Evidence
pytest `test_place_bet_double_submit` (strict-xfailed, both 200
receipts dumped); live 2026-10-12 18:44 UTC, balance 120.50 -> 118.50, second
receipt `{"message":"Bet placed successfully", ... "balance":118.5, "currency":"USD"}`.
