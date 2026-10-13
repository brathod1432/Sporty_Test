"""UI test-step functions: reusable verbs for browser interactions and assertions."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import re
import time

from libs.logger import get_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from testfunctions.assert_functions import ERROR_MODAL_TITLE, assert_page_contains
from testfunctions.data_functions import pick_match_by_date, pick_stake, pick_upcoming_match
from testfunctions.modal_functions import clear_slip, close_receipt, is_modal_open
from testfunctions.ui_helper import UI, find_all, odds_buttons, poll_until, set_offline, wait_for_content

logger = get_logger("ui_functions")

RECEIPT_MAX_WAIT: float = 25.0
ERROR_MODAL_MAX_WAIT: float = 30.0
OUTCOMES: tuple[str, ...] = ("1", "X", "2")
CARD_SELECTOR: str = "[class*='card'], [class*='Card']"
DATE_PATTERN = re.compile(r"\b\w{3}\s+\d{1,2}\s+\w{3}\b")
ODDS_PATTERN = re.compile(r"\b\d+\.\d{2}\b")
COUNTER_PATTERN = re.compile(r"Showing\s+(\d+)\s+matches")

_JS_CLICK_TEXT = """
var want = arguments[0];
var nodes = document.querySelectorAll('button');
for (var i = 0; i < nodes.length; i++) {
  // Skip buttons inside collapsed/hidden panels, otherwise a hidden
  // "Apply" from the other filter steals the click.
  if (!nodes[i].offsetParent && nodes[i].offsetWidth === 0) { continue; }
  var t = (nodes[i].innerText || nodes[i].textContent || '').trim().toLowerCase();
  if (t === want) { nodes[i].click(); return true; }
}
return false;
"""


# --- page / state -----------------------------------------------------------


def open_app(ui: UI) -> UI:
    """Open the app and wait for the SPA to finish rendering.

    Args:
        ui: an initialised UI facade.
    Returns:
        The same facade, for chaining.
    """
    return ui.openApp()


def page_text(ui: UI) -> str:
    """Full visible page text.

    Args:
        ui: facade.
    Returns:
        The body text.
    """
    return ui.pageText()


def match_count(ui: UI) -> int:
    """Number of matches the UI claims to be showing.

    Args:
        ui: facade with the app open.
    Returns:
        The parsed count, or -1 when the counter is missing.
    """
    match = COUNTER_PATTERN.search(ui.pageText())
    return int(match.group(1)) if match else -1


def visible_cards(ui: UI) -> list:
    """Every currently visible match card element.

    Args:
        ui: facade.
    Returns:
        The card elements.
    """
    return [el for el in find_all(ui._need_driver(), By.CSS_SELECTOR, CARD_SELECTOR) if el.is_displayed()]


def card_dates(ui: UI) -> list[str]:
    """Dates rendered on the visible cards, e.g. "Fri 27 Feb".

    Args:
        ui: facade.
    Returns:
        One entry per card that shows a date.
    """
    out: list[str] = []
    for card in visible_cards(ui):
        for line in (card.text or "").split("\n"):
            if DATE_PATTERN.fullmatch(line.strip()):
                out.append(line.strip())
    return out


def card_odds(ui: UI) -> list[list[float]]:
    """Odds values grouped per visible card (the 1/X/2 triple).

    Args:
        ui: facade.
    Returns:
        One triple per card that has odds.
    """
    groups: list[list[float]] = []
    for card in visible_cards(ui):
        values = [float(t) for t in ODDS_PATTERN.findall(card.text or "")]
        if len(values) >= 3:
            groups.append(values[-3:])
    return groups


def filter_label(ui: UI, which: str = "Date") -> str:
    """Text of a filter control, e.g. "Date: 10/10/2026".

    Args:
        ui: facade.
        which: "Date" or "Odds".
    Returns:
        The label text, or an empty string when absent.
    Raises:
        ValueError: for an unsupported filter name.
    """
    if which not in ("Date", "Odds"):
        msg = f"unknown filter {which!r}; use 'Date' or 'Odds'"
        logger.error(msg)
        raise ValueError(msg)
    for button in find_all(ui._need_driver(), By.TAG_NAME, "button"):
        text = (button.text or "")
        if which in text and button.is_displayed():
            return text.replace("\n", " ")
    return ""


# --- slip -------------------------------------------------------------------


def _odds_values(driver) -> list[tuple[str, float]]:
    """(label, value) for every genuine odds button, skipping filter buttons."""
    out: list[tuple[str, float]] = []
    for button in odds_buttons(driver):
        parts = (button.text or "").strip().split()
        if not parts:
            continue
        try:
            value = float(parts[-1])
        except ValueError:
            continue
        if 1.01 <= value <= 1000.0 and len(parts) >= 2:
            out.append((parts[0], value))
    return out


def select_odds(ui: UI, match_index: int = 0, outcome: str = "1") -> tuple[str, float]:
    """Click an outcome button (fills the slip; places nothing).

    Args:
        ui: facade with the app open.
        match_index: 0-based match index, counting 3 odds buttons per match.
        outcome: "1" (home), "X" (draw) or "2" (away).
    Returns:
        The (label, value) of the button clicked.
    Raises:
        ValueError: for an unknown outcome.
        AssertionError: when the button cannot be resolved.
    """
    if outcome not in OUTCOMES:
        msg = f"unknown outcome {outcome!r}; use {OUTCOMES}"
        logger.error(msg)
        raise ValueError(msg)
    target = match_index * 3 + OUTCOMES.index(outcome)
    buttons = _odds_values(ui._need_driver())
    if target >= len(buttons):
        msg = f"no odds button at index {target} (only {len(buttons)} found)"
        logger.error(msg)
        raise AssertionError(msg)
    label, value = buttons[target]
    _click_odds(ui, target)
    return label, value


def _click_odds(ui: UI, index: int) -> None:
    """Click the Nth genuine odds button by resolving them the same way."""
    seen = 0
    for button in odds_buttons(ui._need_driver()):
        parts = (button.text or "").strip().split()
        if not parts:
            continue
        try:
            value = float(parts[-1])
        except ValueError:
            continue
        if 1.01 <= value <= 1000.0 and len(parts) >= 2:
            if seen == index:
                button.click()
                time.sleep(0.8)
                return
            seen += 1


def enter_stake(ui: UI, amount: str = "1.00") -> str:
    """Type a stake into the bet slip (never submits).

    Args:
        ui: facade with a selection already made.
        amount: the stake text to enter.
    Returns:
        The amount entered.
    Raises:
        AssertionError: when no stake field is visible.
    """
    fields = [i for i in find_all(ui._need_driver(), By.TAG_NAME, "input")
              if i.is_displayed() and (i.get_attribute("placeholder") or "") == "0.00"]
    if not fields:
        msg = "stake field not visible - make a selection first"
        logger.error(msg)
        raise AssertionError(msg)
    fields[0].click()
    fields[0].send_keys(amount)
    time.sleep(0.6)
    return amount


def select_and_stake(ui: UI, match_index: int = 0, outcome: str = "1", amount: str = "1.00") -> tuple[str, float]:
    """Select an outcome and enter a stake in one step.

    Args:
        ui: facade with the app open.
        match_index: 0-based match index.
        outcome: "1", "X" or "2".
        amount: stake text.
    Returns:
        The (label, value) of the odds button selected.
    """
    picked = select_odds(ui, match_index, outcome)
    enter_stake(ui, amount)
    return picked


def slip_text(ui: UI) -> str:
    """Text of the bet-slip panel only.

    Args:
        ui: facade with the app open.
    Returns:
        The panel text, or an empty string when it cannot be located.
    """
    for element in find_all(ui._need_driver(), By.TAG_NAME, "aside") + \
            find_all(ui._need_driver(), By.TAG_NAME, "section"):
        text = element.text or ""
        if "Bet Slip" in text:
            return text
    return ""


def slip_is_empty(ui: UI) -> bool:
    """Whether the bet slip is in its empty state.

    Args:
        ui: facade.
    Returns:
        True when the "Select odds" prompt is shown and no Remove All is present.
    """
    text = ui.pageText()
    return "Select odds to place a bet" in text and "Remove All" not in text


def slip_balance(ui: UI) -> str:
    """The balance line shown inside the bet slip.

    Args:
        ui: facade.
    Returns:
        The balance line from the slip, or an empty string.
    """
    for line in slip_text(ui).split("\n"):
        if line.strip().lower().startswith("balance"):
            return line.strip()
    return ""


def read_balance(ui: UI) -> str:
    """Header balance text as rendered.

    Args:
        ui: facade with the app open.
    Returns:
        The balance line.
    """
    return ui.readBalance()


def place_bet_buttons(ui: UI) -> list[str]:
    """Labels of the Place Bet control, including the busy state ("plac").

    Args:
        ui: facade.
    Returns:
        The current button labels.
    """
    return [(b.text or "").strip() for b in find_all(ui._need_driver(), By.TAG_NAME, "button")
            if "plac" in (b.text or "").strip().lower() and b.is_displayed()]


def place_bet_enabled(ui: UI) -> bool:
    """Whether the PLACE BET control is present and enabled.

    Args:
        ui: facade.
    Returns:
        True when a visible, enabled Place Bet button exists.
    """
    for button in find_all(ui._need_driver(), By.TAG_NAME, "button"):
        label = (button.text or "").strip().lower()
        if "place bet" in label or label == "placing...":
            return button.is_displayed() and button.is_enabled()
    return False


def wait_for_place_bet_enabled(ui: UI, timeout: float = 10.0) -> bool:
    """Wait until PLACE BET becomes enabled (selection and stake both accepted).

    Prefer this over a fixed sleep: the button enables asynchronously once React
    has processed the odds selection and the typed stake.

    Args:
        ui: facade with a selection and a stake entered.
        timeout: how long to wait.
    Returns:
        True when the button is enabled within the timeout.
    """
    return poll_until(ui._need_driver(), lambda: place_bet_enabled(ui), timeout=timeout, interval=0.2)


def wait_for_placing_state(ui: UI, timeout: float = 8.0) -> bool:
    """Poll until the Place Bet control reports an in-progress state.

    Args:
        ui: facade after a submit.
        timeout: how long to wait.
    Returns:
        True when the busy state was observed.
    """
    return poll_until(
        ui._need_driver(),
        lambda: any("placing" in label.lower() for label in place_bet_buttons(ui)),
        timeout=timeout,
        interval=0.1,
    )


# --- filters ----------------------------------------------------------------


def open_filter(ui: UI, which: str = "Odds") -> None:
    """Open a filter panel.

    Args:
        ui: facade.
        which: "Date" or "Odds".
    """
    ui.clickOnButton(f"{which}: All")


def range_inputs(ui: UI) -> list:
    """The visible number inputs of an open odds-range panel.

    Args:
        ui: facade with the odds panel open.
    Returns:
        MIN then MAX inputs.
    """
    return [i for i in find_all(ui._need_driver(), By.TAG_NAME, "input")
            if i.is_displayed() and (i.get_attribute("type") or "") == "number"]


def set_range(ui: UI, low: str, high: str) -> tuple[float, float]:
    """Type MIN and MAX values into an open odds-range panel.

    Uses ctrl+A rather than clear(), because these inputs are bound to sliders.

    Args:
        ui: facade with the odds panel open.
        low: MIN text.
        high: MAX text.
    Returns:
        The resulting numeric values.
    Raises:
        AssertionError: when the panel does not expose two inputs.
    """
    inputs = range_inputs(ui)
    if len(inputs) < 2:
        msg = f"expected MIN and MAX inputs, found {len(inputs)}"
        logger.error(msg)
        raise AssertionError(msg)
    for field, value in ((inputs[0], low), (inputs[1], high)):
        field.click()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(value)
        time.sleep(0.3)
    return float(inputs[0].get_attribute("value")), float(inputs[1].get_attribute("value"))


def click_apply(ui: UI) -> bool:
    """Click the first exact-text Apply button via JS (no selector ambiguity).

    Args:
        ui: facade with a filter panel open.
    Returns:
        True when a button was clicked.
    """
    return bool(ui._need_driver().execute_script(_JS_CLICK_TEXT, "apply"))


def calendar_days(ui: UI) -> list:
    """Day buttons of an open calendar panel.

    Args:
        ui: facade with the date panel open.
    Returns:
        The day-cell buttons.
    """
    return [d for d in find_all(ui._need_driver(), By.TAG_NAME, "button")
            if re.fullmatch(r"\d{1,2}", (d.text or "").strip()) and d.is_displayed()]


def select_calendar_day(ui: UI, day: int) -> None:
    """Click a specific day in the open calendar.

    Args:
        ui: facade with the date panel open.
        day: day of month.
    Raises:
        AssertionError: when the day is not offered.
    """
    match = next((d for d in calendar_days(ui) if (d.text or "").strip() == str(day)), None)
    if match is None:
        msg = f"day {day} not offered in the calendar"
        logger.error(msg)
        raise AssertionError(msg)
    match.click()
    time.sleep(0.8)


# --- submission / outcomes --------------------------------------------------


def submit_bet(ui: UI) -> None:
    """Click PLACE BET.

    Args:
        ui: facade with a selection and a stake.
    Raises:
        LookupError: when the button is not present.
    """
    ui.clickOnButton("Place Bet")


def wait_for_receipt(ui: UI, timeout: float = RECEIPT_MAX_WAIT) -> str:
    """Wait for the success receipt and return the page text.

    Args:
        ui: facade after submitting.
        timeout: how long to wait.
    Returns:
        The page text containing the receipt.
    Raises:
        AssertionError: when no receipt appears.
    """
    appeared = poll_until(
        ui._need_driver(),
        lambda: "bet id" in ui.pageText().lower() or "bet placed successfully" in ui.pageText().lower(),
        timeout=timeout,
    )
    if not appeared:
        msg = f"no success receipt within {timeout}s"
        logger.error(msg)
        raise AssertionError(msg)
    return ui.pageText()


def wait_for_error_modal(ui: UI, timeout: float = ERROR_MODAL_MAX_WAIT) -> str:
    """Wait for the failure modal and return the page text.

    Args:
        ui: facade after a failed submission.
        timeout: how long to wait; observed around 8s for a real failure.
    Returns:
        The page text containing the modal.
    Raises:
        AssertionError: when the modal never appears.
    """
    appeared = poll_until(
        ui._need_driver(),
        lambda: ERROR_MODAL_TITLE.lower() in ui.pageText().lower(),
        timeout=timeout,
    )
    if not appeared:
        msg = f"no error modal within {timeout}s"
        logger.error(msg)
        raise AssertionError(msg)
    text = ui.pageText()
    assert_page_contains(text, "rebet", "close", label="error modal")
    return text


_JS_RECORD_AND_SUBMIT = """
(function () {
  window.__states = [];
  var timer = setInterval(function () {
    var b = [].slice.call(document.querySelectorAll('button'))
      .filter(function (x) { return (x.innerText || '').toLowerCase().indexOf('place bet') !== -1; })[0];
    var t = b ? (b.innerText || '').trim() : '';
    if (window.__states[window.__states.length - 1] !== t) { window.__states.push(t); }
  }, 25);
  window.__stopRecord = function () { clearInterval(timer); };

  var btn = [].slice.call(document.querySelectorAll('button'))
    .filter(function (x) { return (x.innerText || '').toLowerCase().indexOf('place bet') !== -1; })[0];
  if (btn) { btn.click(); return true; }
  return false;
})();
"""

_JS_READ_STATES = "return (window.__states || []).slice();"


def submit_and_record_states(ui: UI, settle: float = 3.0) -> list[str]:
    """Click PLACE BET and record every distinct button label it passes through.

    The in-progress label can last well under a second, which is shorter than a
    Python-side polling round trip, so the labels are sampled inside the page.

    Args:
        ui: facade with a selection and a stake; the button must be enabled.
        settle: seconds to keep recording after the click.
    Returns:
        The distinct labels observed, in order (e.g. ["PLACE BET", "PLACING..."]).
    """
    driver = ui._need_driver()
    driver.execute_script(_JS_RECORD_AND_SUBMIT)
    deadline = time.time() + settle
    while time.time() < deadline:
        time.sleep(0.25)
    try:
        driver.execute_script("if (window.__stopRecord) { window.__stopRecord(); }")
    except Exception:
        pass
    return list(driver.execute_script(_JS_READ_STATES) or [])


def submit_with_network_blocked(ui: UI) -> str:
    """Submit with the network blocked, restore it, and await the error modal.

    Free way to exercise the failure path: the request never reaches the server.

    Args:
        ui: facade with a selection and a stake.
    Returns:
        The page text containing the error modal.
    """
    set_offline(ui._need_driver(), offline=True)
    try:
        submit_bet(ui)
        return wait_for_error_modal(ui)
    finally:
        set_offline(ui._need_driver(), offline=False)


def refresh_page(ui: UI, wait: float = 4.0) -> None:
    """Reload the page and wait for the SPA to re-render.

    Args:
        ui: facade.
        wait: seconds allowed for re-render.
    """
    ui._need_driver().refresh()
    time.sleep(wait)
    wait_for_content(ui._need_driver())


# --- helpers for regression tests --------------------------------------------

PANEL_SELECTOR = (
    "[class*='panel' i], [class*='popover' i], "
    "[class*='dropdown' i], [class*='drawer' i]"
)

STAKE_CASES = (("-5", "5"), ("1e9", "19"), ("10.999", "10.99"), ("0", "0"))

EXPECTED_MARKERS = ("profile", "my bets", "history", "wallet")


def _box(element) -> dict[str, float]:
    """Bounding box with left/top/right/bottom edges."""
    rect = element.rect
    get = (lambda k: rect[k]) if isinstance(rect, dict) else (lambda k: getattr(rect, k))
    x, y = float(get("x")), float(get("y"))
    w, h = float(get("width")), float(get("height"))
    return {
        "x": x, "y": y, "width": w, "height": h,
        "left": x, "top": y, "right": x + w, "bottom": y + h,
    }


def _overlaps(a: dict[str, float], b: dict[str, float]) -> bool:
    """True when two boxes intersect."""
    return not (
        a["right"] <= b["left"] or b["right"] <= a["left"]
        or a["bottom"] <= b["top"] or b["bottom"] <= a["top"]
    )


def _panel(ui: UI):
    """Return the visible odds panel element, or None."""
    return next(
        (
            el for el in find_all(ui._need_driver(), By.CSS_SELECTOR, PANEL_SELECTOR)
            if el.is_displayed() and "ODDS RANGE" in (el.text or "").upper()
        ),
        None,
    )


def _open_odds_panel(ui: UI) -> None:
    """Open the app and the Odds filter panel, assert it opens."""
    ui.openApp()
    open_filter(ui, "Odds")
    time.sleep(1)
    assert _panel(ui) is not None, "odds panel did not open"


def _stake_field(ui: UI):
    """Return the stake input field, asserting it exists."""
    fields = [
        i for i in find_all(ui._need_driver(), By.TAG_NAME, "input")
        if i.is_displayed() and (i.get_attribute("placeholder") or "") == "0.00"
    ]
    if not fields:
        msg = "stake field not visible - make a selection first"
        logger.error(msg)
        raise AssertionError(msg)
    return fields[0]


def _place_bet_visible(ui: UI) -> list:
    """Return visible PLACE BET elements (disabled included)."""
    return [
        b for b in find_all(ui._need_driver(), By.TAG_NAME, "button")
        if "plac" in (b.text or "").strip().lower() and b.is_displayed()
    ]


def _apply_single_day(ui: UI, month: str = "10") -> tuple[int, list]:
    """Apply a one-day filter on a day that provably has fixtures."""
    target = pick_match_by_date(month)
    day = int(target.split("-")[2])
    open_filter(ui, "Date")
    time.sleep(1.2)
    select_calendar_day(ui, day)
    assert click_apply(ui), "no Apply button found"
    time.sleep(2.5)
    return match_count(ui), visible_cards(ui)


__all__ = [
    "CARD_SELECTOR",
    "DATE_PATTERN",
    "OUTCOMES",
    "ODDS_PATTERN",
    "calendar_days",
    "card_dates",
    "card_odds",
    "clear_slip",
    "click_apply",
    "close_receipt",
    "enter_stake",
    "filter_label",
    "is_modal_open",
    "match_count",
    "open_app",
    "open_filter",
    "page_text",
    "place_bet_buttons",
    "place_bet_enabled",
    "range_inputs",
    "read_balance",
    "refresh_page",
    "select_and_stake",
    "select_calendar_day",
    "select_odds",
    "set_range",
    "slip_balance",
    "slip_is_empty",
    "slip_text",
    "submit_and_record_states",
    "submit_bet",
    "submit_with_network_blocked",
    "visible_cards",
    "wait_for_error_modal",
    "wait_for_placing_state",
    "wait_for_place_bet_enabled",
    "wait_for_receipt",
    "_box",
    "_overlaps",
    "_panel",
    "_open_odds_panel",
    "_stake_field",
    "_place_bet_visible",
    "_apply_single_day",
]