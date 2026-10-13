## [SportyQAD-011][API] Bet on past-date match accepted and charged (upcoming-only rule not enforced)

- **Severity:** Critical
- **Type:** Bug

### Reproduction Steps
1. Read balance via `GET /api/balance` (was 123.50).
2. `POST /api/place-bet` with a past-date `matchId` (`premier-league-manutd-chelsea`,
   kickoff 2026-02-27), selection HOME, stake 1.00, valid `x-user-id`.
3. Read status/body; re-read balance.

### Expected Result
422 rejection (most likely `invalid_match`), balance untouched: spec Section 1/Section 3 allow upcoming/pre-match events only.

### Observed Result
**200 "Bet placed successfully"**, odds 2.45, payout 2.45, balance deducted to 122.50. The server enforces no date rule at all.

### Business Impact
Users can (and did, in testing) wager on long-played events -
a compliance-grade failure: settled-in-the-past fixtures must never accept stakes.

### Evidence
pytest `test_past_match_rejected` (strict-xfailed, fails with full 200
receipt dump); live receipt body captured 2026-10-12 13:47 UTC.
