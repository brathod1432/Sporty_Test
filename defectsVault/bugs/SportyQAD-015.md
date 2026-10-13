## [SportyQAD-015][UI] Match counter stays at the unfiltered total after filtering

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. Open the app; note the counter ("Showing 103 matches").
2. Open the Date filter, select 10 October 2026, click Apply.
3. Observe the list: only one card is rendered (Dortmund vs Frankfurt, Sat 10 Oct).
4. Read the counter again.

### Expected Result
The counter reflects the filtered set ("Showing 1 matches").

### Observed Result
The list filters correctly but the counter still reads "Showing 103 matches", the pre-filter total.

### Business Impact
Users cannot tell how many matches a filter actually returned,
so they may believe a date is fully explored when it is not, or think the filter
failed when it worked.

### Evidence
`../screenshots/gap_dateapplied.png` - filter label "Date: 10/10/2026",
a single rendered card, counter still "Showing 103 matches". Same stale-counter
family as SportyQAD-010, reproduced on a valid (non-error) filter path.
