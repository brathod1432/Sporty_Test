# Sporty_Test — Sports Betting App Test Harness

> **App:** `https://qae-assignment-tau.vercel.app/` · **Author:** Brijesh Rathod [bgrathod00@gmail.com]

Automation suite for the Sporty single-bet placement flow: **42 tests** (16 API checks, 1 end-to-end UI journey, 25 UI regression checks) built on **pytest + requests + Selenium**.

**Latest free run: 28 passed · 5 skipped · 9 xfailed · 0 failed** (3m42s). The free run spends €0.

---

## The assignment deliverables

| Part | File | Contents |
|---|---|---|
| A — Manual QA & Test Strategy | [`PartA_ManualQA_and_Test_Strategy.md`](PartA_ManualQA_and_Test_Strategy.md) | 6 prioritised scenarios with risk rationale, top-3 execution results |
| B — Automation | [`PartB_Automation.md`](PartB_Automation.md) | Framework design, the 2 showcase tests, directory guide, reviewer run guide |
| C — Strategy & Recommendations | [`PartC_Strategy_and_Recommendations.md`](PartC_Strategy_and_Recommendations.md) | Why these 2 tests, what stays manual, top-3 scale-up recommendations |
| — Test case library | [`documentation/test_strategy/`](documentation/test_strategy/) | 10 case files (TC-001…TC-010) with priority, risk, steps, expected, cost |
| — Defect reports | [`defectsVault/`](defectsVault/) | 22 filed defects (15 Bugs + 7 Epics) with reproduction steps and evidence |
| — Brief + spec | [`documentation/`](documentation/) | Assignment and feature spec as PDFs, plus the OpenAPI capture |

---

## Quick start

**Prerequisites:** Python 3.11+ (3.11.9 used) · Chrome (Selenium fetches its own driver).

```cmd
git clone https://github.com/brathod1432/Sporty_Test.git
cd Sporty_Test

python -m venv .venv
.venv\Scripts\activate
pip install -r python311_requirements.txt

copy .env.example .env
```

Edit `.env` and set **`USER_ID`** to your 22-character test account id. Everything else has a working default.

**Verify:**

```cmd
python libs\logger.py                          # logger self-test
.venv\Scripts\python -m pytest tests\ --collect-only -q   # lists 42 tests
```

---

## Running the suite

### Free run — the default, spends €0

```cmd
.venv\Scripts\python -m pytest tests\ -v
```

**Prove it costs nothing:** read `GET /api/balance` before and after. Every money-moving test is gated behind `--run-bet`, so a plain run cannot spend.

### Gated run — spends real balance, approval only

```cmd
.venv\Scripts\python -m pytest tests\ -v --run-bet
```

Runs the 5 money tests, each resetting the balance in a `finally` block. Never run this in CI.

### Without pytest — every file is also a script

```cmd
.venv\Scripts\python tests\api_tests\test_api_business_rules.py -td check_below_minimum_rejected
.venv\Scripts\python tests\api_tests\test_api_business_rules.py -td check_a,check_b   # several
```

No flag runs everything. `-td` picks by name. `-x` stops at the first failure.

### Run a single test

```cmd
.venv\Scripts\python -m pytest tests\api_tests\test_api_business_rules.py::test_below_minimum_rejected -v
```

---

## The two showcase tests

**E2E UI — `test1_place_bet_happy_path`** (`tests/ui_tests/test_e2e_bet.py`)
The one revenue action, proven in a real browser: select outcome → stake → place → receipt → balance drop. It's the only flow no API test can reach, because the receipt modal, the cleared slip and the button states exist nowhere outside the browser. Gated — it spends €1.00 and resets on the way out.

**API — `test_below_minimum_rejected`** (`tests/api_tests/test_api_business_rules.py`)
Sends stakes of `0.50` and `0.01` at `POST /api/place-bet`, demands `422 invalid_stake_min`, and asserts nothing was charged. Milliseconds, zero cost, zero flakiness — and it pins the boundary the spec states two different ways (`at least 1.00` in one place, `more than 1.00` in another), which is also what sets the stake the E2E test uses.

Both assert on the **balance**, not just the status code. Reasoning in [`PartC_Strategy_and_Recommendations.md`](PartC_Strategy_and_Recommendations.md).

---

## Test inventory

### Gated behind `--run-bet` (5)

| Test | Defect | Why it costs |
|---|---|---|
| `test1_place_bet_happy_path` | — | Places a real €1.00 bet |
| `test_past_match_rejected` | SportyQAD-011 | Charges €1.00 while failing |
| `test_double_submit_rejected` | SportyQAD-014 | Charges €2.00 while failing |
| `test_negative_stake_rejected` | SportyQAD-021 | **Adds** to the balance while failing |
| `test_balance_updates_realtime_after_bet` | SportyQAD-022 | Needs a placed bet to observe the stale header |

### Expected failures — strict xfails tracking filed defects

These are not broken tests. Each is a confirmed, filed bug held open with `@pytest.mark.xfail(strict=True)`, so it flips to a **failure** (not a silent pass) the day the server-side fix lands.

The table below covers all 11 strict-xfailed tests. Eight of them run in a free run; the other three (QAD-011, QAD-014, QAD-021) are gated, so they only appear once you pass `--run-bet`.

| Defect | Severity | Test(s) | What the app does wrong |
|---|---|---|---|
| **SportyQAD-011** | Critical | `test_past_match_rejected` | Bets on completed matches return `200` and charge — the upcoming-only rule is never enforced |
| **SportyQAD-014** | Critical | `test_double_submit_rejected` | Two concurrent bets both succeed; no `409` guard, so the user is charged twice |
| **SportyQAD-021** | Critical | `test_negative_stake_rejected` | `stake: -1` returns `200` and **credits the account**. Unbounded — every other stake value is correctly refused |
| **SportyQAD-018** | Medium | `test_reset_reports_actual_balance` | Reset reports `125.5` while actually restoring `120.0` |
| **SportyQAD-002** | Medium | `test_tc009_kickoff_time` | Cards show a bare `-` instead of kickoff time |
| **SportyQAD-015** | Medium | `test_match_counter_updates` | After filtering, the counter still shows the unfiltered total |
| **SportyQAD-010** | Medium | `test_invalid_range_rejected`, `test_empty_state` | An inverted odds range is silently coerced to `10.00-10.00`; zero matches renders blank with no explanation |
| **SportyQAD-004** | Medium | `test_popover_does_not_cover_cards`, `test_popover_dismisses_on_outside_click` | The odds popover covers the cards it is filtering, and ignores outside-click and Escape |
| **SportyQAD-009** | Medium | `test_profile_icon_opens_details` | The profile icon has no click handler at all |

A 9th xfail exists but is **not** a defect: `test_loading_state` is marked `xfail(strict=False)` because the sub-second "Placing…" label isn't reliably capturable by the in-page recorder. It's a flaky-timing test, documented rather than hidden.

### Also filed, deliberately untested

`SportyQAD-019` (no authentication or session management) and `SportyQAD-020` (the user id — the only credential — travels in the URL query string) are filed as **High** Epics. No test could add authentication to the app's server, so they're reported rather than automated. See [`PartC`](PartC_Strategy_and_Recommendations.md) for why 019 has to be fixed before per-test users are practical.

Full write-ups with evidence: [`defectsVault/DEFECTS_ReadMe.md`](defectsVault/DEFECTS_ReadMe.md).

---

## Project structure

```
Sporty_Test/
├── PartA_ManualQA_and_Test_Strategy.md   # Deliverable A
├── PartB_Automation.md                   # Deliverable B
├── PartC_Strategy_and_Recommendations.md # Deliverable C
├── README.md                             # This file
├── conftest.py                           # The --run-bet flag. One place, whole suite.
├── python311_requirements.txt            # Pinned dependencies
├── pyrightconfig.json                    # Type-checker config
├── package.json                          # mermaid-cli only, to render the Part B diagram
│
├── libs/                                 # Plumbing. Never contains tests.
│   ├── logger.py                         # get_logger(name) -> coloured console + file logs
│   ├── rest_helper.py                    # Typed REST client: GET/POST/PUT/PATCH/DELETE + dispatcher
│   ├── GeneralUtils.py                   # Small shared utilities
│   └── testInitialization.py             # Dual runner: Configure() / testSuite() / run()
│
├── libs/testfunctions/                   # Named verbs. This is where the work happens.
│   ├── api_helper.py                     # Auth, raw endpoint calls, require_balance() guard
│   ├── api_functions.py                  # Scenario verbs: attempt_bet, double_submit, restore_balance
│   ├── rest_api.py                       # One typed helper per endpoint, each checking expected codes
│   ├── assert_functions.py               # assert_status, assert_error_code, assert_balance_unchanged
│   ├── data_functions.py                 # Match/stake/outcome pickers — no hardcoded ids or dates
│   ├── ui_helper.py                      # Selenium driver, waits, screenshots. UI is a context manager.
│   ├── ui_functions.py                   # Browser steps: select odds, enter stake, submit, await receipt
│   └── modal_functions.py                # Receipt and error-modal handling
│
├── tests/                                # Assertions only.
│   ├── api_tests/
│   │   └── test_api_business_rules.py    # 16 API checks — money rules, protocol, endpoint contracts
│   └── ui_tests/
│       ├── test_e2e_bet.py               # The gated E2E happy-path journey
│       └── test_ui_regression.py         # 25 UI regression checks
│
├── documentation/
│   ├── HQA_Take_Home_Task.pdf            # The assignment brief
│   ├── Feature_Specification.pdf         # The feature spec
│   ├── API_OpenAPI.json                  # Captured OpenAPI document
│   ├── UI_UX_issues.md                   # Exploratory method notes
│   └── test_strategy/                    # TC-001…TC-010 case files + summary table
│
└── defectsVault/
    ├── DEFECTS_ReadMe.md                 # Master table — 22 entries with links
    ├── UI_UX_issues.md                   # Exploratory method notes
    ├── bugs/                             # 15 bug files (QAD-001…005, 009…015, 018, 021, 022)
    ├── epics/                            # 7 epic files (QAD-006…008, 016, 017, 019, 020)
    └── screenshots/                      # 15 PNGs attached as evidence
```

The rule the whole codebase follows: **tests state intentions, helpers do the work.** A test says `attempt_bet(...)` and asserts on the outcome — it never builds an HTTP request by hand. If you find raw `requests` calls inside a test file, that's a smell: push them down into `libs/testfunctions/`.

---

## Environment variables (`.env`)

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `USER_ID` | **Yes** | — | 22-character test account id, sent as the `x-user-id` header |
| `BASE_URL` | No | `https://qae-assignment-tau.vercel.app` | API base |
| `APP_URL` | No | `https://qae-assignment-tau.vercel.app/?user-id=${USER_ID}` | Web app |
| `API_DOCS_URL` | No | `https://qae-assignment-tau.vercel.app/api/docs` | Swagger UI |
| `DEFAULT_STAKE` | No | `1.01` | Stake used by the tests (one cent above the minimum) |
| `REQUEST_TIMEOUT` | No | `30` | HTTP timeout, seconds |

`.env` is **not** in `.gitignore` in this repo — it's simply never committed. `git add` it by accident and the account id lands in public history. Add it to your local `.git/info/exclude` if you want the protection without touching the tracked file.

---

## Two things to know before you trust a green run

**1. Never assume the opening balance.** The brief says the account starts at €125.50. It doesn't — it holds **€120.00**, and the reset endpoint reports `125.5` while actually restoring `120.0` (that's SportyQAD-018). Every check reads the live balance via `GET /api/balance` instead of hardcoding a figure.

**2. The account is shared, so the balance moves on its own.** It's not private to you, and it drifts mid-run. This has produced false failures where a refused request appeared to have been charged. The rule the suite follows: **balance moved? Re-run before you file a defect.** Only a repeat failure is a defect.

---

## Adding a test

1. Write the logic in a `check_*` function — it's shared by both runners.
2. Add a one-line `test_*` pytest wrapper next to it and register the check in `testSuite(...)`.
3. If it moves money, gate it: `setattr(fn, "requires", ["--run-bet"])` for the direct runner plus `@pytest.mark.skipif` for pytest, and reset the balance in a `finally`.
4. If a bug is open, `@pytest.mark.xfail(strict=True, reason="SportyQAD-0NN: ...")` — never skip or delete it.
5. Assert the **balance**, not just the status code. A `422` on its own is cheap.
6. Get ids, dates and stakes from `pick_*()`. The catalog changes; literals rot.
7. No `print()` — use `get_logger("<name>")`.

---

## Known issues in this repo

- **The `.env` account id is not gitignored.** Commit discipline is currently the only protection. See the note above.
- **`pick_match()` defaults to `today="2026-10-12"`.** Past-dated once the fixtures roll over.
- **`test_loading_state` is `xfail(strict=False)`** — a timing-dependent test, not a defect tracker.
- **Money tests are only CI-safe once accounts can be isolated.** The shared account is the suite's main structural weakness; see recommendation 1 in [`PartC`](PartC_Strategy_and_Recommendations.md).

---

Internal QA harness for a take-home assignment. Not for production use.