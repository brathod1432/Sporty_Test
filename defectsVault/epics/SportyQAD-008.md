## [SportyQAD-008][UI][Improvement] Win-rate and betting statistics

- **Severity:** Low
- **Type:** Epic

### Reproduction Steps
1. Look for any statistics in the app: per-user win rate, profit/loss, or
   per-match outcome hints.
2. Observe: none exist - header shows balance only, cards show odds only.

### Expected Result
At minimum a personal stats strip (bets placed, won, win rate, net profit) once history exists; ideally per-match context (e.g. home-win rate) to inform picks.

### Observed Result
No numbers beyond balance and raw odds.

### Business Impact
Stats keep bettors engaged and coming back; without them
the product is a bare transaction form with no reason to prefer it.

### Evidence
`../screenshots/explore_home.png` (header: balance
only). Feasibility: personal stats depend on SportyQAD-007 history; match-level
rates would need a data feed - phase it: personal stats first, market stats later.
