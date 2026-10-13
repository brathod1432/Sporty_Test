# Part A — Manual QA & Test Strategy

> App: `https://qae-assignment-tau.vercel.app/` (single-bet placement flow)
> Spec: `documentation/Feature_Specification.md` · Full case files: `documentation/test_strategy/TC-001..010`
> Author: Brijesh Rathod [bgrathod00@gmail.com]

---

## How I picked these six

This app does one thing that matters: it takes people's money. So the whole
plan follows a single rule:

- **Anything that can move money the wrong way outranks anything that only looks wrong.** Charging bugs first, display bugs second. Always.
- **Cover the full range.** The brief asks for happy paths, negative cases, and boundary conditions — so that's exactly what the six are:
  - Happy paths: TC-001 (bet works), TC-006 (receipt is right)
  - Negative cases: TC-004 (over balance), TC-005 (under minimum)
  - Boundary cases: TC-002 (past match), TC-003 (double submit)
- **Every test earns its place with a risk, not a step count.** If I can't say what goes wrong in real life when this breaks, it doesn't make the list.

---

## Test plan (6 prioritised scenarios)

### TC-001 — Happy-path bet and receipt reconciliation · Critical · UI

**Why this one.** Placing a bet is the only revenue action in the app. Broken
means the product is unusable; working-but-wrong means the user is told one
thing and charged another — that's a dispute waiting to happen. And only the
browser can prove it: the receipt modal, the cleared slip, and the button
states don't exist in any API response.

**Steps.**
1. Read the balance (`GET /api/balance`), write it down as `B`.
2. Open the app, pick a match dated today or later, note the teams and odds.
3. Click an outcome, stake `1.00`, check the slip shows the same odds.
4. Click `Place Bet` once. Read the receipt: Bet ID, match, selection, stake, odds, payout, timestamp, currency.
5. Check payout = stake × odds to two decimals. Home team named first. Timestamp recent.
6. Close the receipt, confirm the slip is empty, re-read the balance.

**Expected.** Receipt complete and correct · payout exact · slip empty · balance exactly `B − 1.00`.

### TC-002 — Past-match bet must be refused · Critical · API

**Why this one.** The spec allows upcoming matches only. A past match is
already played, so a bet on it can never win — yet the server takes the
stake anyway. The user pays for something that can't return a cent, and
nothing in the response warns them.

**Steps.**
1. Read the balance, write it down as `B`.
2. Pick a match with `kickoffDate` earlier than today.
3. `POST /api/place-bet` with that match, `HOME`, `1.00`.
4. Check the status code, the `error` field, and the balance against `B`.

**Expected.** `422` + match-validation error · nothing recorded · balance still `B`.

### TC-003 — Double submission must charge once · Critical · API

**Why this one.** Anyone can double-click Place Bet or retry after a slow
response. And since the app shows no bet history, a double-charged user can't
even tell which charge was the mistake. This has to be checked at the API —
by the time the UI responds, both requests are already gone.

**Steps.**
1. Read the balance, write it down as `B`.
2. Fire two identical `POST /api/place-bet` (same match, `HOME`, `1.00`), no pause between them.
3. Check both responses and the balance against `B`.

**Expected.** First `200`, second `409` · balance down exactly `1.00`, not `2.00`.

### TC-004 — Stake above balance must be refused · Critical · API

**Why this one.** You can't bet money you don't have. An accepted
over-balance stake drives the balance negative, and from there every number
the user sees is built on a wrong one. Costs nothing to run — a refused bet
moves no money.

**Steps.**
1. Read the balance, write it down as `B`.
2. `POST /api/place-bet` with a stake well above it (e.g. `500.00`).
3. Check the status code, the `error` field, and the balance against `B`.

**Expected.** `422` (`insufficient_balance` or `invalid_stake_max` — either refusal counts) · balance still `B`, never negative.

### TC-005 — Stake below minimum must be refused · High · API

**Why this one.** The spec sets a EUR 1.00 minimum. A tiny accepted bet
wouldn't look broken — it would just quietly eat the balance. I test two
stakes (`0.50`, `0.01`) because the spec reads as "at least 1.00" in one
place and "more than 1.00" in another; going below both readings means the
test holds whichever rule the server enforces. Free to run.

**Steps.**
1. Read the balance, write it down as `B`.
2. `POST /api/place-bet` with `0.50`, then again with `0.01`.
3. Check both status codes, both `error` fields, and the balance against `B`.

**Expected.** Both `422 invalid_stake_min` · nothing recorded · balance still `B`.

### TC-006 — Receipt data integrity and payout arithmetic · High · UI

**Why this one.** The receipt is the only record the user keeps, and there's
no bet history to check it against. A USD label in a EUR app or a rounded
payout turns every bet into a potential dispute. High, not Critical: the
money taken is still right — what's wrong is what the user is *told*.

**Steps.**
1. Read the balance, write it down as `B`.
2. Capture the slip before placing: teams in order, selection, stake, odds, payout.
3. Stake `1.00`, place once, capture every receipt field.
4. Compare field by field; multiply stake × odds by hand; check currency, Bet ID, timestamp.

**Expected.** All fields match · payout exact to two decimals · EUR · Bet ID present · timestamp recent.

---

## Execution — top 3 scenarios

I ran the three Critical cases against the live app. Two failed, and both
failures spend real money, so each run was deliberate and is on record:

| # | Scenario | Verdict |
|---|---|---|
| TC-001 | Happy-path bet + receipt | ✅ **Passes** (manual path) — receipt shown, slip cleared, balance down by exactly the stake |
| TC-002 | Past-match bet refused | ❌ **Fails** — server returns `200` and charges **EUR 1.00** instead of `422` → **SportyQAD-011** (Critical) |
| TC-003 | Double submit charges once | ❌ **Fails** — both requests `200`, **EUR 2.00** taken, no `409` guard → **SportyQAD-014** (Critical) |

A few notes on the runs:

- TC-001's automated version (`test_e2e_bet.py`) confirms the Bet ID and the balance movement. The field-by-field reconciliation stays manual — eyes beat assertions on copy and layout.
- TC-002 and TC-003 run behind `--run-bet` precisely because they charge while failing. That's not caution for its own sake; it's EUR 1–2 per run.
- I also spent a few minutes clicking around the flow with no bets placed (list, filters, header icons). That's where the display-side finds below came from.

---

## Defects found

Short form here; full write-ups with screenshots in `defectsVault/`.

- **SportyQAD-011 — [API] Past-match bet accepted and charged · Critical**
  - Repro: note balance `B` → `POST /api/place-bet` on a past match (`HOME`, `1.00`) → re-read balance.
  - Expected `422`, balance `B`. Got `200`, balance `B − 1.00`.
  - Users pay for bets that can't win. Evidence: `defectsVault/bugs/SportyQAD-011.md` (+ gated xfail test).
- **SportyQAD-014 — [API] Double submit charges twice, no 409 guard · Critical**
  - Repro: note `B` → two identical place-bets, no pause → re-read balance.
  - Expected first `200`, second `409`, `B − 1.00`. Got both `200`, `B − 2.00`.
  - Any double-click or retry double-charges, with no history to spot it. Evidence: `defectsVault/bugs/SportyQAD-014.md` (+ gated xfail test).
- **SportyQAD-001 — [UI] Past matches listed first under "Upcoming" · High**
  - Most of the catalog is past-dated, shown under an "Upcoming" heading. This is the display-side root of the TC-002 problem. Evidence: `SportyQAD-001.md`, `explore_home.png`.
- **SportyQAD-012 — [API] Receipt says USD, everything else is EUR · Medium**
  - The only record the user keeps has the wrong currency. Dispute risk on every bet. Evidence: `SportyQAD-012.md`, live receipt body.
- **SportyQAD-022 — [UI] Header balance stale after a successful bet · High**
  - Receipt and API show the deduction; the header doesn't until refresh. Users see money they no longer have. Evidence: `SportyQAD-022.md` (+ gated xfail test).

And to be clear about scoring: bug count isn't the point — report quality is.
The two Critical money defects are the high-impact finds, each with steps,
expected-vs-actual, impact, and evidence.

---

## What didn't make the six (on purpose)

- **TC-005, TC-006 are High, not Critical.** The minimum-stake rule already holds on API and UI; receipt errors misinform without mischarging.
- **Filters, loading and empty states** are visual/temporal judgement calls. Automating them would freeze today's layout into tests, not the rule behind it.
- **The negative-stake hole (SportyQAD-021, Critical)** turned up while probing TC-004's neighbours. It's filed in the vault with its own write-up — it deserved that, not a borrowed slot in this plan.
