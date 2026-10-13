# TC-006 - Receipt data integrity and payout arithmetic

- **Priority:** High
- **Area:** UI

## Risk Rationale

The receipt is the only record the user gets of what they just did. If a number on it
is wrong, the user has no way to check it, because there is no bet history to compare
against and no receipt to retrieve later. A receipt that says USD while the whole app
is in EUR, or that rounds a payout to the wrong number of decimals, turns every bet
into a possible dispute. This sits at High rather than Critical because the money
taken is still correct - the balance moves by the right amount - so the error is in
what the user is told rather than in what they are charged.

## Steps

1. Read the balance with `GET /api/balance` and write it down as `B`.
2. Open the app and pick a match dated today or later that has distinctive odds.
3. Write down what the bet slip shows before placing: both team names in order, the
   selection, the stake, the odds and the potential payout.
4. Enter a stake of `1.00` and click `Place Bet` once.
5. Write down every field on the receipt: Bet ID, match name, selection, stake, odds,
   payout, timestamp and currency.
6. Compare each receipt field against what was captured in step 3.
7. Multiply stake by odds by hand and check it against the payout to two decimals.
8. Check the currency label on the receipt against the rest of the app.
9. Check the Bet ID is not blank and the timestamp is recent.

## Expected Result

- Every captured value matches the receipt exactly.
- Payout equals stake multiplied by odds, to two decimal places, with no rounding
  drift such as `2.4499999`.
- Home team is named before away team.
- Bet ID is present and unique.
- Timestamp is within a minute of placement.
- The currency on the receipt is EUR, matching the balance.

## Cost - check manually

**This test case costs money. Validate it by hand, not by automation.**

Placing a bet to get a receipt spends EUR 1.00 each run. Comparing the receipt fields
side by side is also quicker by eye than in code. Manual case: `SportyMT-005`.

## Current state

Manual only, by `SportyMT-005` in `tests/manual_tests/MANUAL_TESTS.md`. There is no
automated version of this case.

One real defect is already open here: **SportyQAD-012** - the receipt shows the
currency as USD while the balance and everything else are EUR.

TC-001 overlaps with this case and covers the same fields. The difference is that
TC-001 is about the whole flow working, and this case is specifically about the
numbers on the receipt agreeing with each other.