# TC-001 - Happy-path bet placement and receipt reconciliation

- **Priority:** Critical
- **Area:** UI (Selenium)

## Risk Rationale

Placing a bet is the only thing in this app that makes money. If it is broken the
product cannot be used at all. If it works but shows the wrong numbers, the user is
told one thing and charged another, which is the kind of error that ends in a
dispute. This is also the only flow that cannot be proven through the API alone,
because the receipt modal, the cleared bet slip and the button states only exist in
the browser. So it carries the highest priority despite costing money to run.

## Steps

1. Read the balance with `GET /api/balance` and write it down as `B`.
2. Open the app and scroll to a match dated today or later. Do not use a PAST match.
3. Note the two team names in the order shown, and the odds shown on the `1` button.
4. Click the `1` button. Check the bet slip fills in with the same decimal odds.
5. Type `1.00` in the stake field. Note the potential payout shown in the slip.
6. Click `Place Bet` once. Do not click it again.
7. Read the receipt and write down: Bet ID, match name, selection, stake, odds,
   payout, timestamp and currency.
8. Check that payout equals stake multiplied by odds, to two decimal places.
   `1.00 x 2.45` must be `2.45`, not `2.449999`.
9. Check the home team is named before the away team in the receipt.
10. Check the timestamp is within a minute of now.
11. Close the receipt. Check the bet slip is now empty.
12. Read the balance again with `GET /api/balance`. Check it is exactly `B - 1.00`.

## Expected Result

- The receipt shows every field listed in step 7, and none is blank.
- Payout arithmetic is exact to two decimals.
- Home team appears before away team.
- Timestamp is recent.
- The bet slip is empty after the receipt closes.
- The balance drops by exactly `1.00`, no more and no less.
- If anything above fails, the bet was still recorded by the server, so record the
  balance before and after and report both.

## Cost - check manually

**This test case costs money. Validate it by hand, not by automation.**

Placing a real bet spends EUR 1.00 of test balance, so the automated version is
skipped by default and only runs deliberately with `--run-bet`. Run this case
manually and record the outcome. Manual case: `SportyMT-001` and `SportyMT-005`.

## Current state

The automated version is `tests/ui_tests/test_e2e_bet.py::test1_place_bet_happy_path`,
which is skipped by default. Do not rely on it - it does **not** check everything
above. It only confirms the text "Bet ID" appears, the text "1.00" appears, and the
balance changed. Steps 8, 9 and 10 are not automated at all, and step 12 only checks
the balance changed, not that it fell by exactly 1.00.

Manual cases `SportyMT-001` and `SportyMT-005` are the real validation for this
case. Run those.