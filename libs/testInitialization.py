"""Shared `__main__` entry point for every test script.

Lets a QA run one test function, several, or all of them, without pytest:

    python tests/api_tests/test_rest_endpoints.py
    python tests/ui_tests/test_e2e_bet.py --run-bet -td check_place_bet_happy_path
    python tests/ui_tests/test_regression_filters.py -td check_filters

Several names may be given, separated by commas:

    python tests/api_tests/test_place_bet_validation.py -td check_bad_selection_rejected,check_over_balance_rejected

Custom arguments are declared in `Configure`, test functions in `testSuite`:

    if __name__ == "__main__":
        testInitialization.Configure(
            title="test_regression_filters",
            requires=["--run-bet"],
            args=[testInitialization.argument("--slow", action="store_true")],
        )
        testInitialization.testSuite(
            check_filters,
            check_something_else,
        )
        testInitialization.run()

With no `-td` every registered function runs. With `-td` only the named ones do.
Functions may set `xfail_reason` on themselves; a failure is then reported as XFAIL
instead of FAIL, which keeps the direct runner's output in step with pytest.

pytest is unaffected: this module is never imported at collection time, and
`__test__ = False` stops pytest collecting this file even if it is pointed at it.
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

__test__ = False

import argparse
import os
import sys

from libs.logger import get_logger

logger = get_logger("TestInit")

_title = ""
_requires: list[str] = []
_args: list[tuple[tuple[str, ...], dict]] = []
_funcs: list = []


def Configure(title: str = "", requires: list[str] | None = None,
              args: list[tuple[tuple[str, ...], dict]] | None = None) -> None:
    """Set the options for this script.

    Args:
        title: name shown in the output.
        requires: command-line flags that must be present or the script skips.
        args: extra arguments, each built with `argument()`.
    """
    global _title, _requires, _args
    _title = title
    _requires = requires or []
    _args = args or []


def argument(*flags: str, **kwargs) -> tuple[tuple[str, ...], dict]:
    """Build one custom argument for `Configure(args=[...])`.

    Args:
        *flags: the option strings, e.g. "--slow".
        **kwargs: passed straight to argparse, e.g. action="store_true".
    Returns:
        A spec that `Configure` hands to argparse.
    """
    return flags, kwargs


def testSuite(*funcs) -> None:
    """Register the test functions for this script, one per line."""
    _funcs.clear()
    _funcs.extend(funcs)


def run() -> None:
    """Run the selected test functions and exit with the result.

    Raises:
        SystemExit: 2 for an unknown `-td` name, 1 when a check fails.
    """
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]), description=_title)
    parser.add_argument("-td", "--test-def", default=None,
                        help="comma-separated test names to run (default: all)")
    parser.add_argument("-x", "--stop-on-fail", action="store_true",
                        help="stop at first failure (default: continue through all)")
    for flags, kwargs in _args:
        parser.add_argument(*flags, **kwargs)
    options, _unknown = parser.parse_known_args()

    # Script-level gate (preserved for backward compatibility)
    for flag in _requires:
        if flag not in sys.argv:
            logger.info(f"SKIP ({_title}) needs {flag}")
            return

    selected = _funcs
    if options.test_def:
        by_name = {f.__name__: f for f in _funcs}
        wanted = [n.strip() for n in options.test_def.split(",") if n.strip()]
        unknown = [n for n in wanted if n not in by_name]
        if unknown:
            logger.error(f"Unknown test name(s): {', '.join(unknown)}")
            logger.info("Available: " + ", ".join(by_name))
            raise SystemExit(2)
        selected = [by_name[n] for n in wanted]

    failed: list[str] = []
    skipped: list[str] = []
    xfailed_count = 0
    for func in selected:
        # Per-function gate — checked at call time, not script start
        func_requires = getattr(func, "requires", None)
        if func_requires:
            missing = [f for f in func_requires if f not in sys.argv]
            if missing:
                logger.info(f"SKIP ({func.__name__}) needs {', '.join(missing)}")
                skipped.append(func.__name__)
                continue  # skip this function, proceed to next

        try:
            func()
            logger.success(f"PASS {func.__name__}")
        except Exception as exc:
            expected = getattr(func, "xfail_reason", None)
            if isinstance(exc, AssertionError):
                if expected:
                    logger.warning(f"XFAIL {func.__name__} ({expected}): {str(exc)[:200]}")
                    xfailed_count += 1
                else:
                    failed.append(func.__name__)
                    logger.error(f"FAIL {func.__name__}: {str(exc)[:250]}")
            else:
                # Non-assertion failure — RuntimeError from require_balance, ValueError, etc.
                failed.append(func.__name__)
                logger.error(f"ERROR {func.__name__} ({type(exc).__name__}): {str(exc)[:250]}")

            if options.stop_on_fail and failed:
                logger.info(f"Stopping on first failure (--stop-on-fail)")
                break

    total = len(selected)
    passed = total - len(failed) - len(skipped)
    # xfailed are a subset of passed in terms of exit code, but tracked separately
    logger.info(f"SUMMARY: {passed} passed, {len(failed)} failed, {len(skipped)} skipped, {xfailed_count} xfail | total {total}")

    if failed:
        logger.error(f"{len(failed)} failure(s): {', '.join(failed)}")
        raise SystemExit(1)
    logger.success(f"OK — {passed} passed, {len(skipped)} skipped, {xfailed_count} xfail")