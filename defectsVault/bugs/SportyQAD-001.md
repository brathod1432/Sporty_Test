## [SportyQAD-001][UI] Past matches listed first under "Upcoming Football Matches"

- **Severity:** High
- **Type:** Bug

### Reproduction Steps
1. Open the app with a valid `?user-id=`.
2. Wait for the match list to render (103 matches).
3. Read the badges on the top cards (Man Utd-Chelsea, Real Madrid-Barcelona, ...).

### Expected Result
Upcoming/pre-match fixtures only (spec Section 1, Section 3), no PAST badges.

### Observed Result
The top of the list is past-dated cards (Feb/Mar) each carrying a `PAST` badge under the "Upcoming Football Matches" header. Live catalog check (`GET /api/matches`, 2026-10-12): dates span 2026-02-27 to 2026-12-28, with **58 of 78 distinct dates already past** - past events are listed first, in API order, pushing the ~20 future dates far down the list. Past matches must not accept bets (upcoming-only per spec); only future matches should be placeable.

### Business Impact
Users cannot tell whether they are wagering on future or
already-played events - a trust-breaking defect for a betting product and a
likely compliance problem.

### Evidence
`../screenshots/explore_home.png` (PAST badges visible
on all cards; section header says "Upcoming", counter "Showing 103 matches").
