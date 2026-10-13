## [SportyQAD-012][API] place-bet receipt returns currency USD, everything else is EUR

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. `POST /api/place-bet` with any valid payload.
2. Compare the receipt `currency` against `GET /api/balance`, the OpenAPI spec,
   the feature spec (Section 4.1: EUR), and the UI (EUR everywhere).

### Expected Result
`"currency": "EUR"` like every other surface.

### Observed Result
Receipt body says `"currency": "USD"` while balance/match/spec/UI all say EUR.

### Business Impact
Currency mismatch on the money receipt erodes trust and can
break downstream reconciliation that keys on currency.

### Evidence
Live receipt 2026-10-12 13:47 UTC:
`{"message":"Bet placed successfully","matchId":"premier-league-manutd-chelsea",`
`"selection":"HOME","stake":1,"odds":2.45,"payout":2.45,"balance":122.5,"currency":"USD"}`.
