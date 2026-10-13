## [SportyQAD-006][UI][Improvement] Sort and filter matches by time frame, country/league, team, upcoming/past

- **Severity:** Medium
- **Type:** Epic

### Reproduction Steps
1. Open the app (103 matches, dates 2026-02-27 to 2026-12-28, 58 of 78 dates past).
2. Try to see only next weekend's matches, or only Premier League, or only
   upcoming (non-PAST) fixtures.
3. Observe: only Date-day/range and Odds-range filters exist; no sort control,
   no league/country filter, no team search, no upcoming/past toggle.

### Expected Result
Sort (kickoff date, league) plus filters for time frame, country/league, team, and an upcoming/past switch, so the 103-match wall becomes navigable.

### Observed Result
Flat API-ordered list, past events first.

### Business Impact
Users cannot find the matches they care about, which
directly suppresses bet placement - the app's only revenue action.

### Evidence
`../screenshots/explore_home.png` (only Date/Odds
filters visible). Feasibility: `kickoffDate` and `competition` already come
from the API, so client-side sort/filter is possible without backend changes;
server-side query params would scale better.
