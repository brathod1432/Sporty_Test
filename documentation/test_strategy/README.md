# Test Strategy - Sports Betting QA

> App: `https://qae-assignment-tau.vercel.app/`
> Author: Brijesh Rathod [bgrathod00@gmail.com]
> 10 test cases: the top 6 first, then 4 optional. One file per case in this folder.

## Top 6 - prioritised

| # | ID | Test case | Priority | Area | Cost | Result today |
|---|---|---|---|---|---|---|
| 1 | [TC-001](TC-001-happy-path-bet-receipt.md) | Happy-path bet and receipt reconciliation | Critical | UI | Costs money | **Check manually** - not automated |
| 2 | [TC-002](TC-002-past-match-bet-refused.md) | Past-match bet must be refused | Critical | REST API | Costs money while failing | **Fails** - bug SportyQAD-011 |
| 3 | [TC-003](TC-003-double-submit-single-charge.md) | Double submission must charge once | Critical | REST API | Costs money while failing | **Fails** - bug SportyQAD-014 |
| 4 | [TC-004](TC-004-stake-above-balance-refused.md) | Stake above balance must be refused | Critical | REST API | Free | Passes |
| 5 | [TC-006](TC-006-receipt-data-integrity.md) | Receipt data integrity and payout arithmetic | High | UI | Costs money | **Check manually** - not automated |
| 6 | [TC-008](TC-008-endpoint-user-context-boundary.md) | Endpoint user-context boundary | High | REST API | Free | Passes |

## Optional - recommended, good to have

| # | ID | Test case | Priority | Area | Cost | Result today |
|---|---|---|---|---|---|---|
| 7 | [TC-005](TC-005-stake-below-minimum-refused.md) | Stake below minimum must be refused | High | REST API | Free | Passes |
| 8 | [TC-009](TC-009-team-ordering-match-data.md) | Match card team ordering and data | Medium | UI | Free | Odds pass, team order not tested |
| 9 | [TC-010](TC-010-incomplete-slip-blocks-placement.md) | Placement blocked on an incomplete slip | Medium | UI | Free | Passes |
| 10 | [TC-007](TC-007-reset-reports-persisted-balance.md) | Reset must report the balance it restores | Medium | REST API | Free | **Fails** - bug SportyQAD-018 |

## Why these 6

1. **They move money.** A wrong balance, receipt or charge becomes a customer dispute.
2. **They fail silently.** A bet accepted that should have been refused, or a double
   charge, is found by the customer weeks later with no way to correct it.
3. **They cannot be proven by the API alone.** TC-001 and TC-006 live only in the
   browser - the receipt modal and bet slip do not exist in any API response.

TC-005 is High but optional because the minimum-stake rule is already proven working
by both the API and UI tests. The dangerous gap in that same area - a negative stake
being **paid out** - is bug SportyQAD-021 (Critical), written up in
`defectsVault/bugs/SportyQAD-021.md`.

**New finding:** **SportyQAD-022 (High)** — Balance header does not update in real-time after a successful bet via UI. The bet succeeds, receipt and API show the new balance, but the header stays stale until manual refresh. Covered by `check_balance_updates_realtime_after_bet` (strict xfail, gated).

## Two things to know

- **Costs money** means the test spends real balance. Run those by hand and record the
  result. The free ones run under plain `pytest` (money tests skip without `--run-bet`)
  and never move the balance — confirm with `GET /api/balance` before and after.
- **Never assume the opening balance.** This account holds **EUR 120.00**, not the
  EUR 125.50 named in the brief. Reset works, but it reports 125.50 while restoring
  120.00 - see TC-007 and bug SportyQAD-018. Always read `GET /api/balance`.