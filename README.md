# Sporty_Test — Sports Betting App Test Harness

Automation suite for a sports-betting web app: **42 tests** (16 API checks, 1 end-to-end UI journey, 25 UI regression checks) built with **pytest + requests + Selenium**. Every test runs under `pytest` or as a plain `python` script.

> App: `https://qae-assignment-tau.vercel.app/` · Author: Brijesh Rathod [bgrathod00@gmail.com]

---

## Quick start

- **Prereqs:** Python 3.11, Chrome (Selenium fetches its own driver).
- **Setup:**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r python311_requirements.txt
  copy .env.example .env
  ```
- Put the test user-id in `.env` as `USER_ID`.
- Verify: `python libs/logger.py` (self-test) and `pytest tests/ --collect-only -q` (lists 42 tests).

---

## Running

- **Free run (default, spends nothing)** — `pytest tests/ -v`. Money tests skip without the flag; open bugs report as xfail, each naming its defect ID.
- **Cost proof** — read `GET /api/balance` before and after. A plain run can't spend, and the two readings prove it.
- **Gated run (spends real balance — approval only)** — `pytest tests/ -v --run-bet`. The 4 money tests, each resetting the balance afterwards. Never in CI.
- **Without pytest** — every file is a script: `python tests/api_tests/test_api_business_rules.py -td check_get_matches`. No flag = all checks; `-td` picks by name; `-x` stops at the first failure.

---

## The two showcase tests

- **E2E UI — `test1_place_bet_happy_path`** (`tests/ui_tests/test_e2e_bet.py`): the revenue action in a real browser — select, stake, place, receipt, balance drop. The only flow the API can't prove. Gated.
- **API — `test_below_minimum_rejected`** (`tests/api_tests/test_api_business_rules.py`): stakes `0.50`/`0.01` must return `422 invalid_stake_min` with no charge. Milliseconds, free, zero flakiness.

Full rationale: `PartB_Automation.md`. Test plan: `PartA_ManualQA_and_Test_Strategy.md`. Strategy: `PartC_Strategy_and_Recommendations.md`.

---

## Known open bugs (all strict-xfail, all in `defectsVault/`)

| Test | Defect | Severity | One line |
|---|---|---|---|
| `test_past_match_rejected` | SportyQAD-011 | Critical | Past-match bet accepted and charged |
| `test_double_submit_rejected` | SportyQAD-014 | Critical | Double submit charges twice, no 409 |
| `test_negative_stake_rejected` | SportyQAD-021 | Critical | Negative stake credits the account |
| `test_tc009_kickoff_time` | SportyQAD-002 | Medium | No kickoff time, bare `-` placeholders |
| `test_match_counter_updates` | SportyQAD-015 | Medium | Counter keeps the unfiltered total |
| `test_invalid_range_rejected` / `test_empty_state` | SportyQAD-010 | Medium | Bad odds range silently applied, blank list |
| `test_popover_*` (2) | SportyQAD-004 | Medium | Odds popover covers cards, won't dismiss |
| `test_profile_icon_opens_details` | SportyQAD-009 | Medium | Profile icon does nothing |
| `test_balance_updates_realtime_after_bet` | SportyQAD-022 | High | Header balance stale until refresh |
| `test_reset_reports_actual_balance` | SportyQAD-018 | Medium | Reset reports 125.5, restores 120.0 |

An xfail here is a filed bug with steps and screenshots — never a mystery. The day one XPASSes, the server was fixed.

---

## Structure

```
Sporty_Test/
├── libs/                   # Helpers: logger, rest_helper, testInitialization (dual runner)
├── libs/testfunctions/     # Step verbs: api_helper, api_functions, rest_api, assert/data/modal/ui
├── tests/api_tests/        # test_api_business_rules.py (16 checks)
├── tests/ui_tests/         # test_e2e_bet.py (gated) + test_ui_regression.py (25 checks)
├── documentation/          # Brief + spec, API guide, test_strategy/ (TC-001..010)
├── defectsVault/           # 22 defects (15 Bugs + 7 Epics) + screenshots
├── conftest.py             # The --run-bet flag
└── .env                    # USER_ID + URLs (copy from .env.example, never commit)
```

Rule of the codebase: **tests state intentions, helpers do the work.** Adding a test? One `check_*` + one `test_*`, register it in `testSuite(...)`, gate it if it moves money, xfail it if the bug is open. Details in `PartB_Automation.md`.

---

## Environment (`.env`)

| Variable | Required | Default |
|---|---|---|
| `USER_ID` | **Yes** | — (22-char test account id) |
| `BASE_URL` / `APP_URL` / `API_DOCS_URL` | No | `https://qae-assignment-tau.vercel.app/...` |
| `DEFAULT_STAKE` / `REQUEST_TIMEOUT` | No | `1.01` / `30` |

---

Internal QA harness for a take-home assignment. Not for production use.
