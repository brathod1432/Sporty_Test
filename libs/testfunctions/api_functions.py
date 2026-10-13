"""API test-step functions: reusable scenario verbs for API tests."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

from dataclasses import dataclass
from typing import Any

from libs.logger import get_logger
from libs.rest_helper import RestResponse

from testfunctions.api_helper import (
    get_balance,
    get_matches,
    pick_match,
    place_bet,
    place_bet_raw,
    require_balance,
    reset_balance,
)

logger = get_logger("api_functions")


@dataclass
class BetAttempt:
    """The outcome of one attempted bet: responses plus the balance movement."""

    match_id: str
    selection: str
    stake: float
    response: RestResponse
    balance_before: float
    balance_after: float

    @property
    def status_code(self) -> int:
        """HTTP status of the attempt."""
        return self.response.status_code

    @property
    def charged(self) -> bool:
        """True when the balance moved - the bet was accepted."""
        return self.balance_after != self.balance_before


def attempt_bet(match_id: str, selection: str, stake: float) -> BetAttempt:
    """Submit one bet and record the balance before and after.

    Args:
        match_id: catalog match id.
        selection: "HOME", "DRAW" or "AWAY".
        stake: amount to stake.
    Returns:
        A BetAttempt with both responses and the balance movement.
    """
    before = get_balance()
    response = place_bet_raw(match_id, selection, stake)
    after = get_balance()
    return BetAttempt(match_id, selection, stake, response, before, after)


def attempt_rejected_bet(selection: str = "DRAW", stake: float = 0.50,
                         match_id: str | None = None) -> BetAttempt:
    """Submit a bet that should be rejected, on an UPCOMING match by default.

    Args:
        selection: selection to submit.
        stake: amount to submit (default 0.50, below the minimum).
        match_id: optional override; otherwise the first upcoming match is used.
    Returns:
        The BetAttempt; assert `status_code == 422` and `charged is False`.
    """
    target = match_id or str(pick_match(get_matches(), future=True)["id"])
    return attempt_bet(target, selection, stake)


def attempt_on_past_match(selection: str = "HOME", stake: float = 1.00) -> BetAttempt:
    """Submit a bet against a PAST match (spec says this must be refused).

    Args:
        selection: selection to submit.
        stake: amount to submit.
    Returns:
        The BetAttempt; currently the server accepts and charges this.
    """
    past = str(pick_match(get_matches(), future=False)["id"])
    return attempt_bet(past, selection, stake)


def double_submit(match_id: str | None = None, selection: str = "HOME",
                  stake: float = 1.00) -> tuple[BetAttempt, BetAttempt]:
    """Fire two place-bet requests back to back (spec expects 409 on the second).

    Args:
        match_id: optional override; otherwise the first upcoming match is used.
        selection: selection for both requests.
        stake: amount for both requests.
    Returns:
        The first and second attempts, each with its own balance movement.
    """
    target = match_id or str(pick_match(get_matches(), future=True)["id"])
    return (
        attempt_bet(target, selection, stake),
        attempt_bet(target, selection, stake),
    )


def place_and_reconcile(selection: str = "HOME", stake: float = 1.00,
                        match_id: str | None = None) -> tuple[BetAttempt, float]:
    """Place one bet and return the attempt plus the expected balance delta.

    This spends real test balance - call behind a deliberate gate.

    Args:
        selection: selection to submit.
        stake: amount to stake.
        match_id: optional override.
    Returns:
        The attempt and the balance that should remain after a correct deduction.
    """
    require_balance(minimum=stake)
    attempt = attempt_bet(match_id or str(pick_match(get_matches(), future=True)["id"]), selection, stake)
    return attempt, round(attempt.balance_before - stake, 2)


def restore_balance() -> float:
    """Reset the user balance and return the value the API reports.

    Returns:
        The balance reported by reset-balance.
    Raises:
        AssertionError: when the reset call fails.
    """
    response = reset_balance()
    if response.status_code != 200:
        logger.error(f"reset-balance failed: {response.status_code} {response.json_dump()}")
        raise AssertionError(f"reset-balance failed: {response.status_code} {response.json_dump()}")
    return float(response.body["balance"])


def balance_now() -> float:
    """Current balance as a float.

    Returns:
        The live EUR balance.
    """
    return get_balance()


def catalog_size() -> int:
    """Number of matches in the catalog.

    Returns:
        The catalog length.
    """
    return len(get_matches())


def catalog_dates() -> list[str]:
    """Every distinct kickoff date in the catalog, sorted.

    Returns:
        Sorted ISO date strings.
    """
    return sorted({str(m["kickoffDate"]) for m in get_matches()})


def teardown_reset_balance() -> float:
    """Reset balance after a money-spending test.

    Call this in a finally block or as a pytest fixture teardown.
    Returns the balance reported by the reset endpoint.
    """
    return restore_balance()


def teardown_reset_balance_silent() -> None:
    """Reset balance silently - never raises, logs result only.
    Use when teardown must not mask the original test result.
    """
    try:
        restore_balance()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Balance reset failed: {exc}")


__all__ = [
    "BetAttempt",
    "attempt_bet",
    "attempt_on_past_match",
    "attempt_rejected_bet",
    "balance_now",
    "catalog_dates",
    "catalog_size",
    "double_submit",
    "place_and_reconcile",
    "place_bet",
    "restore_balance",
    "teardown_reset_balance",
    "teardown_reset_balance_silent",
]