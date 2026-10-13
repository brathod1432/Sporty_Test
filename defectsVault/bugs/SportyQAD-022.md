# SportyQAD-022 [UI] — Balance header does not update in real-time after successful bet

**Severity:** High  
**Type:** Bug  
**Status:** Open  
**Reported:** 2026-10-13

---

## Reproduction Steps

1. Log into the app with a valid `USER_ID` (e.g., `candidate-AAAAAAAA`).
2. Note the balance shown in the header (e.g., **€110.00**).
3. Select any odds on an upcoming match.
4. Enter a valid stake (e.g., **€1.00**).
5. Click **PLACE BET** and wait for the success receipt ("Bet placed successfully").
6. **Without refreshing the page**, observe the balance in the header.

## Expected Result

The header balance should immediately reflect the new balance (e.g., **€109.00**) after the receipt appears, matching the server-side state.

## Observed Result

The header balance **remains unchanged** (still shows €110.00) even though:
- The bet was accepted (HTTP 200, receipt shows "Bet placed successfully")
- The API `GET /api/balance` returns the correct new balance (€109.0)
- The bet slip clears correctly

The balance only updates after a **manual page refresh** (F5 or `driver.refresh()`).

## Evidence

| Checkpoint | Balance |
|------------|---------|
| API (before bet) | 110.0 |
| UI Header (before bet) | 110.00 |
| **Place bet via UI** | — |
| API (after bet, immediate) | **109.0** |
| UI Header (after bet, no refresh) | **110.00** ← **STALE** |
| UI Header (after manual refresh) | 109.00 |

The receipt correctly shows `balance: 109` and `currency: "USD"` in the response body, but the React component rendering the header does not re-fetch or update its balance state.

## Business Impact

- **User confusion**: Users see outdated balance after placing bets
- **Trust erosion**: Discrepancy between receipt (shows new balance) and header (shows old)
- **Potential double-betting**: User may think bet failed and place again
- **Spec violation**: Section 4.1 implies real-time balance updates; Section 4.4 receipt shows updated balance

## Root Cause Hypothesis

The header balance is likely fetched once on initial page load (`componentDidMount` / `useEffect` with empty deps) and never subscribes to balance changes. The bet placement succeeds via `POST /api/place-bet`, but no event triggers a balance re-fetch in the header component.

## Suggested Fix

- Emit a `balanceChanged` event after successful `place-bet` response
- Or: make the header balance component subscribe to a global balance store that updates on receipt
- Or: re-fetch `GET /api/balance` in the header after any successful mutation

## Related Defects

- **SportyQAD-018**: Reset balance reports 125.5 but persists 120.0 (balance reporting inconsistency)
- **SportyQAD-021**: Negative stake credits account (balance manipulation)

## Test Coverage

This defect is now covered by automated verification:
- `verify_ui_balance_realtime.py` — places bet via UI, checks header balance before/after without refresh
- Can be integrated into regression suite as `check_balance_updates_realtime_after_bet`