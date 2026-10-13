"""Test data selection functions: reusable picks for match IDs, dates, and stakes."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

from datetime import date
from typing import Any, Literal

from libs.logger import get_logger

from testfunctions.api_helper import get_matches

logger = get_logger("data_functions")

# Business limits from the feature spec (Section 3).
MIN_STAKE: float = 1.00
MAX_STAKE: float = 100.00

Outcome = Literal["1", "X", "2"]  # home / draw / away
OUTCOMES: tuple[str, ...] = ("1", "X", "2")


def today() -> str:
    """Today's date as YYYY-MM-DD, for past/future decisions."""
    return date.today().isoformat()


def _matches() -> list[dict[str, Any]]:
    return get_matches()


def pick_upcoming_match(matches: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """First match with a kickoff date today or later.

    Args:
        matches: optional pre-fetched catalog to avoid a second API call.
    Returns:
        The full Match dict (id, competition, kickoffDate, homeTeam, awayTeam, odds).
    Raises:
        AssertionError: when the catalog holds no upcoming match.
    """
    catalog = matches if matches is not None else _matches()
    reference = today()
    for match in catalog:
        if str(match["kickoffDate"]) >= reference:
            return match
    msg = "no upcoming match in the catalog"
    logger.error(msg)
    raise AssertionError(msg)


def pick_past_match(matches: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """First match whose kickoff date is before today.

    Args:
        matches: optional pre-fetched catalog.
    Returns:
        The full Match dict.
    Raises:
        AssertionError: when the catalog holds no past match.
    """
    catalog = matches if matches is not None else _matches()
    reference = today()
    for match in catalog:
        if str(match["kickoffDate"]) < reference:
            return match
    msg = "no past match in the catalog"
    logger.error(msg)
    raise AssertionError(msg)


def pick_match_by_date(month: str, matches: list[dict[str, Any]] | None = None) -> str:
    """A catalog date (YYYY-MM-DD) in the given month that actually has fixtures.

    Args:
        month: two-digit month, e.g. "10".
        matches: optional pre-fetched catalog.
    Returns:
        The date string.
    Raises:
        AssertionError: when that month has no fixtures.
    """
    catalog = matches if matches is not None else _matches()
    dates = sorted({str(m["kickoffDate"]) for m in catalog if str(m["kickoffDate"])[5:7] == month})
    if not dates:
        msg = f"no catalog fixtures in month {month}"
        logger.error(msg)
        raise AssertionError(msg)
    return dates[0]


def pick_stake(kind: Literal["min", "max", "below_min", "over_max", "safe"] = "min",
               balance: float | None = None) -> float:
    """A stake value suited to the scenario.

    Args:
        kind: "min" (1.00, the cheapest valid bet), "max" (100.00), "below_min"
            (0.50, must be rejected), "over_max" (150.00, must be rejected),
            "safe" (10.00, comfortably inside the limits).
        balance: current balance; required for "safe" and "over_max" to stay meaningful.
    Returns:
        The stake as a float.
    Raises:
        AssertionError: when "safe" is requested with no balance given and the
            catalog default would be unsafe.
        ValueError: for unknown stake kind.
    """
    if kind == "min":
        return MIN_STAKE
    if kind == "max":
        return MAX_STAKE
    if kind == "below_min":
        return 0.50
    if kind == "over_max":
        return MAX_STAKE + 50.00
    if kind == "safe":
        if balance is None:
            msg = "pick_stake('safe') needs the current balance"
            logger.error(msg)
            raise AssertionError(msg)
        return round(min(10.00, max(MIN_STAKE, balance / 2)), 2)
    msg = f"unknown stake kind {kind!r}"
    logger.error(msg)
    raise ValueError(msg)


def pick_outcome(available: tuple[str, ...] = OUTCOMES) -> Outcome:
    """Pick the home outcome by default; validates against the enum.

    Args:
        available: allowed outcomes.
    Returns:
        "1" (home win).
    Raises:
        ValueError: when "1" is not among the available outcomes.
    """
    if "1" not in available:
        msg = f"home outcome unavailable in {available}"
        logger.error(msg)
        raise ValueError(msg)
    return "1"


__all__ = [
    "MAX_STAKE",
    "MIN_STAKE",
    "OUTCOMES",
    "Outcome",
    "pick_match_by_date",
    "pick_outcome",
    "pick_past_match",
    "pick_stake",
    "pick_upcoming_match",
    "today",
]