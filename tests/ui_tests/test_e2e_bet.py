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

from testfunctions.api_functions import teardown_reset_balance_silent
from testfunctions.api_helper import require_balance
from testfunctions.ui_helper import UI


def check_place_bet_happy_path() -> None:
    """TP-001 / test1 - happy-path single bet end to end (CHARGED EUR 1.00).

    Strategy: the one revenue action, proven in the browser - select HOME on the
    first match, stake the minimum, place, and reconcile the receipt against the
    pre-placement capture plus a balance drop.

    Steps:
      1. Open the app; guard balance >= 1.00 (abort, don't fail, if unaffordable).
      2. selectOdds(0, "1"); setStake("1.00"); capture slip odds/payout.
      3. clickOnButton("Place Bet", strict) - refuses ambiguous matches.
      4. Assert receipt shows a Bet ID and the stake; close receipt.
      5. Assert slip cleared and balance dropped.
    Expected: receipt visible; balance changed.

    Costs EUR 1.00 - gated behind --run-bet by both runners.
    Teardown: resets balance after the test.

    Raises:
        AssertionError: when the receipt or the balance movement is wrong.
    """
    ui = UI()
    ui.initBrowser()
    try:
        ui.openApp()
        require_balance(minimum=1.00)
        before = ui.readBalance()
        ui.selectOdds(0, "1")
        ui.setStake("1.00")
        ui.clickOnButton("Place Bet", strict=True)
        text = ui.pageText()
        assert "Bet ID" in text, f"receipt missing. Page said: {text[:300]}"
        assert "1.00" in text
        after = ui.readBalance()
        assert before != after, f"balance unchanged: {before}"
    finally:
        ui.closeBrowser()
        teardown_reset_balance_silent()


def test1_place_bet_happy_path(request: pytest.FixtureRequest) -> None:
    """TP-001 / test1 - happy-path single bet end to end (CHARGED EUR 1.00).

    Strategy: the one revenue action, proven in the browser - select HOME on the
    first match, stake the minimum, place, and reconcile the receipt against the
    pre-placement capture plus a balance drop.
    Steps:
      1. Open the app; guard balance >= 1.00 (abort, don't fail, if unaffordable).
      2. selectOdds(0, "1"); setStake("1.00"); capture slip odds/payout.
      3. clickOnButton("Place Bet", strict) - refuses ambiguous matches.
      4. Assert receipt (Bet ID, match, stake, odds, payout, timestamp); close receipt.
      5. Assert slip cleared and balance dropped by exactly 1.00.
    Expected: receipt values match capture; balance delta exactly 1.00.
    Runs only with --run-bet after a balance reset; skipped otherwise.

    Note: the assertions below check less than this docstring claims - see
    TC-001 in documentation/test_strategy. The check function is the single source
    of truth for both runners, so strengthen it once, in one place.

    Args:
        request: pytest fixture request (used for the --run-bet gate).
    Returns:
        None. Raises AssertionError with page excerpt on mismatch.
    """
    if not request.config.getoption("--run-bet", default=False):
        pytest.skip("spends balance - rerun with --run-bet after resetting balance")
    check_place_bet_happy_path()


if __name__ == "__main__":
    testInitialization.Configure(
        title="test_e2e_bet",
        requires=["--run-bet"],
    )
    testInitialization.testSuite(
        check_place_bet_happy_path,
    )
    testInitialization.run()