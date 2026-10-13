## [SportyQAD-005][UI] Empty-text buttons, icon buttons lack discernible names

- **Severity:** Low
- **Type:** Bug

### Reproduction Steps
1. Open the app, wait for render.
2. Count buttons: 351 total, ~40 with empty text (slider thumbs, icon-only
   controls); icon buttons expose only Material-Icons ligature text
   (`calendar_today`, `expand_more`).

### Expected Result
Every control has an accessible name and stable test hooks.

### Observed Result
Screen readers get ligature/noise, and automation must match on class fragments (fragile - it misfired during this very exploration, clicking the Odds filter instead of an odds button).

### Business Impact
Accessibility gap for assistive-tech users; brittle
selectors raise future automation maintenance cost.

### Evidence
Run log (inventory: 351 buttons, ~40 empty-text). Screenshot:
`../screenshots/explore_home.png`.
