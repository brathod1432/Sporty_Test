"""Reusable assertion functions for UI and API tests."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

from typing import Any

from libs.logger import get_logger
from libs.rest_helper import RestResponse

from testfunctions.api_helper import get_balance

logger = get_logger("assert_functions")

# Copy the feature spec requires verbatim (Section 4.4).
MIN_STAKE_MESSAGE: str = "Minimum stake is"
MAX_STAKE_MESSAGE: str = "Maximum stake is"
INSUFFICIENT_BALANCE_MESSAGE: str = "Insufficient balance"
ERROR_MODAL_TITLE: str = "Something went wrong"


def _body_dict(res: RestResponse) -> dict[str, Any]:
    return res.body if isinstance(res.body, dict) else {}


def assert_status(res: RestResponse, expected: int, context: str = "") -> RestResponse:
    """Assert the HTTP status code.

    Args:
        res: the response under test.
        expected: the status code required.
        context: optional label included in the failure message.
    Returns:
        The same response, for chaining.
    Raises:
        AssertionError: on any other status, with the body dump attached.
    """
    if res.status_code != expected:
        prefix = f"{context}: " if context else ""
        msg = f"{prefix}expected HTTP {expected}, got {res.status_code}\n{res.json_dump()}"
        logger.error(msg)
        raise AssertionError(msg)
    return res


def assert_error_code(res: RestResponse, expected_code: str,
                      allowed: tuple[str, ...] = ()) -> dict[str, Any]:
    """Assert the machine-readable `error` field in the body.

    Args:
        res: the response under test.
        expected_code: the error code required (e.g. "invalid_stake_min").
        allowed: extra codes that are equally acceptable (e.g. when the server
            checks max-stake before balance).
    Returns:
        The parsed body dict.
    Raises:
        AssertionError: when the code is neither the expected nor an allowed one.
    """
    body = _body_dict(res)
    code = body.get("error")
    if code not in (expected_code, *allowed):
        msg = f"expected error {expected_code!r}, got {code!r}\n{res.json_dump()}"
        logger.error(msg)
        raise AssertionError(msg)
    return body


def assert_balance_unchanged(before: float, user_id: str | None = None) -> float:
    """Assert the live balance still equals the value recorded earlier.

    Use after a call that was expected to be rejected; a change means the call
    was charged, which is the failure this is meant to catch.

    Args:
        before: the balance captured before the call.
        user_id: optional override; defaults to the `.env` user.
    Returns:
        The unchanged balance.
    Raises:
        AssertionError: when the balance moved.
    """
    after = get_balance(user_id)
    if after != before:
        msg = f"balance moved {before} -> {after} (expected no charge)"
        logger.error(msg)
        raise AssertionError(msg)
    return after


def assert_receipt_matches(captured: dict[str, Any], receipt: dict[str, Any]) -> None:
    """Assert a receipt agrees with the pre-placement slip capture.

    Args:
        captured: values read from the slip before submitting, e.g.
            {"matchId": ..., "selection": "HOME", "stake": 1.0, "odds": 2.45}.
        receipt: the parsed place-bet response body.
    Raises:
        AssertionError: naming the first field that disagrees.
    """
    for field, expected in captured.items():
        actual = receipt.get(field)
        if isinstance(expected, float) or isinstance(actual, float):
            if abs(float(actual or 0.0) - float(expected)) > 0.005:
                msg = f"receipt {field}: expected {expected}, got {actual}"
                logger.error(msg)
                raise AssertionError(msg)
        elif actual != expected:
            msg = f"receipt {field}: expected {expected!r}, got {actual!r}"
            logger.error(msg)
            raise AssertionError(msg)


def assert_payout_math(stake: float, odds: float, payout: float) -> None:
    """Assert payout equals stake x odds to the cent.

    Args:
        stake: the staked amount.
        odds: the odds used at placement.
        payout: the payout reported by the receipt.
    Raises:
        AssertionError: when the arithmetic is off by more than half a cent.
    """
    expected = round(stake * odds, 2)
    if abs(payout - expected) > 0.005:
        msg = f"payout {payout} != stake {stake} x odds {odds} = {expected}"
        logger.error(msg)
        raise AssertionError(msg)


def assert_page_contains(page_text: str, *needles: str, label: str = "page") -> None:
    """Assert every needle appears in the rendered page text (case-insensitive).

    Args:
        page_text: the full visible page text.
        needles: substrings that must all be present.
        label: what is being checked, used in the failure message.
    Raises:
        AssertionError: listing the missing substrings.
    """
    lowered = page_text.lower()
    missing = [n for n in needles if n.lower() not in lowered]
    if missing:
        msg = f"{label} missing {missing}; tail was: {page_text[-200:]!r}"
        logger.error(msg)
        raise AssertionError(msg)


def assert_single_selection(slip_text: str) -> None:
    """Assert the bet slip holds exactly one active selection.

    Args:
        slip_text: the bet-slip panel text.
    Raises:
        AssertionError: when zero or several matches are listed in the slip.
    """
    count = slip_text.count(" vs ")
    if count != 1:
        msg = f"expected exactly 1 selection in the slip, found {count}: {slip_text[:200]!r}"
        logger.error(msg)
        raise AssertionError(msg)


__all__ = [
    "ERROR_MODAL_TITLE",
    "INSUFFICIENT_BALANCE_MESSAGE",
    "MAX_STAKE_MESSAGE",
    "MIN_STAKE_MESSAGE",
    "assert_balance_unchanged",
    "assert_error_code",
    "assert_page_contains",
    "assert_payout_math",
    "assert_receipt_matches",
    "assert_single_selection",
    "assert_status",
]