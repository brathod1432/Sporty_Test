# Sporty_Test — Sports Betting App Test Harness

Minimal, zero-framework test suite for the **Sporty** sports-betting web application. Built with **pytest + requests + selenium** and reusable helpers in `libs/`. All tests run against a live deployed app (URL configured via `.env`).

> **Current status**: 28 tests passing, 4 skipped, 8 expected-fail (tracking known defects). Free test suite spends €0 balance.

---

## Quick Start

### Prerequisites
- **Python 3.11 or higher** (3.11.9 recommended; lower versions not supported)
- **Git** (optional, for cloning)
- **Chrome/Chromium** installed (for selenium UI tests)

### 1. Clone & Enter Project
```cmd
git clone <repo-url>
cd Sporty_Test
```

### 2. Create Virtual Environment
```cmd
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
```

### 3. Install Dependencies
```cmd
pip install --upgrade pip
pip install -r python311_requirements.txt
```
This installs: `pytest==9.1.1`, `requests==2.34.2`, `numpy==2.4.6`, `selenium==4.51.0`, `ipython==9.17.1` (+ transitive deps).

### 4. Configure Environment
```cmd
copy .env.example .env
```
Edit `.env` and set **`USER_ID`** to your 22-character test account ID (provided by the Sporty team).  
Other vars (`BASE_URL`, `APP_URL`, `API_DOCS_URL`, `DEFAULT_STAKE`, `REQUEST_TIMEOUT`) have sensible defaults.

### 5. Verify Setup
```cmd
python libs/logger.py           # Self-test: prints coloured log demo
.venv\Scripts\python -m pytest tests/ -v --co -q   # Dry-run: lists 40 tests
```

---

## Running Tests

### Free Test Suite (default, spends €0)
```cmd
.venv\Scripts\python -m pytest tests/ -v
```
- 28 passed, 4 skipped, 8 xfailed
- Balance guard in `tools/run_free_suite.py` verifies zero money spent

### Expected Failures (8 xfailed) — All Track Reported Defects
The **8 `xfailed` tests are not broken tests** — they are **strict expected failures** that document **confirmed bugs in the Sporty app**. Each uses `@pytest.mark.xfail(strict=True)` so it will **XPASS (turn green) automatically** the day the server-side fix is deployed, alerting you the defect is resolved.

| # | Test | Defect ID | Severity | What the App Does Wrong |
|---|------|-----------|----------|-------------------------|
| 1 | `test_past_match_rejected` | **SportyQAD-011** | Critical | Accepts bets on **past/completed matches** — returns `200`, charges stake (spec: upcoming only) |
| 2 | `test_double_submit_rejected` | **SportyQAD-014** | Critical | **No concurrency guard** — two rapid bets both `200`, double-charges (spec: `409`) |
| 3 | `test_negative_stake_rejected` | **SportyQAD-021** | Critical | **Negative stake accepted** — `stake: -1` returns `200`, **credits account** (+€1), unbounded |
| 4 | `test_tc009_kickoff_time` | **SportyQAD-002** | High | **No kickoff time on cards** — shows bare `-` placeholders (spec §2.1 requires `HH:MM`) |
| 5 | `test_match_counter_updates` | **SportyQAD-015** | Medium | **Date filter works but counter lies** — "Showing 103 matches" with 1 card rendered |
| 6 | `test_invalid_range_rejected` | **SportyQAD-010** | Medium | **Invalid odds range (MIN>MAX) silently coerced** to `10.00-10.00`, blanks list, no error |
| 7 | `test_empty_state` | **SportyQAD-010** | Medium | **Filter to zero matches shows nothing** — no "no matches" copy, counter doesn't zero |
| 8 | `test_popover_does_not_cover_cards` + `test_popover_dismisses_on_outside_click` | **SportyQAD-004** | Medium | **Odds popover overlays cards** AND **cannot dismiss** — no click-outside/Escape handler |
| 9 | `test_profile_icon_opens_details` | **SportyQAD-009** | Low | **Profile icon is dead `<span>`** — no handler, no history/wallet access |
| 10 | *(new — no xfail test yet)* | **SportyQAD-022** | High | **Balance header stale after bet** — UI bet succeeds, receipt & API show new balance, but header stays at old value until manual refresh |

> **All 10 defects** (QAD-011, QAD-014, QAD-021, QAD-002, QAD-015, QAD-010×2, QAD-004×2, QAD-009, QAD-022) are **fully documented in `defectsVault/`** with reproduction steps, screenshots, and severity/type classification.

### Charged Tests (require `--run-bet` flag + manual approval)
```cmd
.venv\Scripts\python -m pytest tests/ -v --run-bet
```
- Runs: happy-path bet (TC-001), past-match rejection (TC-002), double-submit (TC-003), negative-stake (SportyQAD-021)
- **Each run spends real balance** — only execute with explicit approval

### Run a Single Test File (direct Python, no pytest)
```cmd
.venv\Scripts\python tests\api_tests\test_protocol_validation.py
.venv\Scripts\python tests\ui_tests\test_regression_balance.py -td check_balance
```
- Every test file exposes a `testSuite` via `libs/testInitialization.py`
- Flags: `-td check_name` (single), `-td a,b` (multiple), no flag = all checks
- Gated tests auto-skip without `--run-bet` (print `SKIP` and exit 0)

### Run All via Direct Python (bypasses pytest)
```cmd
.venv\Scripts\python tools\run_free_suite.py
```
- Executes every test file directly, scans logs for `place-bet` calls
- Proves zero-cost execution with complete evidence

---

## Project Structure

```
Sporty_Test/
├── .env                       # Your secrets (gitignored) — copy from .env.example
├── .env.example               # Template: USER_ID, BASE_URL, APP_URL, API_DOCS_URL, DEFAULT_STAKE, REQUEST_TIMEOUT
├── .gitignore                 # Ignores .venv/, .opencode/, logs/, __pycache__/, .env
├── BD_README.md               # Internal project memory (agent-maintained)
├── BD_changelog.md            # Append-only task history
├── BD_todo.md                 # Backlog checklist
├── BD_tasks/                  # One JSON per agent task
├── conftest.py                # Pytest plugin: --run-bet gate, shared fixtures
├── python311_requirements.txt # Pinned dependencies (pip install -r)
├── pyrightconfig.json         # Type-check config (venv paths, libs/ on sys.path)
├── README.md                  # This file
│
├── libs/                      # Reusable helpers (import via `from libs.x import ...`)
│   ├── __init__.py
│   ├── logger.py              # ProjectLogger family: get_logger(), coloured output, file+terminal capture, self-test
│   ├── rest_helper.py         # REST client: GET/POST/PUT/PATCH/DELETE + dispatcher, typed RestResponse, raiseError flag
│   ├── testInitialization.py  # Shared test runner: Configure(), argument(), testSuite(), run(), --run-bet gate, -td filter
│   │
│   └── testfunctions/         # Step-function layer (tests call these directly)
│       ├── __init__.py
│       ├── ui_helper.py       # Selenium driver factory, waits, parallel browsers, DOM ops, console logs, screenshots
│       ├── ui_functions.py    # 30+ UI steps: select_odds, enter_stake, submit_bet, wait_for_receipt, open_filter, etc.
│       ├── api_functions.py   # High-level bet flows: attempt_bet, attempt_rejected_bet, double_submit, restore_balance
│       ├── assert_functions.py# Balance/Receipt/Error assertions: assert_balance_unchanged, assert_receipt_matches, etc.
│       ├── data_functions.py  # Match/stake/outcome pickers: pick_match, pick_outcome, pick_stake
│       ├── modal_functions.py # Receipt/error modal handling: close_receipt, is_modal_open, clear_slip (dismisses backdrop)
│       ├── rest_api.py        # One typed helper per endpoint: get_matches_rc, get_balance_rc, place_bet_rc, reset_balance_rc
│       └── api_helper.py      # Auth + balance/matches/place/reset + require_balance() guard, unchanged-guard
│
├── tests/
│   ├── api_tests/             # API contract / validation tests (6 files)
│   │   ├── test_place_bet_validation.py     # TP-003..005: min/max/over-balance (2 pass, 1 xfail)
│   │   ├── test_past_match_rejected.py      # SportyQAD-011: past matches accepted (xfail)
│   │   ├── test_place_bet_double_submit.py  # SportyQAD-014: double charge (xfail)
│   │   ├── test_negative_stake_rejected.py  # SportyQAD-021: negative stake pays out (xfail, Critical)
│   │   ├── test_protocol_validation.py      # 4 free: 401/405/400/422 boundaries
│   │   └── test_rest_endpoints.py           # 6 free: catalog/balance/reset/refused/auth on all 4 routes
│   │
│   └── ui_tests/              # Browser regression tests (23+ files)
│       ├── explore_ui.py              # Discovery: match count, buttons, console errors
│       ├── capture_loading.py         # Loading spinner + €0.00 header/slip (read-only)
│       ├── test_e2e_bet.py            # Happy-path bet (TC-001, gated)
│       ├── test_regression_app_load.py
│       ├── test_regression_balance.py
│       ├── test_regression_filters.py
│       ├── test_regression_match_cards.py
│       ├── test_regression_empty_slip.py
│       ├── test_regression_date_filter.py
│       ├── test_regression_odds_range_filter.py
│       ├── test_regression_stake_input.py
│       ├── test_regression_loading_state.py
│       ├── test_regression_error_modal.py
│       ├── test_regression_network_resilience.py
│       ├── test_regression_https_no_mixed_content.py
│       ├── test_regression_rapid_match_switching.py
│       ├── test_regression_popover_overlap.py
│       ├── test_regression_profile_icon.py
│       ├── test_regression_kickoff_time_slot.py
│       ├── test_regression_empty_state.py
│       ├── test_regression_no_selection_blocks.py
│       ├── test_regression_refresh_clears_slip.py
│       ├── test_regression_stake_validation_messages.py
│       └── test_regression_invalid_range.py
│
├── documentation/
│   ├── Feature_Specification.md       # Full spec transcription (5 sections, business rules, endpoints)
│   ├── HQA_Take_Home_Task.md          # Original assignment (Part A/B/C, 8 betting concepts)
│   ├── api_guide.md                   # Auth table, 4 endpoints with typed req/resp, 422 catalog, rest_helper usage
│   ├── UI_gap_analysis.md             # Spec §-by-§ vs live app matrix (10X safe probes)
│   │
│   └── test_strategy/                 # Top 6 prioritized + Optional 4 test cases
│       ├── README.md                  # Summary table: ID, Title, Priority, Area, Cost, Current State
│       ├── TC-001-happy-path-bet-receipt.md
│       ├── TC-002-past-match-bet-refused.md
│       ├── TC-003-double-submit-single-charge.md
│       ├── TC-004-stake-above-balance-refused.md
│       ├── TC-005-stake-below-minimum-refused.md
│       ├── TC-006-receipt-data-integrity.md
│       ├── TC-007-reset-reports-persisted-balance.md
│       ├── TC-008-endpoint-user-context-boundary.md
│       ├── TC-009-team-ordering-match-data.md
│       └── TC-010-incomplete-slip-blocks-placement.md
│
├── defectsVault/                      # Defect registry with evidence
│   ├── DEFECTS_ReadMe.md              # Summary table: all 21 entries (15 Bugs + 6 Epics) with links
│   ├── bugs/                          # 15 bug files (SportyQAD-001..005, 009..015, 018, 021)
│   ├── epics/                         # 6 epic files (SportyQAD-006..008, 016, 017, 019, 020)
│   └── screenshots/                   # 18 PNG evidence files (gap_*, loading_state.png, profile_click2.png, etc.)
│
├── tools/
│   ├── run_free_suite.py              # Zero-cost proof: runs all tests directly, scans balance + logs for place-bet calls
│   └── mermaid_check.py               # Mermaid diagram syntax validator (CI helper)
│
├── logs/                              # Runtime logs (gitignored) — created by logger per test run
└── .opencode/                         # Internal agent memory (gitignored) — rules, decisions, stack, context
```

---

## Key Helper Modules (in `libs/`)

| Module | Purpose |
|--------|---------|
| `logger.py` | Canonical logging: `get_logger(name)` → coloured console + rotating file logs, `section()`, `log_kv()`, `exception()`, self-test |
| `rest_helper.py` | Typed REST client: `RestHelper.get/post/put/patch/delete`, single `_request()` dispatcher, `RestResponse.to_dict/json_dump`, `raiseError` flag |
| `testInitialization.py` | Universal test runner: `Configure(title, requires)`, `argument()`, `testSuite(*funcs)`, `run()`, `-td` filter, `--run-bet` gate |
| `testfunctions/ui_helper.py` | Selenium infrastructure: driver factory, `wait_for_content` (SPA-aware), parallel browsers (`run_parallel`), DOM ops, screenshots |
| `testfunctions/ui_functions.py` | 30+ reusable UI steps: `select_and_stake`, `open_filter`, `set_range`, `click_apply`, `submit_and_record_states`, `wait_for_place_bet_enabled` |
| `testfunctions/api_functions.py` | High-level bet flows: `attempt_bet`, `attempt_rejected_bet`, `double_submit`, `restore_balance`, `BetAttempt` dataclass |
| `testfunctions/assert_functions.py` | Assertions: `assert_status`, `assert_error_code`, `assert_balance_unchanged`, `assert_receipt_matches`, `assert_payout_math`, `assert_single_selection` |
| `testfunctions/data_functions.py` | Test data pickers: `pick_match`, `pick_outcome`, `pick_stake`, `upcoming_matches`, `live_matches` |
| `testfunctions/modal_functions.py` | Modal handling: `close_receipt`, `is_modal_open`, `clear_slip` (dismisses `modalBackdrop` first) |
| `testfunctions/rest_api.py` | Per-endpoint typed helpers: `get_matches_rc`, `get_balance_rc`, `place_bet_rc`, `reset_balance_rc` — each validates `expected_rc` list |
| `testfunctions/api_helper.py` | Auth + balance/matches/place/reset + `require_balance(minimum)` guard, `unchanged_guard()` context manager |

---

## Test Organization

| Directory | Scope | Run Cost |
|-----------|-------|----------|
| `tests/api_tests/` | API contract, validation, protocol, negative cases | Free (except gated: past-match, double-submit, negative-stake) |
| `tests/ui_tests/` | Browser regression: app load, balance, filters, cards, slip, stake, loading, modals, network, HTTPS, popovers | Free (except gated: happy-path bet) |
| `tests/` root | `conftest.py` (shared `--run-bet` gate), `explore_ui.py`, `capture_loading.py` | Free |

**All tests inherit from `libs.testInitialization`** — runnable via pytest **or** direct Python (`python test_file.py -td check_name`).

---

## Documentation & Defects

### Test Strategy (`documentation/test_strategy/`)
- **Top 6 (Prioritized)**: TC-001..TC-004 (Critical), TC-006, TC-008 (High)
- **Optional 4**: TC-005, TC-007, TC-009, TC-010
- Each case: Priority, Risk Rationale, Steps, Expected Result, Cost (Free/Charged), Current State (pass/xfail/manual)

### Defects Vault (`defectsVault/`)
- **`DEFECTS_ReadMe.md`** — Master table: 21 entries (15 Bugs + 6 Epics), Type, Severity, links
- **`bugs/`** — SportyQAD-001..005, 009..015, 018, 021 (Critical: 011, 014, 021)
- **`epics/`** — SportyQAD-006..008, 016, 017, 019, 020 (missing features: history, search, auth)
- **`screenshots/`** — 18 PNGs attached to defects (visual evidence)

---

## Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USER_ID` | **Yes** | — | 22-char test account ID (get from Sporty team) |
| `BASE_URL` | No | `https://sporty-qatest-382508864092.europe-west1.run.app/api` | API base |
| `APP_URL` | No | `https://sporty-qatest-382508864092.europe-west1.run.app` | Web app |
| `API_DOCS_URL` | No | `https://sporty-qatest-382508864092.europe-west1.run.app/api-docs` | OpenAPI spec |
| `DEFAULT_STAKE` | No | `10` | Default stake for tests |
| `REQUEST_TIMEOUT` | No | `10` | HTTP timeout seconds |

---

## CI / Quality Gates

```cmd
# Type checking (pyright)
.venv\Scripts\pyright

# Lint + type check (if configured)
.venv\Scripts\python -m pytest tests/ -v --tb=short

# Free suite proof (balance + log scan)
.venv\Scripts\python tools\run_free_suite.py
```

All gates must pass before merge. `pyright` config ensures `libs/` and `tests/` resolve under venv.

---

## Known Defects (Critical + High)

| ID | Title | Severity | Impact |
|----|-------|----------|--------|
| **SportyQAD-021** | Negative stake accepted → pays customer | Critical | Unbounded credit, repeatable |
| **SportyQAD-011** | Past matches accepted (bets on completed games) | Critical | Invalid bets accepted |
| **SportyQAD-014** | Double submit → double charge, no 409 guard | Critical | Duplicate charges |
| **SportyQAD-018** | Reset balance reports 125.5 but persists 120.0 | Medium | Misleading recovery |
| **SportyQAD-019/020** | No auth/session; credential in URL query string | High | Credential leakage |
| **SportyQAD-022** | Balance header does not update in real-time after bet | **High** | User sees stale balance after successful bet; must refresh to see correct amount |

Tracked in `defectsVault/` with reproduction steps and screenshots.

---

## Contributing / Extending

1. Add test file under `tests/api_tests/` or `tests/ui_tests/`
2. Import helpers from `libs.testfunctions.*` (not `libs/` directly)
3. Register checks via `testSuite()` in `testInitialization`
4. Add `--run-bet` gate if test spends balance: `requires=["--run-bet"]`
5. Run `pyright` and free suite before committing

---

## License / Ownership

Internal QA harness for Sporty take-home assignment. Not for production use.