# TC-005 - Stake below minimum must be refused

- **Priority:** High
- **Area:** REST API

## Risk Rationale

The spec sets a minimum stake of EUR 1.00. Below that the app should refuse rather
than accept, because the rules it states elsewhere assume a meaningful stake - a
receipt, a payout calculation and a balance reconciliation all stop making sense at
EUR 0.01. The risk here is quiet rather than loud: a tiny accepted bet would not
look broken to the user, it would just quietly erode the balance. Two values are
tested instead of one because the spec can be read as "at least 1.00" or "greater
than 1.00" - testing below both readings means the test passes whichever rule the
server actually enforces, and it does not depend on resolving that ambiguity first.

## Steps

1. Read the balance with `GET /api/balance` and write it down as `B`.
2. Pick a match dated today or later from `GET /api/matches`.
3. POST `/api/place-bet` with `selection` of `DRAW` and a stake of `0.50`.
4. Check the HTTP status code and the `error` field.
5. POST `/api/place-bet` again with the same match and a stake of `0.01`.
6. Check the HTTP status code and the `error` field.
7. Read the balance and compare it with `B`.

## Expected Result

- Both stakes return HTTP `422` with `invalid_stake_min`.
- Neither bet is recorded.
- Balance still exactly `B`.

## Cost - free

**This test case is free.** Every request it makes is refused by the server, so
the balance cannot move. It runs in the normal test run, with no flag needed.

## Current state

Passing. Test file:
`tests/api_tests/test_place_bet_validation.py::test_below_minimum_rejected`.
Free to run - both requests are refused, so nothing is charged.

Two related checks are still missing and would also be free:

- A stake of exactly `0`. It should be refused by the same rule, but a zero stake is
  a special case and is not the same code path as a small one.
- A stake sent as text, for example `"abc"`, or a negative stake. Both should be
  refused rather than quietly treated as zero.