# TC-002 - Past-match bet must be refused

- **Priority:** Critical
- **Area:** REST API

## Risk Rationale

The feature specification (Section 1) limits betting to matches that have not started
yet. A match dated in the past has already been played, so nobody can win it - yet
the server accepts the bet and takes the stake. The user pays for something that
cannot return a cent, and nothing in the response tells them the match had already
started. This is the clearest case in the app of taking money for an outcome the user
could never have won, which is why it rates above every display or usability defect.

## Steps

1. Read the balance with `GET /api/balance` and write it down as `B`.
2. Call `GET /api/matches` and pick a match whose `kickoffDate` is earlier than today.
3. POST `/api/place-bet` with that `matchId`, `selection` of `HOME` and a stake of `1.00`.
4. Check the HTTP status code.
5. Check the `error` field in the response body.
6. Read the balance again and compare it with `B`.

## Expected Result

- HTTP `422`, with a match-validation error code such as `invalid_match_id`.
- No bet recorded.
- Balance still exactly `B`.

## Cost

**Costs money while the bug is open.** The automated version spends EUR 1.00 on each
failing run, because the server charges the bet instead of refusing it. It is
therefore automated but held back behind `--run-bet` - do not run it by accident.

## Current state

**This test fails today.** The bet is accepted, HTTP `200` is returned and EUR 1.00
is charged. Filed as **SportyQAD-011** (Critical, open). The test is written as a
strict XFAIL so it stays in the suite and will start passing by itself the day the
server is fixed. It charges EUR 1.00 on each failing run, so it is behind `--run-bet`.

Test file: `tests/api_tests/test_past_match_rejected.py`.