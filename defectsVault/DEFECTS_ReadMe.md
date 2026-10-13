# Defects - Sporty Betting QA

> How this vault is organized: this file holds **only the high-level summary table**.
> Full details live per defect under `bugs/` (Type Bug) and `epics/` (Type Epic).
> Screenshots: `screenshots/`. Method notes: `UI_UX_issues.md`.
> Explored 2026-10-12, headless Chrome 1600x900, Selenium 4.51 - no bet was placed.

## Severity scale (scored by QA)

`Critical` money lost / data corrupt / app unusable - `High` core flow wrong or misleading -
`Medium` feature degraded or confusing - `Low` cosmetic / edge / a11y nit.
(Type: `Bug` = broken behavior, `Epic` = improvement proposal. Fix scheduling lives elsewhere.)

## Summary

| Defect ID | Type | Severity | Defect Title | Comments |
|---|---|---|---|---|
| [SportyQAD-001](bugs/SportyQAD-001.md) | Bug | High | [UI] Past matches listed first under "Upcoming Football Matches" | Screenshot: explore_home.png; 58 of 78 catalog dates past |
| [SportyQAD-002](bugs/SportyQAD-002.md) | Bug | Medium | [UI] No kickoff time shown, only date plus "-" placeholder | Screenshot: explore_home.png |
| [SportyQAD-003](bugs/SportyQAD-003.md) | Bug | Low | [UI] Balance flashes EUR 0.00 on first paint | Screenshot: loading_state.png; true balance EUR 124.50 |
| [SportyQAD-004](bugs/SportyQAD-004.md) | Bug | Medium | [UI] Odds-filter popover covers the match cards and cannot be dismissed | Screenshots: explore_home.png, gap_popover_sticky.png |
| [SportyQAD-005](bugs/SportyQAD-005.md) | Bug | Low | [UI] Empty-text buttons, icon buttons lack discernible names | 351 buttons, ~40 empty-text |
| [SportyQAD-006](epics/SportyQAD-006.md) | Epic | Medium | [UI][Improvement] Sort and filter matches by time frame, country/league, team, upcoming/past | Proposal; no UI exists today |
| [SportyQAD-007](epics/SportyQAD-007.md) | Epic | Medium | [UI][Improvement] "My Bets" button showing placed-bet history | Proposal; needs new API endpoint |
| [SportyQAD-008](epics/SportyQAD-008.md) | Epic | Low | [UI][Improvement] Win-rate and betting statistics | Proposal; depends on bet history |
| [SportyQAD-009](bugs/SportyQAD-009.md) | Bug | Medium | [UI] Profile icon does nothing - no profile, history, or wallet details reachable | Screenshot: profile_click2.png |
| [SportyQAD-010](bugs/SportyQAD-010.md) | Bug | Medium | [UI] Invalid odds range silently applied - no rejection, blank list, stale counter | Screenshot: gap_badrange.png; spec §2.6 |
| [SportyQAD-011](bugs/SportyQAD-011.md) | Bug | Critical | [API] Bet on past-date match accepted and charged (upcoming-only rule not enforced) | Strict-xfailed test; EUR 1.00 charged live 2026-10-12 |
| [SportyQAD-012](bugs/SportyQAD-012.md) | Bug | Medium | [API] place-bet receipt returns currency USD, everything else is EUR | Live receipt body 2026-10-12 |
| [SportyQAD-013](bugs/SportyQAD-013.md) | Bug | Medium | [UI] PLACE BET button not rendered at all when no odds selected (absent, not disabled) | Screenshot: gap_pb_no_stake.png; DOM probe |
| [SportyQAD-014](bugs/SportyQAD-014.md) | Bug | Critical | [API] Double submit charges twice - 409 concurrency guard not implemented | Strict-xfailed; EUR 2.00 charged live 2026-10-12 |
| [SportyQAD-015](bugs/SportyQAD-015.md) | Bug | Medium | [UI] Match counter stays at the unfiltered total after filtering | Screenshot: gap_dateapplied.png; strict-xfailed |
| [SportyQAD-016](epics/SportyQAD-016.md) | Epic | Medium | [UI][Improvement] Historical results view for completed matches | Exploratory (Selenium); gap, not a defect - no scores or statistics, API has no result fields |
| [SportyQAD-017](epics/SportyQAD-017.md) | Epic | Medium | [UI][Improvement] Search and "no results" handling for the match list | Exploratory (Selenium); gap, not a defect - no search control, blank empty state |
| [SportyQAD-018](bugs/SportyQAD-018.md) | Bug | Medium | [API] Reset balance reports the wrong balance | Strict-xfailed; reports 125.5, actually restores 120.0 |
| [SportyQAD-019](epics/SportyQAD-019.md) | Epic | High | [API][Improvement] No authentication or session management | Auth probe; gap - no login, logout, session or revocation |
| [SportyQAD-020](epics/SportyQAD-020.md) | Epic | High | [API][Improvement] The user id - the only credential - travels in the URL | Auth probe; leak - id in the query string, so in history, logs and Referer |
| [SportyQAD-021](bugs/SportyQAD-021.md) | Bug | Critical | [API] Negative stake accepted - the server pays the customer | Strict-xfailed; stake -1 credited +1.00, -2.50 credited +2.50; unbounded money printer, no lower bound on stake |
| [SportyQAD-022](bugs/SportyQAD-022.md) | Bug | High | [UI] Balance header does not update in real-time after successful bet | Bet placed via UI, receipt shows new balance, API confirms, but header stays stale until manual refresh |


