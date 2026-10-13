## [SportyQAD-016][UI][Improvement] Historical results view for completed matches

- **Severity:** Medium
- **Type:** Epic

### Summary

The app lets users bet on upcoming matches but offers no way to review what
already happened. There is no results screen, no final score, no winner, and no
match statistics - the catalog itself carries no result data at all. Users who
want to verify or analyse previous activity have nowhere to go.

Source: incoming test case "Past Matches and Historical Data Validation".

### Reproduction Steps
1. Open the app and let the match list render.
2. Look for a "Past Matches" section, a results view, or any link to history.
3. Try to find a final score, winner, or statistics (possession, shots).
4. Attempt to open a completed match and replay its bet slip.
- Observe: none of these exist. No results surface, no score fields, no
  statistics, and no match detail view.

### Expected Result

- A results/history view listing completed matches with final score and winner.
- Per-match detail with the odds that were offered at kickoff.
- Optional team statistics (possession, shots) where a data feed exists.
- A way to replay what a placed bet would have returned.

### Observed Result

- No "Past Matches", "History", "Statistics", "score", "winner", "search",
  "pagination" or "sort" text anywhere in the rendered app.
- No search input, pagination control or sort control in the DOM.
- `GET /api/matches` returns 103 matches whose fields are exactly
  `id, competition, kickoffDate, homeTeam, awayTeam, odds` - no score, result or
  status field.
- Match cards render `PAST` badges but no result, so a completed fixture is
  indistinguishable from an unsettled one apart from the date.

### Business Impact

Bettors cannot verify past outcomes or build any view on form, which weakens
trust in the odds shown and makes the product feel like a one-way transaction.
It also blocks the natural retention path: a user with no history and no results
has little reason to return.

### Evidence

- `../screenshots/explore_home.png` - past-dated cards show a `PAST` badge and
  the team names with a "-" slot where a score would sit.
- Catalog probe 2026-10-12: `Match` schema has no result or score field.
- Absence probe: none of the searched UI surfaces exist.
- Note: this is a gap, not a defect - the feature spec scopes betting to
  upcoming/pre-match events only (Section 1) and never specifies results.

### Related

SportyQAD-007 ("My Bets" history) is the user-side counterpart: this epic is
about match results, that one about the user's own wagers.