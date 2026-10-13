"""Project-wide pytest options.

`--run-bet` gates balance-spending tests (happy-path bet, double-submit probe).
Without it they skip, so a plain `pytest` run is always zero-cost.
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-bet",
        action="store_true",
        default=False,
        help="allow balance-spending tests (place real test bets)",
    )
