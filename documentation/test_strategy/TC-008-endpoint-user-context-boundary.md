# TC-008 - Endpoint user-context boundary

- **Priority:** High
- **Area:** REST API

## Risk Rationale

The app has no login and no password. The only thing identifying a user is the
`x-user-id` header, so that header is the entire authentication boundary. The whole
wallet - balance and betting activity - sits behind it. If any endpoint serves data
without checking it, one person can read another person's balance. This rates High
rather than Critical for one reason: the boundary currently holds on every endpoint
tested, and the id is long and random, so it cannot simply be guessed. What remains
is the risk of a leak rather than a crack. That changes the moment the id gets into
a screenshot or an access log, because there is no logout and no way to revoke it.

## Steps

1. Call `GET /api/matches` with no headers at all.
2. Call `GET /api/balance` with no headers at all.
3. Call `POST /api/reset-balance` with no headers at all.
4. Call `POST /api/place-bet` with no headers at all.
5. Repeat all four with a made-up user id, for example `candidate-AAAAAAAA`.
6. Check the status code and the `error` field on each of the eight responses.
7. Check whether any response carries a session cookie.
8. Check the URL the app loads in the browser for the user id.

## Expected Result

- All eight requests are refused with HTTP `401`.
- The `error` field is `missing_user_id` when the header is absent, and
  `invalid_user_id` when it is present but wrong.
- No balance, match or bet data appears in any response body.
- No session cookie is ever set - there is no session, which is expected today.
- The user id is not visible in the page URL. **This last one currently fails** - it
  is passed in the URL as `?user-id=...`, so it ends up in browser history, access
  logs and any screenshot of the address bar.

## Cost - free

**This test case is free.** Every request it makes is refused by the server, so
the balance cannot move. It runs in the normal test run, with no flag needed.

## Current state

Steps 1 to 7 pass. Automated in `tests/api_tests/test_protocol_validation.py` and
`tests/api_tests/test_rest_endpoints.py`. Free to run.

Step 8 fails today and is filed as **SportyQAD-020** (Epic) - the only credential the
app has is exposed in the URL.

Two related gaps are recorded but not testable yet:

- There is no bet history endpoint, so a bet cannot be looked up afterwards to check
  it belongs to the right user.
- No test covers a fabricated `matchId` in a real bet, because that request would
  place an actual wager and cost money.