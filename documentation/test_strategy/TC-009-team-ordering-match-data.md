# TC-009 - Match card team ordering and displayed data

- **Priority:** Medium
- **Area:** UI

## Risk Rationale

The match card is the only place both teams are shown before a bet is placed. If the
home and away teams are swapped, the user reads the wrong pairing, picks the `1` or
`2` button believing it means something else, and bets on the wrong team. The money
is lost in a completely ordinary way - the bet is accepted, charged and settled
correctly, just against the wrong team - so nothing else in the app would catch it.
That financial consequence is what keeps this in the test set even though the defect
would be on screen.

## Steps

1. Open the app and let the list render.
2. Take the first match dated today or later.
3. Read the `GET /api/matches` entry for that match and note the `homeTeam` and
   `awayTeam` fields exactly as the API returns them.
4. Read the two team names off the card, from left to right.
5. Compare the left name with `homeTeam` and the right name with `awayTeam`.
6. Check the odds are shown as three buttons labelled `1`, `X` and `2`.
7. Compare each button's value with the `home`, `draw` and `away` odds in the API
   response for that match.
8. Check the competition name is visible on the card.
9. Check the kickoff date, and whether a kickoff time is shown.

## Expected Result

- The left team on the card is always `homeTeam` and the right is always `awayTeam`,
  with no exceptions across the list.
- Three odds buttons are present, each showing a decimal greater than 1.0.
- The button values match the API odds for that same match.
- The competition name is visible.
- A kickoff date and time are both shown.

## Cost - free

**This test case is free.** Every request it makes is refused by the server, so
the balance cannot move. It runs in the normal test run, with no flag needed.

## Current state

Partly covered:

- **Odds buttons and their values: pass.** `tests/ui_tests/test_regression_match_cards.py`.
- **Team ordering: not tested at all.** This is the main point of the case and it has
  no test. It is free to add - it only reads the DOM and the API, it places no bet.
- **Kickoff time: known defect.** The app shows a date with a bare `-` where the time
  should be. Filed as **SportyQAD-002**, tracked by a strict XFAIL in
  `tests/ui_tests/test_regression_kickoff_time_slot.py`.
- **Competition name: not explicitly asserted**, though it does render.

One edge case in the original brief cannot be tested: asking what happens when a
match is missing some of its odds. All 103 matches currently carry all three
outcomes, so there is nothing to test against. It would need a fixture or a mocked
response.