## [SportyQAD-003][UI] Balance flashes EUR 0.00 on first paint

- **Severity:** Low
- **Type:** Bug

### Reproduction Steps
1. Open the app fresh (cold load) with a funded, non-zero balance.
2. Observe the header pill and bet slip before content renders (~1s spinner).

### Expected Result
Balance hidden/skeleton until loaded.

### Observed Result
Header and slip both display `Balance: EUR 0.00` with "Showing 0 matches".

### Business Impact
A user glancing early believes their account is empty,
causing needless panic and support contacts.

### Evidence
`../screenshots/loading_state.png` (spinner + EUR 0.00 in
both spots; the account held a real, non-zero balance at the time).
