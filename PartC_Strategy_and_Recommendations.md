# Part C — Strategy & Recommendations

> App: `https://qae-assignment-tau.vercel.app/`
> Author: Brijesh Rathod [bgrathod00@gmail.com]

---

## Why these 2 tests, and not the others

**E2E UI — happy-path bet (`test1_place_bet_happy_path`).**

- It's the single revenue action. If it breaks, the product is dead; if it miscalculates, every bet is a dispute.
- It's the **only flow the API can't touch** — receipt modal, cleared slip, button states live purely in the browser.
- One test, maximum signal. Gated and self-resetting, so it proves the journey without becoming a standing charge.

**API — below-minimum stakes (`test_below_minimum_rejected`).**

- The cheapest test I own: milliseconds, zero charge, zero flakiness.
- It settles the spec's own argument with itself (1.00 vs 1.01) — and that answer sets the E2E test's stake, so this test quietly holds up the other one.
- Boundary rules beat enum checks for value per millisecond. I picked it over past-match, bad-selection and over-balance for exactly that reason — and SportyQAD-021 (a negative stake being *paid out*) later showed why boundaries are where servers actually break.

The pair works because they don't overlap: each covers what the other can't
reach, and both assert on the **balance**, so neither can pass while silently
wrong.

---

## What stays manual, and why

- **Receipt and error-modal copy.** Every run costs money, and a person reads wording faster than code asserts it. Automation proves the receipt *exists*; eyes prove it *reads right*.
- **Filters, loading states, list rendering.** Visual and temporal judgement. Tests would encode today's layout instead of the rule — breaking on every redesign while proving nothing.
- **Past-match acceptance.** A probe that fails honestly until the server refuses. Green over a Critical money bug would be dishonest; the xfail *is* the position.

---

## If this scales — my top 3

1. **Per-test users + a reset fixture.** The shared account is the suite's weakest structural point: drift has already faked failures, and the 409 guard can't be tested without colliding with yourself. One user per worker, reset on setup, balance asserted on teardown — and the money tests become CI-safe.
2. **A `data-testid` contract with the frontend.** Every flaky moment here traces to class-fragment or text matching (a filter button stealing an odds click, an empty-text Apply). Stable hooks on odds buttons, stake input, Place Bet and modals kill that whole category at the source, for almost zero frontend cost.
3. **A spec-first validation matrix, reviewed each release.** The 1.00-vs-1.01 minimum, the unenforced past-match rule, the USD receipt — all found live, none in the docs. A small table (field, valid range, error code) checked against the OpenAPI spec every release turns surprises into generated tests. The negative-stake hole is the receipt showing the table pays for itself.

---

## Security gaps — filed, not built here

Authentication lives on the app's server, so no test code could add it. What
I did instead is file it as two Epics:

- **SportyQAD-019 — no authentication or session management.** No login, no password, no session, no logout, no 2FA. The `x-user-id` header is the whole of authentication: anyone holding it owns the wallet permanently, with no revocation and no expiry. Fix direction is a real credential store, expiring sessions, server-side logout, and 2FA as an option.
- **SportyQAD-020 — the user id travels in the URL.** Since the id *is* the credential, `?user-id=` writes it into browser history, server/proxy logs, `Referer` headers and screenshots — and with no revocation (019), one log line is a permanent compromise. Fixable independently: move it into a header or `HttpOnly` cookie even before any login flow exists.

Why they matter to this strategy: per-test users (recommendation 1) only work
if accounts can be issued and revoked — which needs 019 fixed first. And
every screenshot in this repo was taken with the credential in the address
bar, which is 020 demonstrating itself.

---

## If the app scales — 10M users, 1M online at once

Everything below comes from defects this repo already proves. Today they cost
euros; at a million concurrent users they cost the business.

- **Bets must go through once, even when tapped twice.** QAD-014 shows two simultaneous bets both succeeding — no guard at all. On a quiet test account that's EUR 2. On match day with a million people hammering Place Bet, it's systematic double-charging. Every bet needs a fingerprint: same fingerprint twice, one bet charged.
- **The balance can't be read-then-updated.** Right now the app checks the balance and deducts it as separate steps, and two bets landing together can both pass the check. At scale that race fires constantly. The deduction has to happen in one indivisible move — "take the stake only if it's there" — or overdrafts become routine.
- **Stop trusting the request.** QAD-021's money printer needs a single curl command. QAD-011 accepts bets that can't win. With ten million users, someone automates both on day one. The server has to enforce every limit itself — stake bounds, per-user speed limits, and alarms for impossible patterns like balances going *up* after a bet.
- **The login system won't survive the public.** No sessions, no logout, and the password-equivalent sitting in the URL (019 + 020). At this scale that means credentials spilling into logs and screenshots by the thousand, with no way to cut any of them off. Real logins with expiry and revocation come before everything else — including the per-test users in my top 3.
- **The match list needs growing up.** 103 matches load fine today. Ten million users means more matches, live odds, and phones on bad connections: pages of results instead of everything at once, filtering done by the server, match data cached close to the user.
- **Keep a receipt for every bet.** There is no bet history today, so a double-charged user can't even point at the wrong charge. Multiply that by a million users and support drowns with no data to answer tickets from. A permanent per-user bet record isn't a nice feature — it's how disputes get settled.
- **Remove the free-money button before launch.** The reset endpoint hands out funds on demand and already misreports what it did (QAD-018). Useful in testing, catastrophic in production. It shouldn't be hidden — it shouldn't ship.
- **Watch the money, not just the machines.** Server-uptime dashboards won't catch silent double-charges or a bypassed check. The alarms that matter are business ones: sudden spikes in failed bets, the duplicate-blocker going quiet, balances moving the wrong way. This vault is basically the starter list.

---

**The one-liner:** automate the money boundaries machines check best, keep human
eyes on what humans judge best, and fix the shared account first — everything
after that depends on trusting the balance.
