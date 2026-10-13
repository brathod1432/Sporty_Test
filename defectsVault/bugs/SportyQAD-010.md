## [SportyQAD-010][UI] Invalid odds range silently applied - no rejection, blank list, stale counter

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. Open the app, wait for the 103-match list.
2. Open the "Odds: All" filter, set MIN to 50 and MAX to 2 (min > max).
3. Click Apply.
4. Observe: no error, no warning, no message of any kind.

### Expected Result
Per spec Section 2.6 the invalid range "must [be] reject[ed] ... with clear feedback".

### Observed Result
The values are silently coerced to "Odds: 10.00 - 10.00", the match list renders **empty**, yet the counter still claims "Showing 103 matches".

### Business Impact
Users get an empty page with a contradicting counter and no
way to know their filter was invalid - discovery flow dead-ends silently.

### Evidence
`../screenshots/gap_badrange.png` (10.00-10.00 label, empty list,
"Showing 103 matches", no message). Valid-range apply partially works (MIN took),
so the defect is specifically the missing invalid-range rejection.
