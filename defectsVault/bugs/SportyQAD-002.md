## [SportyQAD-002][UI] No kickoff time shown, only date plus "-" placeholder

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. Open the app, wait for matches to render.
2. Look at any match card meta line (e.g. "Serie A - Sun 01 Mar").
3. Note the `-` slot under each team name where a time would sit.

### Expected Result
"kickoff date/time label" per spec Section 2.1.

### Observed Result
Date only ("Fri 27 Feb") plus a bare `-` that reads as missing data (the API carries `kickoffDate` date-only, so the UI invents the empty slot).

### Business Impact
Bettors cannot see when a match starts, so they cannot
judge urgency - directly weakens the core pre-match flow.

### Evidence
`../screenshots/explore_home.png` (date + `-` slots on
every card).
