## [SportyQAD-021][API] Negative stake accepted - the server pays the customer

- **Severity:** Critical
- **Type:** Bug

### Reproduction Steps
1. Read the balance: `GET /api/balance` -> `{"balance": 120.0, "currency": "EUR"}`.
2. POST `/api/place-bet` with an UPCOMING `matchId`, `selection` of `AWAY`, and a
   stake of `-1`.
3. Read the HTTP status and the response body.
4. Read the balance again: `GET /api/balance` -> `{"balance": 131.0, "currency": "EUR"}`.
5. Compare the two balances.

### Expected Result

A negative stake is not a valid amount of money. The request must be refused with
HTTP `422` and an error code such as `invalid_stake_min`, and the balance must not
move in either direction.

### Observed Result

The bet is **accepted**. HTTP `200`, body `{"message": "Bet placed successfully"}`,
and the balance **increased** by exactly the absolute value of the negative stake.

Measured on 2026-10-12:

| Stake sent | HTTP | Body | Balance before | Balance after | Delta |
|---|---|---|---|---|---|
| `-10` | 200 | Bet placed successfully | 120.00 | 130.00 | **+10.00** |
| `-1` | 200 | Bet placed successfully | 130.00 | 131.00 | **+1.00** |
| `-2.50` | 200 | Bet placed successfully | 131.00 | 133.50 | **+2.50** |

The credit matches the absolute stake exactly, every time. Nothing caps it - the
spec caps the maximum stake at EUR 100.00, but a negative stake bypasses the
maximum because no lower bound is applied.

### The full validation ladder, for contrast

Every neighbouring case is refused correctly. Only the negative stake is not:

| Stake | HTTP | Error code |
|---|---|---|
| `0` | 422 | `invalid_stake_min` |
| `0.01` | 422 | `invalid_stake_min` |
| `0.99` | 422 | `invalid_stake_min` |
| `"abc"` | 422 | `invalid_stake_type` |
| `null` | 422 | `invalid_stake_type` |
| absent | 422 | `invalid_stake_type` |
| `100.01` | 422 | `invalid_stake_max` |
| `1200` (10x balance) | 422 | `invalid_stake_max` |
| `12000` (100x balance) | 422 | `invalid_stake_max` |
| `1000000` | 422 | `invalid_stake_max` |
| **`-1`** | **200** | **none - accepted** |

The server checks type, then minimum, then maximum - and the minimum check is
`stake < 1.00` with no test for `stake < 0`. A negative number passes every gate.

### Business Impact

This is an unbounded money printer. Any user who sends one request with a negative
stake is paid the absolute value, repeatedly, without limit and without any bet
being genuinely placed. A trivial script turns the app into an infinite balance
generator, and nothing in the response or the UI signals that anything unusual
happened - the receipt reads "Bet placed successfully".

It is worse than an ordinary validation gap for three reasons:

- **It needs no special access.** No race condition, no double submit, no leaked
  credential. One `curl` from anyone holding the user id.
- **It is not self-limiting.** The other money bugs cost EUR 1 or EUR 2 per run.
  This one is unbounded in the amount and repeatable forever.
- **It defeats the evidence.** Every balance-based assertion in this suite assumes a
  balance that only falls. A single negative stake breaks that assumption, which is
  why the test cases here all read the live balance rather than a fixed figure.

For a real-money product this is the single most severe finding in this vault. It is
worse than SportyQAD-011 and SportyQAD-014 combined, because those lose the customer
a small fixed amount per bet while this one creates money from nothing.

### Evidence

- `tests/api_tests/test_api_business_rules.py::test_negative_stake_rejected`
  (strict XFAIL, SportyQAD-021) - currently HTTP 200 and the balance rises.
- Live probe 2026-10-12: three negative stakes (-10, -1, -2.50), each credited by
  exactly its absolute value.
- Validation ladder probe 2026-10-12: 10 neighbouring stake values, all correctly
  refused, confirming the gap is specific to negatives.
- Test file is spend-gated, because while this bug is open every run **adds** to the
  balance instead of removing from it.

### Fix direction

Reject any stake that is not strictly greater than zero, before the minimum check,
and return `invalid_stake_min`. The check must be on the numeric value, not on the
range, so that `-1`, `-0.01` and `-1000000` are all refused.