## [SportyQAD-007][UI][Improvement] "My Bets" button showing placed-bet history

- **Severity:** Medium
- **Type:** Epic

### Reproduction Steps
1. Place a bet (or imagine one): receipt modal shows Bet ID, match, stake, odds,
   payout, timestamp.
2. Close the receipt (spec: returns to main flow "without active selection").
3. Try to find that bet again anywhere in the UI.
4. Observe: it is gone - no history page, panel, or button exists.

### Expected Result
A "My Bets" button/panel listing placed bets (match, selection, stake, odds, payout, timestamp, status) so users can verify wagers.

### Observed Result
The receipt modal is the only record; once closed, the bet is unverifiable in the UI.

### Business Impact
Users cannot audit their own money movements - a trust and
support-ticket risk for any real-money product.

### Evidence
`../screenshots/explore_home.png` (no history control
in header, slip, or footer). Feasibility: bigger lift - the OpenAPI spec has no
history endpoint, so this needs a new `GET` endpoint plus the UI; worth speccing
early.
