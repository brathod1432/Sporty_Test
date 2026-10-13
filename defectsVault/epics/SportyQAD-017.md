## [SportyQAD-017][UI][Improvement] Search and "no results" handling for the match list

- **Severity:** Medium
- **Type:** Epic

### Summary

With 103 matches and no way to search, users cannot find a specific fixture by
team, and an empty filter result currently produces a blank area with a
contradictory counter and no message. Search and a graceful empty state are the
two missing pieces.

Source: incoming test case "Past Matches and Historical Data Validation" (search
and missing-data edge cases).

### Reproduction Steps
1. Open the app and let the match list render.
2. Look for a search box, or any way to type a team or date to find a match.
3. Apply the Date filter with a day that has no fixtures (or an impossible odds
   range) and read the result.
- Observe: no search control exists at all; an empty result renders a blank
  list while the counter still claims the unfiltered total, with no message.

### Expected Result

- A search field that filters by team, competition or date as the user types.
- A clear "No matches found" state when a filter or search returns nothing.
- A counter that reflects the filtered result set.

### Observed Result

- No search input (`input[type=search]`, placeholder containing "search"), no
  sort control and no pagination control in the DOM.
- No "no results" / "no matches" copy anywhere in the rendered app.
- Empty filter result: blank list area, counter still reads the pre-filter
  total, no feedback at all (tracked as SportyQAD-010 and SportyQAD-015).

### Business Impact

Users give up quickly on a 100-plus-row list with no way to jump to a match,
and a blank result with a wrong counter reads as a broken app rather than an
empty one - both push people away from the only action that earns revenue.

### Evidence

- Absence probe 2026-10-12: no search, sort or pagination controls found.
- `../screenshots/gap_badrange.png` - blank list, counter stale, no message.
- Automatable today: `tests/ui_tests/test_regression_empty_state.py`
  (strict-xfailed, tracks the empty-state half of this gap).

### Related

SportyQAD-006 covers sorting and filtering; this epic covers search and the
empty state. SportyQAD-016 covers the missing results view.