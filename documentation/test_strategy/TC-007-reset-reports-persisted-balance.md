# TC-007 - Reset must report the balance it restores

- **Priority:** Medium
- **Area:** REST API
- **Cost - free**

**This test case is free.** Every call it makes moves no money - it only reads and
resets. It runs in the normal test run, with no flag needed.

## Risk Rationale

Resetting the balance is how a tester recovers an account that has been drained by a
bug or by another tester sharing the same user id. The risk here is not to the end
user, it is to our own results. The endpoint works - it does restore the account -
but it reports the wrong number for what it restored. A tester or script that takes
the opening balance from the reset response instead of re-reading it will work from
a figure that does not exist. Because the error is a small, fixed offset it looks
like a perfectly plausible balance, which is what makes it easy to miss. Medium
because no money moves incorrectly; the damage is to the evidence, not the customer.

## Steps

1. Read the balance with `GET /api/balance` and write it down.
2. POST `/api/reset-balance`.
3. Write down the `balance` value in the reset response body.
4. Read the balance again with `GET /api/balance`.
5. Compare the value from step 3 with the value from step 4.
6. Repeat steps 2 to 5 twice more.

## Expected Result

- HTTP `200` with a message, a balance and a currency.
- The balance in the response equals the balance read straight afterwards.
- The account is genuinely restored, not left untouched.

## Current state

**The reset works. The number it reports is wrong.**

The response always says `balance: 125.5`. The account actually restores to
`120.00`. The two never agree.

Persistence was confirmed on 2026-10-12: a free suite run started at a balance of
`133.50`, called reset twice, placed no bets, and finished at `120.00`.

This was nearly filed as a different bug. When the balance already happens to be
`120.00`, a reset changes nothing visible, and the endpoint looks like a silent
no-op that reports success. That reading is wrong - the effect was simply invisible.
Any conclusion about this endpoint drawn from a 120.00 balance is unreliable.

Filed as **SportyQAD-018** (Medium, open), downgraded from High on 2026-10-12 once
it was clear that no money moves incorrectly. Tracked by a strict XFAIL in
`tests/api_tests/test_rest_endpoints.py::test_reset_reports_actual_balance`.

Two knock-on effects:

- The test brief's opening balance of EUR 125.50 is wrong. This account holds
  **EUR 120.00**. Never assume a fixed figure - always read it.
- Reset is safe to call before a scored block, it just must not be trusted for the
  number. This correction restores the advice in `tests/manual_tests/MANUAL_TESTS.md`,
  which had been amended after the earlier, incorrect reading.

Not a caching problem: the balance responses report `X-Vercel-Cache: MISS` and
`max-age=0, must-revalidate`, and a cache-busted request returns the same value.