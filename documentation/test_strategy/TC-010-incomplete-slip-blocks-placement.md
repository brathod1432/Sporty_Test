# TC-010 - Placement cannot be invoked on an incomplete slip

- **Priority:** Medium
- **Area:** UI

## Risk Rationale

A bet should only be submittable once an outcome and a stake are both present.
Without that rule the app can be pushed into sending a bet with a missing field, and
the server either rejects it after a pointless round trip or, worse, accepts it with
a default. It also protects the user from a mis-click: an empty or half-filled slip
should not be one stray click away from spending money. This is Medium rather than
High because the server-side validation is independently covered by TC-004 and
TC-005 - if a bad request does reach the API it is still refused there. What is being
tested here is the screen behaving sensibly, not whether the money is safe.

## Steps

1. Open the app and leave the bet slip empty. Do not click any odds button.
2. Look for the `Place Bet` button. Note whether it is present and whether it is
   clickable.
3. Try to activate it.
4. Confirm no bet request was sent and the balance did not change.
5. Select an outcome on a match dated today or later. Leave the stake blank.
6. Look at the `Place Bet` button again and try to activate it.
7. Confirm still no bet request and the balance unchanged.
8. Enter a valid stake of `1.00` and check the button becomes usable.

## Expected Result

- With no outcome selected, `Place Bet` cannot be activated.
- With an outcome but no stake, `Place Bet` cannot be activated.
- No request reaches `/api/place-bet` in either case.
- The balance never changes.
- Once both an outcome and a valid stake are present, the button becomes usable.
- Any blocked attempt should tell the user what is missing, rather than doing
  nothing at all.

## Cost - free

**This test case is free.** Every request it makes is refused by the server, so
the balance cannot move. It runs in the normal test run, with no flag needed.

## Current state

Passing. Test file: `tests/ui_tests/test_regression_no_selection_blocks.py`.
Free to run.

One related defect is open: **SportyQAD-013** - when no odds are selected the
`Place Bet` button is not rendered at all, rather than being shown disabled. A user
does not learn why nothing is happening to them.

The blocked attempt currently shows the failure modal from the spec, covered by
`tests/ui_tests/test_regression_error_modal.py`.

Not covered: what happens when the balance is EUR 0.00. The button should be
disabled, but that state cannot be reached without spending the balance down first,
so there is no way to test it for free.