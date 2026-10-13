"""Small task functions for API tests over libs/rest_helper.py."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import os
from typing import Any

from libs.logger import get_logger
from libs.rest_helper import RestResponse, send_request

from testfunctions.ui_helper import load_user_id

logger = get_logger("api_helper")

BASE_URL: str = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app")


def auth_headers(user_id: str | None = None) -> dict[str, str]:
    """Request headers with the test user. Reads `.env` unless given."""
    return {"x-user-id": user_id or os.getenv("USER_ID") or load_user_id()}


def api_url(path: str) -> str:
    """Full URL for an API path."""
    return f"{BASE_URL.rstrip('/')}{path}"


def get_balance(user_id: str | None = None) -> float:
    """Current EUR balance (raises on non-200)."""
    res = send_request("get", api_url("/api/balance"), headers=auth_headers(user_id))
    if res.status_code != 200:
        logger.error(f"GET /api/balance -> {res.status_code}: {res.body}")
        raise AssertionError(f"GET /api/balance -> {res.status_code}: {res.body}")
    return float(res.body["balance"])


def get_matches(user_id: str | None = None) -> list[dict[str, Any]]:
    """Match catalog (raises on non-200)."""
    res = send_request("get", api_url("/api/matches"), headers=auth_headers(user_id))
    if res.status_code != 200:
        logger.error(f"GET /api/matches -> {res.status_code}: {res.body}")
        raise AssertionError(f"GET /api/matches -> {res.status_code}: {res.body}")
    return list(res.body)


def pick_match(matches: list[dict[str, Any]], future: bool, today: str = "2026-10-12") -> dict[str, Any]:
    """First match strictly in the future (future=True) or past (False)."""
    for match in matches:
        is_future = str(match["kickoffDate"]) >= today
        if is_future == future:
            return match
    msg = f"No {'future' if future else 'past'} match in catalog"
    logger.error(msg)
    raise AssertionError(msg)


def place_bet(match_id: str, selection: str, stake: float, user_id: str | None = None) -> RestResponse:
    """POST /api/place-bet. Never raises - returns the response for asserts."""
    return send_request(
        "post",
        api_url("/api/place-bet"),
        headers=auth_headers(user_id),
        json={"matchId": match_id, "selection": selection, "stake": stake},
        raiseError=False,
    )


def reset_balance(user_id: str | None = None) -> RestResponse:
    """POST /api/reset-balance. Never raises - returns the response for asserts."""
    return send_request("post", api_url("/api/reset-balance"), headers=auth_headers(user_id), raiseError=False)


def assert_balance_unchanged(before: float, user_id: str | None = None) -> float:
    """Re-read balance, assert it still equals `before`. Returns the balance."""
    after = get_balance(user_id)
    if after != before:
        msg = f"balance moved {before} -> {after} (unexpected charge!)"
        logger.error(msg)
        raise AssertionError(msg)
    return after


def place_bet_raw(match_id: str, selection: str, stake: float, user_id: str | None = None) -> RestResponse:
    """POST /api/place-bet without raiseError - caller inspects the status."""
    return send_request(
        "post", api_url("/api/place-bet"),
        headers=auth_headers(user_id),
        json={"matchId": match_id, "selection": selection, "stake": stake},
        raiseError=False,
    )


def require_balance(expected: float | None = None, minimum: float = 0.0,
                     user_id: str | None = None) -> float:
    """Guard: abort the run unless the opening balance is usable.

    Raises RuntimeError (not AssertionError) so a guard trip reads as an
    environment problem, never as a test failure. Returns the balance.
    """
    actual = get_balance(user_id)
    if expected is not None and actual != expected:
        msg = f"balance guard: expected {expected}, live is {actual} - reset first?"
        logger.error(msg)
        raise RuntimeError(msg)
    if actual < minimum:
        msg = f"balance guard: {actual} below minimum {minimum} - cannot proceed"
        logger.error(msg)
        raise RuntimeError(msg)
    return actual


__all__ = [
    "BASE_URL",
    "api_url",
    "assert_balance_unchanged",
    "auth_headers",
    "get_balance",
    "get_matches",
    "pick_match",
    "place_bet",
    "place_bet_raw",
    "require_balance",
    "reset_balance",
]