"""Unified API business-rule test suite — 16 checks covering validation,
protocol, endpoint contracts, and three Critical open bugs.

All checks are FREE except the three gated ones (SportyQAD-011, 014, 021).
Gating is per-function, so a plain run executes 13 free checks and skips 3.

Run (free):
  .venv\\Scripts\\python3 -m pytest tests/api_tests/test_api_business_rules.py -v
  .venv\\Scripts\\python3 tests/api_tests/test_api_business_rules.py

Run (all 16, gated):
  .venv\\Scripts\\python3 -m pytest tests/api_tests/test_api_business_rules.py --run-bet -v
  .venv\\Scripts\\python3 tests/api_tests/test_api_business_rules.py --run-bet
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import os
import sys

ENV = os.getcwd()
sys.path.append(ENV)
sys.path.append(ENV + '/libs/')
sys.path.append(ENV + '/tests/')
sys.path.append(ENV + '/testfunctions/')

import testInitialization
import pytest

from libs.logger import get_logger
logger = get_logger("test_api_business_rules")

# ─── Imports consolidated from all six sources ───
from libs.rest_helper import send_get, send_post, send_request

from testfunctions.api_functions import (
    attempt_bet, attempt_rejected_bet, balance_now,
    teardown_reset_balance_silent,
)
from testfunctions.api_helper import (
    get_matches, get_balance, pick_match, place_bet_raw, require_balance,
    api_url, auth_headers, BASE_URL
)
from testfunctions.assert_functions import (
    assert_balance_unchanged, assert_status, assert_error_code
)
from testfunctions.data_functions import MIN_STAKE, MAX_STAKE, pick_stake
from testfunctions.rest_api import (
    get_matches_rc, get_balance_rc, place_bet_rc, reset_balance_rc,
    DEFAULT_MATCHES_RC, DEFAULT_BALANCE_RC, DEFAULT_PLACE_BET_RC, DEFAULT_RESET_RC
)
from libs.rest_helper import send_request

# ─── Constants from source files ───
UNAUTHORIZED = 401
BAD_REQUEST = 400
UNPROCESSABLE = 422
FAKE_USER = {"x-user-id": "definitely-not-a-real-user"}
NEGATIVE_STAKES = (-1.00, -2.50)
STAKE = pick_stake("min")

# ─── Gated flag shared by three checks ───
GATED_FLAG = "--run-bet"

# ─── 1. Stake Validation (from test_place_bet_validation.py) ───

def _upcoming_id() -> str:
    """Shared helper: first upcoming match id."""
    return str(pick_match(get_matches(), future=True)["id"])

def check_below_minimum_rejected() -> None:
    """Stakes under the minimum are rejected (TP-003)."""
    match_id = _upcoming_id()
    for stake in (0.50, 0.01):
        attempt = attempt_bet(match_id, "DRAW", stake)
        assert_status(attempt.response, UNPROCESSABLE, f"stake {stake}")
        assert_error_code(attempt.response, "invalid_stake_min")
        assert not attempt.charged, f"stake {stake} was charged"

def check_bad_selection_rejected() -> None:
    """Non-enum selections are rejected (TP-004)."""
    match_id = _upcoming_id()
    for selection in ("HOME_WIN", "home"):
        attempt = attempt_bet(match_id, selection, pick_stake("min"))
        assert_status(attempt.response, UNPROCESSABLE, f"selection {selection}")
        assert_error_code(attempt.response, "invalid_selection")
        assert not attempt.charged, f"selection {selection} was charged"

def check_over_balance_rejected() -> None:
    """Stakes above balance are rejected (TP-005)."""
    attempt = attempt_rejected_bet("AWAY", MAX_STAKE + 50.00)
    assert_status(attempt.response, UNPROCESSABLE, "over balance")
    assert_error_code(attempt.response, "insufficient_balance", allowed=("invalid_stake_max",))
    assert not attempt.charged

# ─── 2. Protocol & Security Validation (from test_protocol_validation.py) ───

def check_missing_user_context() -> None:
    """Every endpoint rejects missing/invalid user context."""
    before = balance_now()
    anonymous = send_request("get", api_url("/api/matches"), raiseError=False)
    assert_status(anonymous, UNAUTHORIZED, "no user header")
    bogus = send_request("get", api_url("/api/matches"),
                         headers={"x-user-id": "definitely-not-a-real-user"}, raiseError=False)
    assert_status(bogus, UNAUTHORIZED, "fabricated user id")
    assert_balance_unchanged(before)

def check_unsupported_http_method() -> None:
    """POST /api/matches returns 405."""
    before = balance_now()
    res = send_post(api_url("/api/matches"), headers=auth_headers(), json={}, raiseError=False)
    assert_status(res, 405, "POST /api/matches")
    assert_balance_unchanged(before)

def check_malformed_body() -> None:
    """Non-JSON and non-object bodies are rejected."""
    before = balance_now()
    headers = auth_headers()

    broken = send_post(api_url("/api/place-bet"), headers=headers,
                       data="{not json", raiseError=False)
    assert_status(broken, BAD_REQUEST, "malformed body")
    assert_error_code(broken, "invalid_request", allowed=("invalid_json",))

    array = send_post(api_url("/api/place-bet"), headers=headers,
                      json=["a", "b"], raiseError=False)
    assert_status(array, BAD_REQUEST, "non-object body")
    assert_error_code(array, "invalid_request")
    assert_balance_unchanged(before)

def check_blank_match_id() -> None:
    """Empty or missing matchId is rejected."""
    before = balance_now()
    res = send_post(api_url("/api/place-bet"), headers=auth_headers(),
                    json={"matchId": "", "selection": "HOME", "stake": STAKE}, raiseError=False)
    assert_status(res, UNPROCESSABLE, "blank matchId")
    assert_error_code(res, "invalid_match_id", allowed=("invalid_match",))
    assert_balance_unchanged(before)

# ─── 3. Endpoint Contract Tests (from test_rest_endpoints.py) ───

def check_get_matches() -> None:
    """GET /api/matches returns a well-formed catalog."""
    res = get_matches_rc()
    matches = res.body
    assert isinstance(matches, list) and matches, f"expected a non-empty list, got {type(matches)}"
    required = {"id", "competition", "kickoffDate", "homeTeam", "awayTeam", "odds"}
    missing = required - set(matches[0].keys())
    assert not missing, f"Match is missing fields: {sorted(missing)}"
    for match in matches:
        assert isinstance(match["odds"], dict), f"odds is not an object: {match['odds']!r}"
        for side in ("home", "draw", "away"):
            value = match["odds"].get(side)
            assert isinstance(value, (int, float)), f"odds.{side} is not numeric: {value!r}"
            assert value > 1.0, f"fractional odds.{side} must exceed 1.0, got {value}"

def check_get_balance() -> None:
    """GET /api/balance returns a numeric EUR balance."""
    body = get_balance_rc().body
    assert isinstance(body.get("balance"), (int, float)), f"balance not numeric: {body!r}"
    assert body["balance"] >= 0, f"negative balance: {body!r}"
    assert body.get("currency") == "EUR", f"currency is not EUR: {body!r}"

def check_reset_balance_contract() -> None:
    """POST /api/reset-balance answers 200 with message, balance, currency."""
    res = reset_balance_rc()
    assert isinstance(res.body.get("message"), str), f"no message in reset body: {res.body!r}"
    assert isinstance(res.body.get("balance"), (int, float)), f"no balance: {res.body!r}"
    assert res.body.get("currency") == "EUR", f"currency is not EUR: {res.body!r}"

def check_place_bet_refused() -> None:
    """POST /api/place-bet refuses a below-minimum stake with 422."""
    before = balance_now()
    res = place_bet_rc("", "DRAW", pick_stake("below_min"), expected_rc=[UNPROCESSABLE])
    assert res.body.get("error") in ("invalid_stake_min", "invalid_match_id"), res.json_dump()
    assert_balance_unchanged(before)

def check_endpoints_require_user_context() -> None:
    """Every endpoint refuses a request without a valid user context."""
    for name, call in (
        ("GET /api/matches", lambda: get_matches_rc(headers=FAKE_USER, expected_rc=[UNAUTHORIZED])),
        ("GET /api/balance", lambda: get_balance_rc(headers=FAKE_USER, expected_rc=[UNAUTHORIZED])),
        ("POST /api/reset-balance", lambda: reset_balance_rc(headers=FAKE_USER, expected_rc=[UNAUTHORIZED])),
        ("POST /api/place-bet",
         lambda: place_bet_rc("any", "HOME", MIN_STAKE, headers=FAKE_USER, expected_rc=[UNAUTHORIZED])),
    ):
        call()
        logger.info(f"  {name} -> 401 without a valid user context")

def check_reset_reports_actual_balance() -> None:
    """POST /api/reset-balance reports the balance it actually restores (QAD-018)."""
    reported = reset_balance_rc().body["balance"]
    live = get_balance_rc().body["balance"]
    assert live == reported, f"reset reports {reported} but the restored balance is {live}"

setattr(check_reset_reports_actual_balance, "xfail_reason", "SportyQAD-018")

# ─── 4. Critical Bug Probes — gated (from dedicated files) ───

def check_past_match_rejected() -> None:
    """Past-match bet must be refused (SportyQAD-011)."""
    try:
        target = str(pick_match(get_matches(), future=False)["id"])
        attempt = attempt_bet(target, "HOME", pick_stake("min"))
        assert_status(attempt.response, UNPROCESSABLE, f"past match {target}")
        assert not attempt.charged, f"past match {target} was charged"
    finally:
        teardown_reset_balance_silent()

setattr(check_past_match_rejected, "requires", [GATED_FLAG])
setattr(check_past_match_rejected, "xfail_reason", "SportyQAD-011")

def check_negative_stake_rejected() -> None:
    """Negative stake must be refused, not paid out (SportyQAD-021)."""
    try:
        target = _upcoming_id()
        before = balance_now()
        for stake in NEGATIVE_STAKES:
            attempt = attempt_bet(target, "AWAY", stake)
            assert_status(attempt.response, UNPROCESSABLE, f"negative stake {stake}")
            assert not attempt.charged, (
                f"stake {stake} moved the balance "
                f"{attempt.balance_before} -> {attempt.balance_after}; "
                f"the server credited a negative stake")
        assert_balance_unchanged(before)
    finally:
        teardown_reset_balance_silent()

setattr(check_negative_stake_rejected, "requires", [GATED_FLAG])
setattr(check_negative_stake_rejected, "xfail_reason", "SportyQAD-021")

def check_double_submit_rejected() -> None:
    """Double submit must be blocked with 409, single charge (SportyQAD-014)."""
    try:
        before = require_balance(minimum=1.00)
        match = _upcoming_id()
        first = place_bet_raw(match, "HOME", 1.00)
        second = place_bet_raw(match, "HOME", 1.00)
        assert first.status_code == 200, f"first bet failed: {first.status_code} {first.json_dump()}"
        assert second.status_code == 409, f"double submit not blocked: {second.status_code} {second.json_dump()}"
        after = get_balance()
        assert after == round(before - 1.00, 2), f"charged twice: {before} -> {after} (expected {round(before - 1.00, 2)})"
        logger.success(f"double submit OK (first 200, second 409, balance {before} -> {after})")
    finally:
        teardown_reset_balance_silent()

setattr(check_double_submit_rejected, "requires", [GATED_FLAG])
setattr(check_double_submit_rejected, "xfail_reason", "SportyQAD-014")

# ─── pytest wrappers (1 per check, matching source behavior) ───

def test_below_minimum_rejected() -> None:
    """Stakes under the minimum are rejected (TP-003)."""
    check_below_minimum_rejected()

def test_bad_selection_rejected() -> None:
    """Non-enum selections are rejected (TP-004)."""
    check_bad_selection_rejected()

def test_over_balance_rejected() -> None:
    """Stakes above balance are rejected (TP-005)."""
    check_over_balance_rejected()

def test_missing_user_context() -> None:
    """Every endpoint rejects missing/invalid user context."""
    check_missing_user_context()

def test_unsupported_http_method() -> None:
    """POST /api/matches returns 405."""
    check_unsupported_http_method()

def test_malformed_body() -> None:
    """Non-JSON and non-object bodies are rejected."""
    check_malformed_body()

def test_blank_match_id() -> None:
    """Empty or missing matchId is rejected."""
    check_blank_match_id()

def test_get_matches() -> None:
    """GET /api/matches returns a well-formed catalog (200)."""
    check_get_matches()

def test_get_balance() -> None:
    """GET /api/balance returns a numeric EUR balance (200)."""
    check_get_balance()

def test_reset_balance() -> None:
    """POST /api/reset-balance answers 200 with a complete body."""
    check_reset_balance_contract()

@pytest.mark.xfail(strict=True, reason="SportyQAD-018: reset reports 125.5, actually restores 120.0")
def test_reset_reports_actual_balance() -> None:
    """REST API - the reset response matches the persisted balance."""
    check_reset_reports_actual_balance()

def test_place_bet_refused() -> None:
    """POST /api/place-bet refuses a below-minimum stake (422)."""
    check_place_bet_refused()

def test_endpoints_require_user_context() -> None:
    """REST API - all four endpoints demand a valid user context (401)."""
    check_endpoints_require_user_context()

@pytest.mark.skipif("not config.getoption('--run-bet')", reason="changes balance while QAD-011 open")
@pytest.mark.xfail(strict=True, reason="SportyQAD-011: past-match bet accepted and charged")
def test_past_match_rejected() -> None:
    """API - a bet on a past-date match must be refused."""
    check_past_match_rejected()

@pytest.mark.skipif("not config.getoption('--run-bet')", reason="changes balance while QAD-021 open")
@pytest.mark.xfail(strict=True, reason="SportyQAD-021: negative stake accepted and credits the account")
def test_negative_stake_rejected() -> None:
    """API - a negative stake must be refused, not paid out."""
    check_negative_stake_rejected()

@pytest.mark.skipif("not config.getoption('--run-bet')", reason="spends balance - rerun with --run-bet")
@pytest.mark.xfail(strict=True, reason="SportyQAD-014: second concurrent bet accepted and charged")
def test_double_submit_rejected() -> None:
    """API - a second immediate place-bet is refused with 409, charged once."""
    check_double_submit_rejected()

# ─── __main__ runner ───

if __name__ == "__main__":
    testInitialization.Configure(
        title="test_api_business_rules",
        # NOTE: no script-level requires; gating is per-function via setattr
    )
    testInitialization.testSuite(
        # 13 free
        check_below_minimum_rejected,
        check_bad_selection_rejected,
        check_over_balance_rejected,
        check_missing_user_context,
        check_unsupported_http_method,
        check_malformed_body,
        check_blank_match_id,
        check_get_matches,
        check_get_balance,
        check_reset_balance_contract,
        check_place_bet_refused,
        check_endpoints_require_user_context,
        check_reset_reports_actual_balance,
        # 3 gated — run() will check per-function `requires` attr
        check_past_match_rejected,
        check_negative_stake_rejected,
        check_double_submit_rejected,
    )
    testInitialization.run()