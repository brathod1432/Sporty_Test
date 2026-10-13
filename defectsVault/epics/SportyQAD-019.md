## [SportyQAD-019][API][Improvement] No authentication or session management

- **Severity:** High
- **Type:** Epic

### Summary

There is no login, no password, no session and no logout. The sole credential is
an `x-user-id` header, and knowing it grants complete, permanent and
unrevocable access to that account's balance and betting activity. Most of the
incoming "Authentication and Session Security" case has nothing to test because
none of that machinery exists.

Source: incoming test case "Authentication and Session Security (End-to-End)".

### Reproduction Steps
1. Open the app; note the user id in the address bar (`?user-id=...`).
2. Open DevTools, Network, and issue any request without the `x-user-id` header.
3. Look for a login page, a logout control, a session cookie, or a token.
- Observe: every request without the header is refused with `401 invalid_user_id`.
  There is no login form, no session cookie (`Set-Cookie` never appears), no
  session or auth header, and no `WWW-Authenticate` challenge anywhere.

### Expected Result

- Login with credentials, then a session that persists across tabs and expires.
- An explicit logout that invalidates the session server-side.
- Server-side revocation, so a leaked credential can be cut off.
- 2FA as an optional second factor.

### Observed Result

- No credential store: the app cannot distinguish "the owner" from "anyone who
  learned the id".
- No session: no `Set-Cookie`, no token, no server-side session store. Requests
  are stateless and re-authenticated on every call.
- No logout: nothing to invalidate, so a leaked id stays valid forever.
- No inactivity timeout: a session cannot expire because none is created.

The id is high entropy (`candidate-AAAAAAAA`), so it is not guessable -
guessing was tested and correctly refused. The exposure comes from disclosure,
not brute force.

### Business Impact

The app hands over a bettor's wallet on presentation of a single long-lived
string. Any leak of that string - a screenshot, a shared link, a proxy log, a
support ticket - is permanent and silent: the owner sees bets appear that they
never placed, with no way to revoke the thief and no alert that anything
happened. For a real-money product that is the difference between a lost password
and an account takeover.

### Evidence

- `tests/api_tests/test_protocol_validation.py::test_missing_user_context` -
  no header -> `401 missing_user_id`; fabricated id -> `401 invalid_user_id`.
- `tests/api_tests/test_rest_endpoints.py::test_endpoints_require_user_context` -
  all four endpoints enforce the boundary.
- Auth probe 2026-10-12: `Set-Cookie` absent on both the page and the API;
  6 of 6 well-formed and malformed candidate ids refused with `invalid_user_id`;
  no `Authorization` or `WWW-Authenticate` header on any response.

### Related

SportyQAD-020 covers the credential leaking through the URL. The current
boundary itself is correctly enforced - this epic is about the credential being
the whole of authentication.