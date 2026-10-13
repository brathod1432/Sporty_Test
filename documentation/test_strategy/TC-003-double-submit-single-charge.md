# TC-003 - Double submission must not charge twice

- **Priority:** Critical
- **Area:** REST API

## Risk Rationale

Double-clicking Place Bet, or retrying after a slow response, must never cost the
user twice. Two things make this risky here. First, the browser makes it easy - a
user can click twice before the first request returns, which is why this has to be
checked at the API rather than the UI. Second, and worse, a user who has been
charged twice has no way to tell which of the two charges was the mistake, and the
app shows no bet history to check against. At the moment the server has no duplicate
protection at all: both requests succeed and both charge.

## Steps

1. Read the balance with `GET /api/balance` and write it down as `B`.
2. Pick a match dated today or later from `GET /api/matches`.
3. Fire two POST requests to `/api/place-bet` at the same time, with no pause
   between them. Both use the same `matchId`, `selection` of `HOME`, and a stake of
   `1.00`.
4. Look at both responses.
5. Read the balance and compare it with `B`.
6. Count how many times the balance actually fell by 1.00.

## Expected Result

- The first request succeeds with HTTP `200`.
- The second is refused with HTTP `409` (conflict), or returns the same bet as the
  first rather than creating a new one.
- Balance drops by exactly `1.00` in total, not `2.00`.
- Only one bet exists for the user.

## Cost

**Costs money while the bug is open.** The automated version spends EUR 2.00 on each
failing run, because both requests are charged. It is therefore automated but held
back behind `--run-bet` - do not run it by accident.

## Current state

**This test fails today.** Both requests return `200` and EUR 2.00 is taken. Filed as
**SportyQAD-014** (Critical, open). The second request should be rejected with `409`;
the spec describes an in-progress guard that was never implemented. Written as a
strict XFAIL. It charges EUR 2.00 on each failing run, so it sits behind `--run-bet`.

Test file: `tests/api_tests/test_place_bet_double_submit.py`.

There is no UI version of this test. A rapid double-click on the Place Bet button
would be the closest match to what a real user does, and it is not covered.