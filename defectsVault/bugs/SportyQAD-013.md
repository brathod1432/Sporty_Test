## [SportyQAD-013][UI] PLACE BET button not rendered at all when no odds selected (absent, not disabled)

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. Open the app fresh (empty bet slip, no selection).
2. Query the DOM for any button whose text contains "place bet".
3. Observe: zero matches - the button does not exist.
4. Select an outcome; the button now appears (disabled, since no stake).
5. Clear the selection; the button disappears again.

### Expected Result
A disabled PLACE BET control present from load (consistent affordance), or at minimum a stable, testable control that toggles.

### Observed Result
The button is conditionally rendered: absent with no selection, present-but- disabled once a selection exists. Inconsistent control presence (UX flicker on every select/deselect) and a selector-timing hazard for automation.

### Business Impact
Users lose the sense of the primary action's location when the
slip is empty, and the flow "appears" rather than enables - small trust tax on the
money screen; no data risk.

### Evidence
Live probe 2026-10-12: `PLACE BET state (no selection): []`;
`PLACE BET state (selection, no stake): [('PLACE BET', False)]`. Screenshot:
`../screenshots/gap_pb_no_stake.png`.
