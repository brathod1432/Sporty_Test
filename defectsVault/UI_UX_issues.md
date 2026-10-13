# UI/UX Check - Sports Betting QA (exploratory, 2026-10-12)

> Method: headless Chrome 1600x900 via `testfunctions/ui_helper.py` + `tests/ui_tests/explore_ui.py`.
> Auth: real `USER_ID` from `.env`. **No bet was placed by these scripts**
> (`place_bet` is not even imported in `explore_ui.py` - verifiable).
> Evidence: `screenshots/explore_home.png`, inventory dumps in run logs.
>
> Corrections applied 2026-10-12 after the SportyQAD-018 and SportyQAD-021 findings.
> U1 is now answered with proof rather than left as a question.

## Balance incident (read first)

- 13:05 UTC: `GET /api/balance` -> **EUR 125.50**.
- 13:16 UTC, during the exploratory runs: UI and API both show **EUR 124.50**
  (a drop of exactly EUR 1.00, the minimum stake).
- These scripts **never called `place_bet`** and never submitted any form. The single
  click performed (`select_outcome(0)`) demonstrably hit the **"Odds: All" filter
  button** - its class contains "odd", which matched the first selector. Proven by
  the screenshot: the odds-filter dropdown is open and the bet slip is **empty**.
- Likely cause: **concurrent use of this shared candidate ID**, not this run.
- **Correction:** the EUR 125.50 figure came from the reset response, which reports
  the wrong value. The account actually holds **EUR 120.00** and `POST
  /api/reset-balance` restores to 120.00 while reporting 125.50
  (SportyQAD-018). Treat any 125.50 figure in these notes as unverified and read
  `GET /api/balance` instead.
- Action: call `POST /api/reset-balance` before a scored block. It works; only the
  number it reports back is wrong.

## What the UI looks like (verified)

- Header (red): logo "Sports Betting QA", `Balance: EUR X` pill, user avatar icon.
- Main: "Upcoming Football Matches" + "Showing 103 matches"; filters `Date: All`,
  `Odds: All`; match cards (competition, PAST badge, date, teams, 1/X/2 odds buttons).
- Right: fixed `Bet Slip` (badge 0, balance repeated), empty state
  "Select odds to place a bet".
- Footer: "Version 1.0.0". Tab title: "Sports Betting QA". Zero JS console errors.

## Issues found

### U1 - All matches badged PAST under "Upcoming Football Matches" (High)

Every card (Man Utd-Chelsea, Real Madrid-Barcelona, and so on) shows a `PAST` badge
with Feb/Mar dates, yet the section promises *upcoming / pre-match only*
(spec Section 1 and Section 3).

**This was logged as an open question and is now answered.** The original note asked
whether users "may or may not be able to wager on already-played events". They can.
A bet on a past-date match is accepted with HTTP `200` and the stake is charged.
Filed as **SportyQAD-011** (Critical), reproduced live, tracked by a strict-xfailed
test. The catalog is stale test data, not inverted badge logic - the badge itself is
date-driven and correct.

### U2 - No kickoff TIME shown, only date (Medium)

Cards show "Fri 27 Feb" plus a `-` placeholder where a time would sit. Spec Section
2.1 requires a kickoff date/time label. The API only carries `kickoffDate`
(YYYY-MM-DD), so the UI invents a `-` slot. Decide: drop the `-` slot, or add time to
the API and UI. As it stands it reads as missing data. Filed as **SportyQAD-002**.

### U3 - Balance flashes EUR 0.00 on load (Low)

First paint (spinner state) shows `Balance: EUR 0.00` in the header and the slip
before the real value loads ("Showing 0 matches" likewise). A user glancing early
sees an empty account. Fix: skeleton or blank the balance until loaded, instead of
0.00. Filed as **SportyQAD-003**.

### U4 - Odds-filter popover covers match cards (Medium)

Opening "Odds: All" overlays the first match cards (see
`screenshots/gap_popover_sticky.png`). Standard dropdown behaviour, but at 1600px
wide it hides the very rows being filtered. Consider a sidebar or docked filter
panel, or auto-close on Apply. Filed as **SportyQAD-004**.

### U5 - Around 40 empty-text buttons (Low, a11y)

351 buttons found; roughly 40 have empty text (slider thumbs, icon buttons). Icon
buttons rely on Material-Icons ligature text (`calendar_today`, `expand_more`) -
fine visually, but the real `aria-label`s need verifying with a screen reader. Test
hook suggestion: add `data-testid` attributes to the odds buttons, stake input,
Place Bet and modals. Stable selectors beat class-fragment matching, which my own
run proved the hard way. Filed as **SportyQAD-005**.

### Positive notes (also worth recording)

- Header balance and slip balance always agree.
- Empty-slip copy is clear; slip badge count present.
- Odds render exactly as the API returns (2.45 / 3.10 / 2.80 spot-checked visually).
- No console errors on load or after interaction.

## Selenium UI test strategy (proposal)

Stay in `tests/ui_tests/`, stack Selenium 4.51 + pytest + `testfunctions/ui_helper.py`
(driver factory, explicit waits, `wait_for_content` for the SPA async render - plain
readyState is NOT enough, proven by run 1 seeing 0 buttons).

1. **E2E happy path (the 1 required UI test):** open app -> wait content ->
   select first-match HOME -> set stake EUR 1 (minimum, conserves balance) ->
   Place Bet -> assert receipt modal (Bet ID, match, stake, odds, payout,
   timestamp) -> assert balance decreased by stake -> close receipt ->
   assert slip cleared. Mitigate flakiness: reset the balance via API first, assert
   receipt values against the pre-placement capture, never hardcode odds.
2. **Keep manual:** filter combinations, modal copy and UX (U1-U5 above), loading
   states, responsive (out of scope per spec), cross-browser.
3. **Conventions:** `data-testid` lobbying (see U5); screenshots on failure into
   `defectsVault/screenshots/`; never run the UI bet test in parallel for one user
   (409 in-progress); headless for CI, headed for local debugging.