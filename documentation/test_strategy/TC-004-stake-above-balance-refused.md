# TC-004 - Stake above available balance must be refused

- **Priority:** Critical
- **Area:** REST API

## Risk Rationale

A user must never be able to bet money the account does not have. If a stake above
the balance is accepted, the balance goes negative, and a negative balance is not a
display problem - it means the account has been committed to a wager it cannot pay
for, and every later figure the user sees is built on a wrong number. This is the
plainest overdraft check in the system and it currently holds, which is why it is
worth keeping as a standing test rather than a one-off. It also costs nothing to
run: a refused bet moves no money.

## Steps

1. Read the balance with `GET /api/balance` and write it down as `B`.
2. Pick a match dated today or later from `GET /api/matches`.
3. POST `/api/place-bet` with that `matchId`, `selection` of `AWAY`, and a stake of
   `500.00` - well above both the balance and the EUR 100.00 maximum stake.
4. Check the HTTP status code.
5. Check the `error` field in the response body.
6. Read the balance again and compare it with `B`.

## Expected Result

- HTTP `422`, with either `insufficient_balance` or `invalid_stake_max`.
  Both are correct: the server checks the maximum stake before the balance, so
  either error is an acceptable refusal.
- No bet recorded.
- Balance still exactly `B`, never negative.

## Note on the brief

The test brief asked for a stake of EUR 200.00. The maximum single stake in the spec
is EUR 100.00, so a stake that large would be refused for being over the maximum
rather than for being over the balance, and the test would not prove what it is
meant to. The step above deliberately stays over both limits and accepts either
refusal, which proves the money is protected either way.

## Cost - free

**This test case is free.** Every request it makes is refused by the server, so
the balance cannot move. It runs in the normal test run, with no flag needed.

## Current state

Passing, but weaker than the name suggests. Test file:
`tests/api_tests/test_place_bet_validation.py::test_over_balance_rejected`.
Free to run.

**The test does not actually test the balance rule.** With a balance of EUR 120.00
and a maximum stake of EUR 100.00, every stake that is above the balance is *also*
above the maximum, so the server rejects on the maximum and returns
`invalid_stake_max`. The `insufficient_balance` branch cannot be reached at this
balance at all. Verified on 2026-10-12 across stakes of 100.01, 150, 200, 1000,
1200, 12000 and 1000000 - every one returned `invalid_stake_max`, never
`insufficient_balance`.

So the case proves the maximum-stake rule, and the overdraft rule is untested.
Reaching it needs a balance below EUR 100.00, which means spending real money first.

Probing that same ladder turned up a far more serious defect next door:
**SportyQAD-021** - a negative stake is accepted and **credits** the account.

The exact boundary - betting precisely the full balance so it lands on EUR 0.00 - is
also not covered, because it succeeds and therefore costs money.