## [SportyQAD-004][UI] Odds-filter popover covers the match cards and cannot be dismissed

- **Severity:** Medium
- **Type:** Bug

### Summary

Two related problems with the ODDS RANGE popover: it **covers the match cards it
is filtering**, and once open it **cannot be dismissed** - clicking elsewhere on
the page, clicking empty space, and pressing Escape all leave it open.

### Reproduction Steps
1. Open the app and wait for the match list to render.
2. Click the "Odds: All" filter button to open the ODDS RANGE panel.
3. Observe that the panel overlays the first match cards (aspect 1).
4. Click on an unrelated area of the page - for example the "Upcoming Football
   Matches" heading.
5. Click on empty space to the right of the match list.
6. Press the Escape key.
7. Observe after steps 4, 5 and 6 that the panel is still open (aspect 2).

### Expected Result

- The popover must not hide the rows the user is filtering (aspect 1).
- It must dismiss when the user clicks outside it, or presses Escape (aspect 2).

### Observed Result

- Aspect 1: the open panel covers the top rows, so the effect of min/max cannot
  be seen while adjusting. Measured 2 of 104 cards covered at 1600px width.
- Aspect 2: the panel survives an outside click on the heading, a click on empty
  space, and the Escape key - all three verified, panel still displayed after
  each. There is no click-outside handler and no keyboard dismissal, so the only
  way to close it is its own collapse toggle.

### Business Impact

Users are trapped in an overlay: they cannot see the results they are adjusting,
and cannot get back to the list without finding the toggle again. In the main
discovery flow this is more than cosmetic friction - repeated use of the filter
becomes needlessly slow and, at smaller widths, the covered content grows.

### Evidence

- `../screenshots/explore_home.png` - panel open, overlapping Manchester
  Utd-Chelsea and Real Madrid-Barcelona cards.
- `../screenshots/gap_popover_sticky.png` - panel still open after an outside
  click, an empty-space click and Escape.
- Automated probe 2026-10-12: panel open = True after heading click, after
  empty-space click, and after Escape.
- Tracked by `tests/ui_tests/test_regression_popover_overlap.py` (aspect 1;
  strict-xfailed, reports "odds panel covers 2 of 104 match cards").

### Related defect

Covering behaviour is the same family as SportyQAD-010 (filter feedback), but
this one is about the popover's geometry and dismissal, not validation.