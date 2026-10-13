"""UI regression checks for the Sports Betting QA app (Selenium).

Every free UI check lives in this one file, grouped by the test-strategy case it
covers. Checks named `check_tc009_*` and `check_tc010_*` map directly to cases in
`documentation/test_strategy/`; the rest are supporting regressions.

Known app defects use `@pytest.mark.xfail(strict=True)`, so they stay in the suite
and turn green by themselves once fixed. FREE - nothing here places a bet.

Run all:  .venv/Scripts/python3 -m pytest tests/ui_tests/test_ui_regression.py -v
Run one:  .venv/Scripts/python3 tests/ui_tests/test_ui_regression.py -td check_tc009_team_ordering
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

# ─── Standard library imports ───
import os
import re
import sys
import time

# ─── Project path setup (once) ───
ENV = os.getcwd()
sys.path.append(ENV)
sys.path.append(ENV + '/libs/')
sys.path.append(ENV + '/tests/')
sys.path.append(ENV + '/testfunctions/')

# ─── Third-party imports ───
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ─── Project imports ───
import testInitialization
from libs.logger import get_logger

# testfunctions - API
from testfunctions.api_functions import balance_now, teardown_reset_balance_silent
from testfunctions.api_helper import get_balance, get_matches, pick_match

# testfunctions - assertions
from testfunctions.assert_functions import (
    MIN_STAKE_MESSAGE,
    assert_balance_unchanged,
    assert_page_contains,
    assert_single_selection,
)

# testfunctions - data
from testfunctions.data_functions import (
    pick_match_by_date,
    pick_stake,
    pick_upcoming_match,
)

# testfunctions - UI functions
from testfunctions.ui_functions import (
    card_dates,
    card_odds,
    click_apply,
    clear_slip,
    close_receipt,
    enter_stake,
    match_count,
    open_app,
    open_filter,
    refresh_page,
    select_and_stake,
    select_calendar_day,
    select_odds,
    set_range,
    slip_is_empty,
    slip_text,
    submit_and_record_states,
    submit_bet,
    submit_with_network_blocked,
    visible_cards,
    wait_for_place_bet_enabled,
    wait_for_receipt,
    _box,
    _overlaps,
    _panel,
    _open_odds_panel,
    _stake_field,
    _place_bet_visible,
    _apply_single_day,
)

# testfunctions - UI helpers
from testfunctions.ui_helper import (
    UI,
    console_errors,
    find_all,
    odds_buttons,
    page_resources,
    set_offline,
)

# ─── Module-level constants ───
logger = get_logger("test_ui_regression")

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

TIME_PATTERN = re.compile(r"\b([01]?\d|2[0-3]):[0-5]\d\b")

LOW, HIGH = 2.00, 3.00

EXPECTED_MARKERS = ("profile", "my bets", "history", "wallet")

PANEL_SELECTOR = (
    "[class*='panel' i], [class*='popover' i], "
    "[class*='dropdown' i], [class*='drawer' i]"
)

# Stake input test cases: (typed text, expected displayed value)
STAKE_CASES = (("-5", "5"), ("1e9", "19"), ("10.999", "10.99"), ("0", "0"))

# ═══════════════════════════════════════════════════════════════════
# TC-009 (new): team ordering across the card
# ════════════════════════════════════════════════════════════════════

def check_tc009_team_ordering() -> None:
    """
    TC-009 - Verify home team renders left of away, competition visible.

    Strategy: Cross-check the rendered card against the API entry for the same
    match. A swapped pair would be caught nowhere else - the bet would be
    accepted, charged and settled correctly, just against the wrong team.

    Steps:
      1. Open the app and render the match list.
      2. Take the first UPCOMING match from the catalog.
      3. Locate its card and read both team names left-to-right.
      4. Assert left name is homeTeam, right is awayTeam.
      5. Assert competition name appears on the card.

    Expected: left = homeTeam, right = awayTeam, competition visible.

    Cost: FREE - no bet is placed.
    Returns: None. Raises AssertionError on mismatch.
    """
    with UI() as ui:
        ui.openApp()
        cards = visible_cards(ui)
        assert cards, "no match cards rendered"

        upcoming = pick_upcoming_match(get_matches())
        home, away = str(upcoming["homeTeam"]), str(upcoming["awayTeam"])
        competition = str(upcoming["competition"])
        logger.info(f"TC-009 comparing card against API: {home} vs {away}")

        card = next(
            (c for c in cards if home.split()[0] in c.text and away.split()[0] in c.text),
            None,
        )
        assert card is not None, f"no card found for {home} vs {away}"

        text = " ".join(card.text.split())
        assert home in text and away in text, f"card missing a team: {text[:160]}"
        assert text.index(home) < text.index(away), (
            f"team order reversed on the card: {text[:160]} "
            f"(home '{home}' must appear before away '{away}')"
        )
        assert competition.lower() in text.lower(), (
            f"competition '{competition}' not visible: {text[:160]}"
        )

        logger.info(f"TC-009 order OK; competition '{competition}' visible")


def test_tc009_team_ordering() -> None:
    """
    TC-009 - UI test: home team renders left of away, competition visible.

    Strategy: Cross-check rendered card against API entry for that match.

    Steps:
      1. Open app and render match list.
      2. Take first UPCOMING match from catalog.
      3. Assert card shows home before away, competition visible.

    Expected: Correct left-to-right order, competition visible.

    Cost: FREE - no bet placed.
    Args: None (pytest fixture).
    Returns: None. Raises AssertionError on mismatch.
    """
    check_tc009_team_ordering()


# ═══════════════════════════════════════════════════════════════════
# TC-009 - match display, team ordering and card data
# ═══════════════════════════════════════════════════════════════════

def check_tc009_match_card_data() -> None:
    """
    TC-009 - Match cards expose 1/X/2 odds buttons with in-range decimal odds.

    Strategy: Parse every odds-like button text, keep numerics, verify the first
    nine (3 matches x 3 outcomes) sit inside the 1.01-1000.00 business band.
    Non-numeric buttons (e.g. filter controls sharing an odd* class) are skipped.

    Steps:
      1. Open the app; collect odds buttons via helper.
      2. Parse trailing decimals; require >= 9 values.
      3. Assert each of first nine within [1.01, 1000.00]; assert counter text.

    Expected: >= 9 odds values, all in range, "Showing ... matches" present.

    Cost: FREE - no bet is placed.
    Returns: None. Raises AssertionError on offending value.
    """
    with UI() as ui:
        ui.openApp()
        buttons = odds_buttons(ui._need_driver())
        values: list[float] = []
        for button in buttons:
            try:
                values.append(float((button.text or "").strip().split()[-1]))
            except ValueError:
                continue  # e.g. filter controls sharing an "odd*" class
        assert len(values) >= 9, f"expected >=9 odds values, found {len(values)}"
        for value in values[:9]:  # first 3 matches x 3 outcomes
            assert 1.01 <= value <= 1000.00, f"odds out of range: {value}"
        cards = ui.pageText()
        assert "Showing" in cards and "matches" in cards, "match counter missing"
        logger.info(f"odds buttons: {len(buttons)} (first 9 in range)")


def test_tc009_match_card_data() -> None:
    """
    TC-009 - Match cards expose 1/X/2 odds buttons with in-range decimal odds.

    Strategy: Parse every odds-like button text, keep numerics, verify the first
    nine (3 matches x 3 outcomes) sit inside the 1.01-1000.00 business band.

    Steps:
      1. Open the app; collect odds buttons via helper.
      2. Parse trailing decimals; require >= 9 values.
      3. Assert each of first nine within [1.01, 1000.00]; assert counter text.

    Expected: >= 9 values, all in range, "Showing ... matches" present.

    Cost: FREE.
    Args: None (pytest fixture).
    Returns: None. Raises AssertionError on offending value.
    """
    check_tc009_match_card_data()


def check_tc009_kickoff_time() -> None:
    """
    TC-009 (xfail) - Cards show kickoff time and no empty placeholder slots.

    Strategy: Pin spec Section 2.1's "kickoff date/time label" requirement.
    Currently strict-xfail: SportyQAD-002 - no kickoff time; bare '-' placeholders.

    Steps:
      1. Open app and wait for match list.
      2. Assert HH:MM time appears in rendered text.
      3. Assert no bare "-" text nodes remain on cards.

    Expected: Real kickoff time present, no placeholder dashes.
    Cost: FREE.
    Returns: None. Raises AssertionError on placeholder still present.
    """
    with UI() as ui:
        ui.openApp()
        driver = ui._need_driver()
        text = ui.pageText()

        assert TIME_PATTERN.search(text), "no kickoff time (HH:MM) rendered anywhere on the page"
        assert not driver.find_elements(By.XPATH, "//*[normalize-space(text())='-']"), \
            "bare '-' placeholders still rendered on match cards"


@pytest.mark.xfail(strict=True, reason="SportyQAD-002: no kickoff time; bare '-' placeholders")
def test_tc009_kickoff_time() -> None:
    """
    TC-009 (xfail) - Cards show kickoff time and no empty placeholder slots.

    Strategy: Pin spec Section 2.1's "kickoff date/time label" requirement.

    Steps:
      1. Open app and wait for match list.
      2. Assert HH:MM time appears in rendered text.
      3. Assert no bare "-" text nodes remain on cards.

    Expected: Real kickoff time present, no placeholder dashes.
    Cost: FREE.
    Args: None (pytest fixture).
    Returns: None. Raises AssertionError when placeholder still present.
    """
    check_tc009_kickoff_time()


# ══════════════════════════════════════════════════════════════════
# TC-010 - the bet slip must block an incomplete bet
# ══════════════════════════════════════════════════════════════════

def check_tc010_incomplete_slip_blocks() -> None:
    """
    TC-010 - The bet slip blocks placement without both selection and stake.

    Strategy: Assert control is absent with no selection (SportyQAD-013) and
    present-but-disabled once a selection exists but no stake.

    Steps:
      1. Open app with empty slip; assert no Place Bet element exists.
      2. Assert empty-slip prompt is shown.
      3. Select first odds; assert exactly one Place Bet appears, disabled.

    Expected: No control without selection; disabled control with selection only.
    Cost: FREE.
    Returns: None. Raises AssertionError on violated state.
    """
    with UI() as ui:
        ui.openApp()
        assert _place_bet_visible(ui) == [], "Place Bet rendered with no selection"
        assert slip_is_empty(ui), "empty-slip prompt missing"

        select_odds(ui, match_index=0, outcome="1")
        after = _place_bet_visible(ui)
        assert len(after) == 1, f"expected 1 Place Bet after selection, saw {len(after)}"
        assert not after[0].is_enabled(), "Place Bet enabled with no stake entered"
        logger.info("no-selection blocks; selected-without-stake disabled")


def test_tc010_incomplete_slip_blocks() -> None:
    """
    TC-010 - The bet slip blocks placement without both inputs.

    Strategy: Assert control absent with no selection (SportyQAD-013) and
    present-but-disabled once a selection exists but no stake.

    Steps:
      1. Open app with empty slip; assert no Place Bet element exists.
      2. Assert empty-slip prompt shown.
      3. Select first odds; assert exactly one Place Bet appears, disabled.

    Expected: No control without selection; disabled control with selection only.
    Cost: FREE.
    Args: None (pytest fixture).
    Returns: None. Raises AssertionError on violated state.
    """
    check_tc010_incomplete_slip_blocks()


# ═══════════════════════════════════════════════════════════════════
# App shell, transport and resilience
# ══════════════════════════════════════════════════════════════════

def check_app_loads() -> None:
    """Verify app shell loads with rendered, non-empty match list."""
    with UI() as ui:
        ui.openApp()
        assert ui.pageText(), "page body is empty"
        assert "Upcoming Football Matches" in ui.pageText(), "match list heading missing"
        assert "Showing" in ui.pageText() and "matches" in ui.pageText(), "match counter missing"


def test_app_loads() -> None:
    """
    App shell loads with a rendered, non-empty match list.

    Strategy: Smoke-guard the whole UI suite - if the SPA shell, heading, or
    counter is missing, every other UI test is meaningless.

    Steps:
      1. Open the app (authed via .env USER_ID).
      2. Assert non-empty body, "Upcoming Football Matches" heading, match counter.

    Expected: All three present; any absence fails fast.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError naming missing element.
    """
    check_app_loads()


def check_https_no_mixed_content() -> None:
    """Verify all resources load over HTTPS; no mixed-content warnings."""
    with UI() as ui:
        ui.openApp()
        insecure = [u for u in page_resources(ui._need_driver()) if not u.startswith("https://")]
        assert not insecure, f"non-HTTPS resources loaded: {insecure}"
        errors = console_errors(ui._need_driver())
        mixed = [e for e in errors if "mixed" in e.lower() or "insecure" in e.lower()]
        assert not mixed, f"mixed-content console errors: {mixed}"
        logger.info(f"HTTPS-only across all resources, {len(errors)} console errors")


def test_https_no_mixed_content() -> None:
    """
    UI/security - all resources load over HTTPS; no mixed-content warnings.

    Strategy: Assert transport guarantee on every resource the SPA loaded,
    plus console scan for mixed-content/insecure warnings.

    Steps:
      1. Open app and let it finish rendering.
      2. Collect all resource URLs from Performance API.
      3. Assert every URL starts with https://; scan console for mixed content.

    Expected: Zero non-HTTPS resources, zero mixed-content warnings.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError listing offending URLs/messages.
    """
    check_https_no_mixed_content()


def check_network_resilience() -> None:
    """Verify offline/online cycle neither blanks nor corrupts the app."""
    with UI() as ui:
        ui.openApp()
        driver = ui._need_driver()

        set_offline(driver, offline=True)
        try:
            time.sleep(1)
            assert "Upcoming Football Matches" in ui.pageText(), "app blanked while offline"
        finally:
            set_offline(driver, offline=False)

        driver.refresh()
        time.sleep(4)
        text = ui.pageText()
        assert "Upcoming Football Matches" in text, "app did not recover after reconnect"
        assert "Balance" in text, "balance missing after reconnect"
        logger.info("offline-safe and recovers after reconnect")


def test_network_resilience() -> None:
    """
    UI - An offline/online cycle neither blanks nor corrupts the app.

    Strategy: Emulate network drop with CDP, assert page survives, restore
    connectivity, assert app fully reloads with data intact.

    Steps:
      1. Open app and confirm rendered.
      2. set_offline(True); assert content still present (no blank/crash).
      3. set_offline(False); refresh; assert list and balance back.

    Expected: Content preserved offline, full recovery online.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError at first failed stage.
    """
    check_network_resilience()


def check_loading_state() -> None:
    """Verify submitting shows in-progress state instead of silent no-op."""
    with UI() as ui:
        ui.openApp()
        select_and_stake(ui, match_index=0, outcome="1", amount=f"{pick_stake('min'):.2f}")
        assert wait_for_place_bet_enabled(ui, timeout=10.0), "Place Bet never enabled"

        set_offline(ui._need_driver(), offline=True)
        try:
            states = submit_and_record_states(ui, settle=3.0)
        finally:
            set_offline(ui._need_driver(), offline=False)

        assert any("placing" in label.lower() for label in states), \
            f"no in-progress state observed; labels seen: {states}"
        logger.info(f"in-progress state observed; button labels: {states}")

        close_receipt(ui)
        clear_slip(ui)


@pytest.mark.xfail(strict=False, reason="Flaky: PLACING... state not consistently captured by JS recorder")
def test_loading_state() -> None:
    """
    UI (xfail) - Submitting shows in-progress state instead of silent no-op.

    Strategy: Block network so submit cannot complete, capture button labels
    from inside the page (busy state lasts under a second).

    Steps:
      1. Open app, select odds, stake minimum.
      2. Wait until PLACE BET enabled.
      3. Emulate offline, click Place Bet, record label changes in-page.
      4. Assert "Placing..." appears; restore network and clear state.

    Expected: Button passes through in-progress label.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError listing observed labels.
    """
    check_loading_state()


# ═══════════════════════════════════════════════════════════════════
# Balance, slip and submission state
# ══════════════════════════════════════════════════════════════════

def check_balance() -> None:
    """Verify header and bet-slip balances are shown and agree."""
    with UI() as ui:
        ui.openApp()
        shown = [
            e.text.strip() for e in find_all(ui._need_driver(), By.XPATH, "//*[contains(text(), 'Balance:')]")
        ]
        shown = [s for s in shown if re.search(r"\d+\.\d{2}", s)]
        assert len(shown) >= 2, f"expected header + slip balances, saw: {shown}"
        amounts = {re.search(r"\d+\.\d{2}", s).group(0) for s in shown}  # type: ignore[union-attr]
        assert len(amounts) == 1, f"balances disagree: {shown}"
        logger.info(f"balance: {shown[0]}")


def test_balance() -> None:
    """
    Header and bet-slip balances are shown and agree.

    Strategy: Two money readouts must never diverge - collect every
    "Balance:" text, extract amounts, assert exactly one distinct value.

    Steps:
      1. Open app.
      2. Gather all visible "Balance:" element texts.
      3. Assert at least header + slip present with identical amounts.

    Expected: >= 2 balance texts, single distinct EUR amount.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError showing divergent texts.
    """
    check_balance()


def check_empty_slip() -> None:
    """Verify fresh bet slip shows badge state and select-odds prompt."""
    with UI() as ui:
        ui.openApp()
        text = ui.pageText()
        assert "Bet Slip" in text, "bet slip panel missing"
        assert "Select odds to place a bet" in text, "empty-slip prompt missing"


def test_empty_slip() -> None:
    """
    Fresh bet slip shows badge state and the select-odds prompt.

    Strategy: Guard the post-reset/close landing state - no stale selection
    may survive from a previous session, and empty copy must be present.

    Steps:
      1. Open app with no prior selection.
      2. Assert "Bet Slip" panel and "Select odds to place a bet" prompt.

    Expected: Both texts present; implicitly no selection card rendered.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError naming missing text.
    """
    check_empty_slip()


def check_error_modal() -> None:
    """Verify a blocked placement shows the spec's failure modal."""
    with UI() as ui:
        ui.openApp()
        select_odds(ui, match_index=0, outcome="1")
        enter_stake(ui, f"{pick_stake('min'):.2f}")

        submit_with_network_blocked(ui)
        close_receipt(ui)  # dismiss modal before touching slip
        clear_slip(ui)
        logger.info("error modal shown with Rebet / Close; slip cleared after dismissal")


def test_error_modal() -> None:
    """
    UI - A blocked placement shows the spec's failure modal.

    Strategy: Block network so submit fails for free, assert failure UI,
    then leave clean state.

    Steps:
      1. Open app, select odds, enter minimum stake.
      2. Submit with network blocked; wait for error modal.
      4. Require Rebet and Close actions; dismiss and clear slip.

    Expected: Modal title "Something went wrong" with Rebet and Close; no charge.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError naming missing modal element.
    """
    check_error_modal()


def check_refresh_clears_slip() -> None:
    """Verify a refresh mid-selection drops the selection."""
    with UI() as ui:
        ui.openApp()
        select_odds(ui, match_index=0, outcome="1")
        assert_page_contains(ui.pageText(), "Remove All", label="populated slip")

        refresh_page(ui)
        assert slip_is_empty(ui), "slip not empty after refresh"
        logger.info("refresh clears the slip")


def test_refresh_clears_slip() -> None:
    """
    UI - A refresh mid-selection drops the selection; no stale bet state.

    Strategy: Select odds (no stake, no charge), hard-refresh, assert slip
    back to empty state - no orphaned selection or half-bet.

    Steps:
      1. Open app; select first odds; confirm slip populated.
      2. Refresh and wait for re-render.
      3. Assert empty-slip prompt back and Remove All gone.

    Expected: Slip empty after refresh, balance unchanged.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError if stale selection survives.
    """
    check_refresh_clears_slip()


def check_rapid_match_switching() -> None:
    """Verify rapid switching across matches keeps one selection, stable odds."""
    with UI() as ui:
        ui.openApp()

        first = select_odds(ui, match_index=0, outcome="1")
        for index in (1, 2, 3, 4):
            select_odds(ui, match_index=index, outcome="1")
            time.sleep(0.15)

        slip = slip_text(ui)
        assert_single_selection(slip)
        assert_page_contains(slip, "remove all", "odds:", label="bet slip")

        current = select_odds(ui, match_index=0, outcome="1")[1]
        assert current == first[1], f"odds drifted within session: {first[1]} -> {current}"

        clear_slip(ui)
        assert slip_is_empty(ui), "slip not cleared after Remove All"
        logger.success(f"rapid switching OK - single selection, odds stable at {first[1]}")


def test_rapid_match_switching() -> None:
    """
    UI - Switching across matches fast never duplicates or orphans a selection.

    Strategy: Select five outcomes on five matches in quick succession, then
    prove slip holds exactly one selection, and first match's odds unchanged
    (spec: odds static for session).

    Steps:
      1. Open app; select matches 0-4 in rapid succession.
      2. Assert exactly one selection, Remove All and odds present in slip.
      3. Re-read match 0's odds and compare; clear via Remove All.

    Expected: One consistent selection, stable odds, clean clear.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError describing broken slip state.
    """
    check_rapid_match_switching()


# ═══════════════════════════════════════════════════════════════════
# Stake entry and validation
# ══════════════════════════════════════════════════════════════════

def check_stake_input_filtering() -> None:
    """Verify stake field enforces numeric filtering at keystroke level."""
    with UI() as ui:
        ui.openApp()
        select_odds(ui, match_index=0, outcome="1")
        field = _stake_field(ui)

        for typed, expected in STAKE_CASES:
            field.clear()
            field.send_keys(typed)
            time.sleep(0.3)
            actual = field.get_attribute("value")
            assert actual == expected, f"typed {typed!r}: expected {expected!r}, got {actual!r}"
        clear_slip(ui)
        logger.success(f"stake input filtering OK ({len(STAKE_CASES)} cases)")


def test_stake_input_filtering() -> None:
    """
    UI - Stake field enforces numeric filtering at keystroke level.

    Strategy: Exercise input's own guard rails so invalid values cannot be
    typed, independent of server-side 422s.

    Steps:
      1. Open app and select odds (renders stake field).
      2. Type -5, 1e9, 10.999 and 0 in turn; compare displayed value.
      3. Assert each displayed value matches expected coercion.

    Expected: Sign stripped, exponent mangled, third decimal truncated, zero kept.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError with actual vs expected value.
    """
    check_stake_input_filtering()


def check_stake_validation_messages() -> None:
    """Verify below-minimum stake shows spec's minimum message, no charge."""
    before = balance_now()
    with UI() as ui:
        ui.openApp()
        select_odds(ui, match_index=0, outcome="1")
        enter_stake(ui, f"{pick_stake('below_min'):.2f}")

        submit_bet(ui)
        assert_page_contains(ui.pageText(), MIN_STAKE_MESSAGE, "1.00", label="bet slip error")
        logger.info("minimum-stake message shown for a below-minimum stake")
        clear_slip(ui)

    assert_balance_unchanged(before)


def test_stake_validation_messages() -> None:
    """
    UI - Below-minimum stake shows spec's minimum message, no charge.

    Strategy: Verify UI half of spec Section 4.4 that API tests cannot cover,
    and prove rejected attempt never becomes a placed bet.

    Steps:
      1. Record balance.
      2. Select odds, enter 0.50, click Place Bet.
      3. Assert "Minimum stake" and 1.00 boundary appear in slip.
      4. Re-read balance and assert unchanged.

    Expected: Minimum message displayed, balance identical before/after.
    Cost: FREE (rejected bet).
    Args: None.
    Returns: None. Raises AssertionError with slip tail when copy absent.
    """
    check_stake_validation_messages()


# ══════════════════════════════════════════════════════════════════
# Filters, popover and profile (known defects tracked as strict xfail)
# ══════════════════════════════════════════════════════════════════

def check_filters() -> None:
    """Verify Date and Odds filters exist; odds panel opens with range controls."""
    with UI() as ui:
        ui.openApp()
        ui.clickOnButton("Date: All")
        ui.clickOnButton("Odds: All")
        text = ui.pageText()
        for marker in ("ODDS RANGE", "MIN", "MAX", "Apply", "Reset"):
            assert marker in text, f"odds panel marker missing: {marker}"


def test_filters() -> None:
    """
    Date and Odds filters exist; odds panel opens with range controls.

    Strategy: Exercise both filter entry points and confirm odds panel
    exposes full range UI (no placement, no apply side-effects asserted).

    Steps:
      1. Open app.
      2. Click "Date: All", then "Odds: All".
      3. Assert ODDS RANGE / MIN / MAX / Apply / Reset markers in page text.

    Expected: All five markers present.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError naming missing marker.
    """
    check_filters()


def check_date_filter_applies() -> None:
    """Verify single-day date filter reduces list correctly."""
    with UI() as ui:
        ui.openApp()
        shown, cards = _apply_single_day(ui)
        assert len(cards) < 103, f"filter did not reduce list: {len(cards)} cards"

        dates = card_dates(ui)
        assert dates, "no dates readable from filtered cards"
        assert len(set(dates)) == 1, f"single-day filter returned mixed dates: {sorted(set(dates))}"
        logger.success(f"single-day filter OK: {len(cards)} cards, all on {dates[0]}")


def test_date_filter_applies() -> None:
    """
    UI - Applying one calendar day leaves only that day's matches.

    Strategy: Pick a day with fixtures, verify rendered cards not counter.

    Steps:
      1. Open app.
      2. Open Date panel, choose day with fixtures, Apply.
      3. Assert fewer cards remain and every card shares one date.

    Expected: Reduced list whose cards all carry same date.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError describing card count or date spread.
    """
    check_date_filter_applies()


def check_counter_updates() -> None:
    """Verify match counter equals rendered cards after filtering."""
    with UI() as ui:
        ui.openApp()
        shown, cards = _apply_single_day(ui)
        assert shown == len(cards), \
            f"counter says {shown} but {len(cards)} cards rendered"


@pytest.mark.xfail(strict=True, reason="SportyQAD-015: counter keeps unfiltered total")
def test_match_counter_updates() -> None:
    """
    UI (xfail) - Match counter equals rendered cards after filtering.

    Strategy: Filter works, question is whether counter tells truth.

    Steps:
      1. Open app; apply single-day date filter.
      2. Compare "Showing N matches" counter with rendered card count.
      3. Assert they agree.

    Expected: Counter equals rendered card count.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError with both numbers on mismatch.
    """
    check_counter_updates()


def check_odds_range_filter() -> None:
    """Verify valid odds min/max range accepted and filters list correctly."""
    with UI() as ui:
        ui.openApp()
        open_filter(ui, "Odds")
        time.sleep(1)

        low, high = set_range(ui, "2", "3")
        assert low == LOW and high == HIGH, f"range fields hold {low}/{high}, expected {LOW}/{HIGH}"

        assert click_apply(ui), "no Apply button found"
        time.sleep(2)

        groups = card_odds(ui)
        assert groups, "no match cards with odds after filtering"
        for triple in groups:
            assert any(LOW <= value <= HIGH for value in triple), \
                f"match kept with no outcome inside {LOW}-{HIGH}: {triple}"
        logger.info(f"valid odds range applied cleanly: {len(groups)} matches, "
              f"each with >=1 outcome inside {LOW}-{HIGH}")


def test_odds_range_filter() -> None:
    """
    UI - Valid odds min/max range accepted and filters list correctly.

    Strategy: Close gap invalid-range test left - MAX input and valid-range
    path (spec Section 2.6, inclusive bounds).

    Steps:
      1. Open app and Odds panel.
      2. Type MIN 2 and MAX 3; assert fields hold those values.
      3. Apply; read every rendered odds triple.
      4. Assert each kept match has >=1 outcome inside range.

    Expected: MAX accepts input; filtered list respects range.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError listing match that should be dropped.
    """
    check_odds_range_filter()


def check_invalid_range_rejected() -> None:
    """Verify MIN > MAX is rejected with clear feedback."""
    with UI() as ui:
        ui.openApp()
        driver = ui._need_driver()
        ui.clickOnButton("Odds: All")
        nums = [
            i for i in find_all(driver, By.TAG_NAME, "input")
            if i.is_displayed() and (i.get_attribute("type") or "") == "number"
        ]
        assert len(nums) >= 2, "odds range inputs missing"
        nums[0].clear(); nums[0].send_keys("50")
        nums[1].clear(); nums[1].send_keys("2")
        ui.clickOnButton("Apply")
        text = ui.pageText()
        assert "invalid" in text.lower() or "must be" in text.lower(), \
            "no invalid-range feedback shown"


@pytest.mark.xfail(strict=True, reason="SportyQAD-010: invalid range silently applied")
def test_invalid_range_rejected() -> None:
    """
    TP-006 (xfail) - Invalid odds range (MIN > MAX) rejected with clear feedback.

    Strategy: Pin spec §2.6 rule by applying MIN 50 / MAX 2, demand feedback.
    Currently strict-xfailed: app coerces to 10.00-10.00, blanks list, stale
    counter (SportyQAD-010).

    Steps:
      1. Open app; open "Odds: All"; set MIN 50, MAX 2; Apply.
      2. Assert invalid-range message in page text.

    Expected: Message containing "invalid" or "must be".
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError when no feedback shown (expected today).
    """
    check_invalid_range_rejected()


def check_empty_state() -> None:
    """Verify filtering to zero matches explains itself and zeroes counter."""
    with UI() as ui:
        ui.openApp()
        driver = ui._need_driver()

        ui.clickOnButton("Odds: All")
        time.sleep(1)
        inputs = [
            i for i in find_all(driver, By.TAG_NAME, "input")
            if i.is_displayed() and (i.get_attribute("type") or "") == "number"
        ]
        assert len(inputs) >= 2, "odds range inputs missing"
        inputs[0].clear(); inputs[0].send_keys("900")
        inputs[1].clear(); inputs[1].send_keys("1000")
        time.sleep(0.5)
        ui.clickOnButton("Apply")
        time.sleep(2)

        text = ui.pageText()
        lowered = text.lower()
        assert "no match" in lowered or "no result" in lowered or "0 matches" in lowered, \
            "no empty-state copy after filtering to zero matches"
        counter = re.search(r"Showing\s+(\d+)\s+matches", text)
        assert counter is None or counter.group(1) == "0", \
            f"counter stale after empty result: {counter.group(0) if counter else 'n/a'}"


@pytest.mark.xfail(strict=True, reason="SportyQAD-010: blank list, stale counter, no empty-state copy")
def test_empty_state() -> None:
    """
    UI (xfail) - Filtering to zero matches explains itself and zeroes counter.

    Strategy: Force impossible odds range, require explicit empty state
    plus accurate counter (spec Section 2.6 feedback).

    Steps:
      1. Open Odds panel; set MIN 900, MAX 1000; Apply.
      2. Assert empty-state message appears.
      3. Assert match counter reads 0 (or absent), not pre-filter total.

    Expected: Clear "no matches" copy and truthful counter.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError describing blank state (expected today).
    """
    check_empty_state()


def check_popover_does_not_cover_cards() -> None:
    """Verify open odds panel never hides the rows it is filtering."""
    with UI() as ui:
        ui.openApp()
        open_filter(ui, "Odds")
        time.sleep(1)
        assert _panel(ui) is not None, "odds panel did not open"
        panel_box = _box(_panel(ui))
        cards = visible_cards(ui)
        assert cards, "no match cards found"
        covered = [c for c in cards if _overlaps(panel_box, _box(c))]
        assert not covered, f"odds panel covers {len(covered)} of {len(cards)} match cards"


def check_popover_dismisses_on_outside_click() -> None:
    """Verify popover closes when user clicks outside it."""
    with UI() as ui:
        ui.openApp()
        open_filter(ui, "Odds")
        time.sleep(1)
        assert _panel(ui) is not None, "odds panel did not open"

        heading = find_all(ui._need_driver(), By.TAG_NAME, "h2")
        if heading:
            ui._need_driver().execute_script("arguments[0].click();", heading[0])
            time.sleep(1.5)
            assert _panel(ui) is None, "panel survived outside click on page heading"

        ui._need_driver().execute_script(
            "var e = document.elementFromPoint(1200, 600); if (e) { e.click(); }"
        )
        time.sleep(1.5)
        assert _panel(ui) is None, "panel survived click on empty space"


@pytest.mark.xfail(strict=True, reason="SportyQAD-004: odds popover overlays match cards")
def test_popover_does_not_cover_cards() -> None:
    """
    UI (xfail) - Open odds panel never hides rows it is filtering.

    Strategy: Compare bounding rectangles instead of judging layout by eye.

    Steps:
      1. Open app and Odds panel.
      2. Locate panel element and every visible match card.
      3. Assert no card rectangle intersects panel rectangle.

    Expected: Zero overlapping cards.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError with overlap count (expected today).
    """
    check_popover_does_not_cover_cards()


@pytest.mark.xfail(strict=True, reason="SportyQAD-004: popover survives outside click and Escape")
def test_popover_dismisses_on_outside_click() -> None:
    """
    UI (xfail) - Popover closes when user clicks outside it.

    Strategy: Open panel, click neutral area; popover must go.

    Steps:
      1. Open Odds panel.
      2. Click page heading (outside panel).
      3. Assert panel closed; repeat with click on empty space.

    Expected: Popover dismisses on outside click.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError when panel stays open (expected today).
    """
    check_popover_dismisses_on_outside_click()


def check_profile_icon_opens_details() -> None:
    """Verify avatar opens profile details and route to bet history / wallet."""
    with UI() as ui:
        ui.openApp()
        driver = ui._need_driver()
        before = ui.pageText()

        icons = driver.find_elements(By.XPATH, "//*[normalize-space(text())='person']")
        assert icons, "profile icon not found in header"
        icons[0].click()
        time.sleep(2)

        after = ui.pageText()
        assert after != before, "clicking profile icon changed nothing"
        lowered = after.lower()
        assert any(marker in lowered for marker in EXPECTED_MARKERS), \
            "no profile, history or wallet content appeared"


@pytest.mark.xfail(strict=True, reason="SportyQAD-009: profile icon has no click handler")
def test_profile_icon_opens_details() -> None:
    """
    UI (xfail) - Avatar opens profile details and route to bet history/wallet.

    Strategy: Pin reachable-account expectation; today control is dead.

    Steps:
      1. Open app and record page text.
      2. Click header person icon.
      3. Assert page changed and shows profile/history/wallet markers.

    Expected: Some account surface opens.
    Cost: FREE.
    Args: None.
    Returns: None. Raises AssertionError when nothing opens (expected today).
    """
    check_profile_icon_opens_details()


# ─── SportyQAD-022: Balance header does not update in real-time after bet ───
def check_balance_updates_realtime_after_bet() -> None:
    """SportyQAD-022 — header balance updates in real-time after successful bet.

    Strategy: place a bet via UI, then assert the header balance reflects the new
    amount WITHOUT a page refresh. Currently the header stays stale until refresh.

    Steps:
      1. Record API and UI header balance before bet.
      2. Select odds, enter stake, submit bet, wait for receipt.
      3. Read header balance immediately (no refresh).
      4. Assert header balance equals API balance (both decreased by stake).

    Expected: header balance matches API balance after bet.
    Cost: CHARGED (€1.00) — gated behind --run-bet.
    """
    try:
        # Get initial balances
        api_before = get_balance()
        with UI() as ui:
            open_app(ui)
            time.sleep(1.5)
            ui_before = ui.readBalance()

            # Place bet via UI
            match_id = str(pick_match(get_matches(), future=True)["id"])
            assert match_id, "no upcoming match id resolved"
            select_odds(ui, match_index=0, outcome="1")
            enter_stake(ui, "1.00")
            assert wait_for_place_bet_enabled(ui, timeout=10.0), "Place Bet never enabled"
            submit_bet(ui)

            # Wait for receipt (success)
            wait_for_receipt(ui)

            # Read header balance immediately after receipt (no refresh)
            ui_after = ui.readBalance()

        api_after = get_balance()

        # Both should decrease by ~1.00
        expected_delta = round(api_before - 1.00, 2)
        assert api_after == expected_delta, f"API balance {api_after} != expected {expected_delta}"
        # UI header should match API
        match = re.search(r"[\d.]+", ui_after)
        assert match is not None, f"no amount rendered in the header balance: {ui_after!r}"
        ui_after_val = float(match.group())
        assert ui_after_val == api_after, (
            f"UI header balance {ui_after_val} != API balance {api_after} — "
            f"header stale until refresh (SportyQAD-022)"
        )
    finally:
        teardown_reset_balance_silent()


@pytest.mark.skipif("not config.getoption('--run-bet')", reason="spends balance — rerun with --run-bet")
@pytest.mark.xfail(strict=True, reason="SportyQAD-022: header balance does not update in real-time after bet")
def test_balance_updates_realtime_after_bet() -> None:
    """UI (xfail) - header balance reflects new amount immediately after bet (SportyQAD-022)."""
    check_balance_updates_realtime_after_bet()


setattr(check_balance_updates_realtime_after_bet, "xfail_reason", "SportyQAD-022")
setattr(check_balance_updates_realtime_after_bet, "requires", ["--run-bet"])


# ─── xfail reasons for direct-run mode ───
setattr(check_tc009_kickoff_time, "xfail_reason", "SportyQAD-002")
setattr(check_popover_does_not_cover_cards, "xfail_reason", "SportyQAD-004")
setattr(check_popover_dismisses_on_outside_click, "xfail_reason", "SportyQAD-004")
setattr(check_profile_icon_opens_details, "xfail_reason", "SportyQAD-009")
setattr(check_balance_updates_realtime_after_bet, "xfail_reason", "SportyQAD-022")


# ═══════════════════════════════════════════════════════════════════
# Entry point for direct execution (without pytest)
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    testInitialization.Configure(title="test_ui_regression")
    testInitialization.testSuite(
        check_tc009_team_ordering,
        check_tc009_match_card_data,
        check_tc009_kickoff_time,
        check_tc010_incomplete_slip_blocks,
        check_app_loads,
        check_https_no_mixed_content,
        check_network_resilience,
        check_loading_state,
        check_balance,
        check_empty_slip,
        check_error_modal,
        check_refresh_clears_slip,
        check_rapid_match_switching,
        check_stake_input_filtering,
        check_stake_validation_messages,
        check_filters,
        check_date_filter_applies,
        check_counter_updates,
        check_odds_range_filter,
        check_invalid_range_rejected,
        check_empty_state,
        check_popover_does_not_cover_cards,
        check_popover_dismisses_on_outside_click,
        check_profile_icon_opens_details,
        check_balance_updates_realtime_after_bet,
    )
    testInitialization.run()