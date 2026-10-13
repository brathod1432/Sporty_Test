"""REST API test functions - one helper per documented endpoint.

Thin wrappers over `libs/rest_helper.py` that also validate the status code.
Every helper takes `expected_rc`, a list of acceptable return codes; a response
outside that list raises.

Example:
    from testfunctions.rest_api import get_matches_rc, get_balance_rc

    res = get_matches_rc()                       # expects 200
    res = get_balance_rc(expected_rc=[200])
    res = place_bet_rc("match-1", "HOME", 0.5,  # 0.5 must be refused
                       expected_rc=[422])
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

from typing import Any

from libs.rest_helper import RestResponse, send_request

from testfunctions.api_helper import api_url, auth_headers

# Documented status codes (see documentation/api_guide.md).
DEFAULT_MATCHES_RC: list[int] = [200]
DEFAULT_BALANCE_RC: list[int] = [200]
DEFAULT_PLACE_BET_RC: list[int] = [200]
DEFAULT_RESET_RC: list[int] = [200]


def validate_rc(res: RestResponse, expected_rc: list[int], context: str = "") -> RestResponse:
    """Assert the response code is one of `expected_rc`.

    Args:
        res: the response to check.
        expected_rc: acceptable return codes, e.g. [200] or [400, 422].
        context: label used in the failure message.
    Returns:
        The same response, for chaining.
    Raises:
        AssertionError: when the code is not in the accepted list.
    """
    if res.status_code not in expected_rc:
        label = f"{context}: " if context else ""
        raise AssertionError(
            f"{label}expected one of {expected_rc}, got {res.status_code}\n{res.json_dump()}")
    return res


def get_matches_rc(headers: dict[str, str] | None = None,
                   expected_rc: list[int] = DEFAULT_MATCHES_RC) -> RestResponse:
    """GET /api/matches.

    Args:
        headers: request headers; defaults to the `.env` user.
        expected_rc: acceptable status codes.
    Returns:
        The validated response (body is a list of Match dicts).
    Raises:
        AssertionError: when the status code is not accepted.
    """
    res = send_request("get", api_url("/api/matches"),
                       headers=headers or auth_headers(), raiseError=False)
    return validate_rc(res, expected_rc, "GET /api/matches")


def get_balance_rc(headers: dict[str, str] | None = None,
                   expected_rc: list[int] = DEFAULT_BALANCE_RC) -> RestResponse:
    """GET /api/balance.

    Args:
        headers: request headers; defaults to the `.env` user.
        expected_rc: acceptable status codes.
    Returns:
        The validated response (body is {"balance": float, "currency": "EUR"}).
    Raises:
        AssertionError: when the status code is not accepted.
    """
    res = send_request("get", api_url("/api/balance"), headers=headers or auth_headers(), raiseError=False)
    return validate_rc(res, expected_rc, "GET /api/balance")


def place_bet_rc(match_id: str, selection: str, stake: float,
                 headers: dict[str, str] | None = None,
                 expected_rc: list[int] = DEFAULT_PLACE_BET_RC) -> RestResponse:
    """POST /api/place-bet.

    Args:
        match_id: catalog match id.
        selection: "HOME", "DRAW" or "AWAY".
        stake: amount to stake.
        headers: request headers; defaults to the `.env` user.
        expected_rc: acceptable status codes - pass [422] for a case that must
            be refused so an unexpected success fails the test.
    Returns:
        The validated response.
    Raises:
        AssertionError: when the status code is not accepted.
    """
    payload: dict[str, Any] = {"matchId": match_id, "selection": selection, "stake": stake}
    res = send_request("post", api_url("/api/place-bet"), headers=headers or auth_headers(), json=payload, raiseError=False)
    return validate_rc(res, expected_rc, "POST /api/place-bet")


def reset_balance_rc(headers: dict[str, str] | None = None,
                     expected_rc: list[int] = DEFAULT_RESET_RC) -> RestResponse:
    """POST /api/reset-balance.

    Args:
        headers: request headers; defaults to the `.env` user.
        expected_rc: acceptable status codes.
    Returns:
        The validated response (body carries the reset message and balance).
    Raises:
        AssertionError: when the status code is not accepted.
    """
    res = send_request("post", api_url("/api/reset-balance"), headers=headers or auth_headers(), raiseError=False)
    return validate_rc(res, expected_rc, "POST /api/reset-balance")


__all__ = [
    "DEFAULT_BALANCE_RC",
    "DEFAULT_MATCHES_RC",
    "DEFAULT_PLACE_BET_RC",
    "DEFAULT_RESET_RC",
    "get_balance_rc",
    "get_matches_rc",
    "place_bet_rc",
    "reset_balance_rc",
    "validate_rc",
]
