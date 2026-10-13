"""Simple Selenium helpers for the Sports Betting web app.

Headless-capable Chrome driver + small page helpers. No test framework
assumed — usable from pytest or plain scripts.

Example:
    from testfunctions.ui_helper import make_driver, open_app, screenshot, quit_driver

    driver = make_driver(headless=True)
    open_app(driver, user_id="...", base_url="https://qae-assignment-tau.vercel.app")
    print("title:", driver.title)
    screenshot(driver, "tests/ui_tests/artifacts/home.png")
    quit_driver(driver)
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from libs.logger import get_logger

logger = get_logger("UIHelper")

# Common constants.
DEFAULT_TIMEOUT: float = 15.0
DEFAULT_WINDOW: tuple[int, int] = (1600, 900)
SUPPORTED_OUTCOMES: tuple[str, ...] = ("1", "X", "2")  # home / draw / away


def app_url(base_url: str, user_id: str) -> str:
    """App URL with auth query param, e.g. https://host/?user-id=<id>."""
    return f"{base_url.rstrip('/')}/?user-id={user_id}"


def make_driver(headless: bool = True, window: tuple[int, int] = DEFAULT_WINDOW) -> webdriver.Chrome:
    """Create a Chrome driver (chromedriver resolved by Selenium Manager)."""
    opts = ChromeOptions()
    if headless: opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--window-size={window[0]},{window[1]}")
    driver = webdriver.Chrome(service=ChromeService(), options=opts)
    driver.set_window_size(window[0], window[1])
    logger.info(f"Chrome driver started (headless={headless}, window={window})")
    return driver


def quit_driver(driver: webdriver.Chrome) -> None:
    """Close the driver, never raising."""
    try:
        driver.quit()
        logger.info("Chrome driver closed")
    except Exception as exc:
        logger.warning(f"Driver quit failed: {exc}")


def open_app(driver: webdriver.Chrome, user_id: str, base_url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Open the app authed as user_id; wait for the page to render. Returns final URL."""
    url = app_url(base_url, user_id)
    logger.info("Opening app")
    driver.get(url)
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
    logger.info(f"App loaded: {driver.title!r} ({url[:60]}...)")
    return driver.current_url


def wait_visible(driver: webdriver.Chrome, by: str, value: str, timeout: float = DEFAULT_TIMEOUT) -> WebElement:
    """Wait for an element to be visible; return it."""
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, value)))


def wait_clickable(driver: webdriver.Chrome, by: str, value: str, timeout: float = DEFAULT_TIMEOUT) -> WebElement:
    """Wait for an element to be clickable; return it."""
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))


def find_all(driver: webdriver.Chrome, by: str, value: str) -> list[WebElement]:
    """Find all matching elements (empty list if none)."""
    try:
        return driver.find_elements(by, value)
    except Exception as exc:
        logger.warning(f"find_all failed ({value}): {exc}")
        return []


def wait_for_content(driver: webdriver.Chrome, timeout: float = DEFAULT_TIMEOUT) -> bool:
    """Wait until the SPA has rendered (any button/input present). Returns True if content appeared."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "button")) > 0
            or len(d.find_elements(By.TAG_NAME, "input")) > 0
        )
        logger.info("Page content rendered")
        return True
    except Exception:
        logger.warning("Timed out waiting for page content")
        return False


def page_inventory(driver: webdriver.Chrome) -> dict[str, Any]:
    """Generic element census — works on any page, no app knowledge needed."""
    inv: dict[str, Any] = {"title": driver.title, "url": driver.current_url}
    for name, tag in (("buttons", "button"), ("inputs", "input"), ("links", "a"),
                      ("headings", "h1,h2,h3"), ("images", "img"), ("tables", "table")):
        try:
            if "," in tag:
                count = sum(len(driver.find_elements(By.TAG_NAME, t)) for t in tag.split(","))
            else:
                count = len(driver.find_elements(By.TAG_NAME, tag))
        except Exception:
            count = -1
        inv[name] = count
    try:
        inv["body_text_len"] = len(driver.find_element(By.TAG_NAME, "body").text)
    except Exception:
        inv["body_text_len"] = -1
    logger.info(f"Inventory: {inv}")
    return inv


def console_errors(driver: webdriver.Chrome) -> list[str]:
    """JS console errors via browser logs (empty list if unsupported)."""
    try:
        entries = driver.get_log("browser")
    except Exception as exc:
        logger.warning(f"Console logs unavailable: {exc}")
        return []
    errors = [e.get("message", "") for e in entries if e.get("level") in ("SEVERE", "ERROR")]
    if errors:
        logger.warning(f"{len(errors)} console error(s)")
    return errors


def screenshot(driver: webdriver.Chrome, path: str | Path) -> Path:
    """Save a PNG screenshot; return the path."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    driver.save_screenshot(str(dest))
    logger.info(f"Screenshot saved: {dest}")
    return dest


# --- Betting-app specific helpers (selectors discovered 2026-10-12) ---


def odds_buttons(driver: webdriver.Chrome) -> list[WebElement]:
    """All clickable odds buttons on the match list."""
    for selector in ("button[class*='odd']", "button[class*='Odd']", "[data-testid*='odd']"):
        found = find_all(driver, By.CSS_SELECTOR, selector)
        if found:
            return found
    # Fallback: buttons whose text looks like decimal odds.
    return [b for b in find_all(driver, By.TAG_NAME, "button")
            if _looks_like_odds((b.text or "").strip())]


def _looks_like_odds(text: str) -> bool:
    try:
        return 1.01 <= float(text) <= 1000.0 and "." in text
    except ValueError:
        return False


def select_outcome(driver: webdriver.Chrome, match_index: int, outcome: str,
                   timeout: float = DEFAULT_TIMEOUT) -> WebElement:
    """Click an outcome button. outcome: '1' (home), 'X' (draw), '2' (away).

    NOTE: selecting only fills the bet slip — it does NOT place a bet.
    """
    if outcome not in SUPPORTED_OUTCOMES:
        raise ValueError(f"Unknown outcome {outcome!r}. Use one of: {', '.join(SUPPORTED_OUTCOMES)}")
    buttons = odds_buttons(driver)
    if match_index >= len(buttons):
        raise IndexError(f"Only {len(buttons)} odds buttons found, asked for index {match_index}")
    buttons[match_index].click()
    logger.info(f"Selected outcome {outcome} on match index {match_index}")
    return buttons[match_index]


def set_stake(driver: webdriver.Chrome, amount: str, timeout: float = DEFAULT_TIMEOUT) -> WebElement:
    """Type a stake into the bet-slip stake input. Does NOT submit anything."""
    field = wait_visible(driver, By.CSS_SELECTOR, "input[type='number'], input[inputmode='decimal'], input[placeholder*='take' i]",
                         timeout=timeout)
    field.clear()
    field.send_keys(amount)
    logger.info(f"Stake entered: {amount}")
    return field


def place_bet(driver: webdriver.Chrome, timeout: float = DEFAULT_TIMEOUT) -> WebElement:
    """Click 'Place Bet'. DANGER: spends real (test) balance — never call in exploratory checks."""
    button = wait_clickable(driver, By.XPATH, "//button[contains(translate(., 'PLACEBET', 'placebet'), 'place bet')]",
                            timeout=timeout)
    button.click()
    logger.info("Place Bet clicked")
    return button


# --- Parallel browsers (threading + barrier sync) ---


@dataclass
class ParallelOutcome:
    """One worker's result from run_parallel. Per-worker errors never escape."""

    index: int
    ok: bool
    value: Any = None
    error: str | None = None
    elapsed_ms: float = 0.0


def run_parallel(
    operation: Callable[[webdriver.Chrome, int], Any],
    parallel_workers: int = 3,
    headless: bool = True,
    window: tuple[int, int] = DEFAULT_WINDOW,
    max_start_skew_ms: float = 50.0,
) -> list[ParallelOutcome]:
    """Open `parallel_workers` Chrome windows and run `operation(driver, index)` on all of them.

    Drivers are created on threads; a threading.Barrier then releases every worker
    at the same instant, so operations start within microseconds of each other
    (target: start skew under `max_start_skew_ms`, default 50ms — the actual skew
    is logged; a warning is logged if it ever exceeds the target).
    Every driver is quit afterwards, success or failure. One worker failing never
    affects the others: its outcome carries ok=False plus the error text.

    Example:
        def load_home(driver, index):
            open_app(driver, USER_ID, BASE_URL)
            return driver.title

        for outcome in run_parallel(load_home, parallel_workers=3):
            print(outcome.index, outcome.ok, outcome.value)
    """
    if parallel_workers < 1:
        raise ValueError(f"parallel_workers must be >= 1, got {parallel_workers}")

    outcomes: list[ParallelOutcome] = []
    drivers: list[tuple[int, webdriver.Chrome]] = []
    creation_errors: list[ParallelOutcome] = []
    lock = threading.Lock()

    def _create(index: int) -> None:
        try:
            driver = make_driver(headless=headless, window=window)
            with lock:
                drivers.append((index, driver))
        except Exception as exc:
            logger.warning(f"Parallel worker {index}: driver creation failed: {exc}")
            with lock:
                creation_errors.append(ParallelOutcome(index=index, ok=False, error=f"driver creation: {exc}"))

    with ThreadPoolExecutor(max_workers=parallel_workers, thread_name_prefix="chrome") as pool:
        list(pool.map(_create, range(parallel_workers)))

    outcomes.extend(creation_errors)
    if not drivers:
        logger.warning("run_parallel: no browsers started")
        return sorted(outcomes, key=lambda o: o.index)

    barrier = threading.Barrier(len(drivers))
    start_marks: dict[int, float] = {}

    def _work(index: int, driver: webdriver.Chrome) -> None:
        try:
            barrier.wait(timeout=60.0)  # all workers released at the same instant
            with lock:
                start_marks[index] = time.perf_counter()
            start = time.perf_counter()
            try:
                value = operation(driver, index)
            finally:
                spent = (time.perf_counter() - start) * 1000
            with lock:
                outcomes.append(ParallelOutcome(index=index, ok=True, value=value, elapsed_ms=spent))
        except Exception as exc:
            logger.warning(f"Parallel worker {index} failed: {exc}")
            with lock:
                outcomes.append(ParallelOutcome(index=index, ok=False, error=str(exc)))
        finally:
            quit_driver(driver)

    with ThreadPoolExecutor(max_workers=len(drivers), thread_name_prefix="op") as pool:
        pool.map(lambda pair: _work(*pair), drivers)

    if len(start_marks) > 1:
        skew_ms = (max(start_marks.values()) - min(start_marks.values())) * 1000
        logger.info(f"run_parallel: {len(drivers)} browsers, start skew {skew_ms:.2f}ms (target < {max_start_skew_ms}ms)")
        if skew_ms > max_start_skew_ms:
            logger.warning(f"Start skew {skew_ms:.2f}ms exceeded target {max_start_skew_ms}ms")
    else:
        logger.info(f"run_parallel: {len(drivers)} browser(s) finished")

    return sorted(outcomes, key=lambda o: o.index)


def load_user_id(env_path: str | Path = ".env") -> str:
    """Read USER_ID from a .env file (fallback when the env var is not set)."""
    path = Path(env_path)
    if not path.exists():
        raise FileNotFoundError(f"No {path} file — copy .env.example to .env and set USER_ID")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip().startswith("USER_ID="):
                value = line.strip().split("=", 1)[1].strip().strip("\"'")
                if value and value != "paste-your-user-id-here":
                    return value
    raise ValueError(f"USER_ID missing or placeholder in {path}")


class UI:
    """QA facade: tiny task methods, chainable, camelCase on purpose for readability.

    Example:
        ui = UI()
        ui.initBrowser().openApp()
        ui.clickOnButton("Place Bet")
        ui.closeBrowser()

    Or auto-closing:
        with UI() as ui:
            ui.openApp()
            ui.clickOnButton("Odds: All")
    """

    def __init__(
        self,
        user_id: str | None = None,
        base_url: str = "https://qae-assignment-tau.vercel.app",
        headless: bool = True,
    ) -> None:
        self.user_id = user_id or os.getenv("USER_ID") or load_user_id()
        self.base_url = base_url
        self.headless = headless
        self.driver: webdriver.Chrome | None = None

    def _need_driver(self) -> webdriver.Chrome:
        if self.driver is None:
            raise RuntimeError("Call initBrowser() first")
        return self.driver

    def initBrowser(self, headless: bool | None = None) -> UI:
        """Start Chrome (headless by default)."""
        if headless is not None:
            self.headless = headless
        self.driver = make_driver(headless=self.headless)
        return self

    def openApp(self) -> UI:
        """Open the app authed as the stored user."""
        open_app(self._need_driver(), self.user_id, self.base_url)
        wait_for_content(self._need_driver())
        return self

    def clickOnButton(self, text: str, timeout: float = DEFAULT_TIMEOUT, strict: bool = False) -> UI:
        """Click the first visible button matching text (case-insensitive).

        Matches button text, then aria-label. Warns if several match - unless
        strict=True, which raises instead (use for scored runs).
        Raises LookupError listing visible buttons when nothing matches.
        """
        driver = self._need_driver()
        needle = text.strip().lower()
        quoted = f'"{needle}"' if "'" in needle else f"'{needle}'"
        lower = "translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
        aria = "translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
        xpath = (
            f"//button[contains({lower}, {quoted}) or contains({aria}, {quoted})]"
        )
        matches = [b for b in driver.find_elements(By.XPATH, xpath) if b.is_displayed()]
        if not matches:
            available = [ (b.text or "").strip()[:40] for b in find_all(driver, By.TAG_NAME, "button") ][:20]
            raise LookupError(f'No button matching "{text}". Visible buttons include: {available}')
        if len(matches) > 1:
            if strict:
                raise AssertionError(f'clickOnButton("{text}"): {len(matches)} matches in strict mode - refusing to guess')
            logger.warning(f'clickOnButton("{text}"): {len(matches)} matches, clicking the first')
        matches[0].click()
        logger.info(f'Clicked button "{(matches[0].text or "").strip()[:40]}"')
        return self

    def selectOdds(self, match_index: int, outcome: str) -> UI:
        """Select an outcome (fills the bet slip only - never places anything)."""
        select_outcome(self._need_driver(), match_index, outcome)
        return self

    def setStake(self, amount: str) -> UI:
        """Type a stake (never submits anything)."""
        set_stake(self._need_driver(), amount)
        return self

    def readBalance(self) -> str:
        """Header balance text, e.g. 'Balance: EUR 124.50'."""
        driver = self._need_driver()
        for element in find_all(driver, By.XPATH, "//*[contains(text(), 'Balance')]"):
            text = (element.text or "").strip()
            if text:
                return text
        raise LookupError("No balance element found")

    def pageText(self) -> str:
        """Full visible page text (for asserts)."""
        return self._need_driver().find_element(By.TAG_NAME, "body").text

    def takeScreenshot(self, name: str) -> Path:
        """Save defectsVault/screenshots/<name>.png."""
        return screenshot(self._need_driver(), f"defectsVault/screenshots/{name}.png")

    def closeBrowser(self) -> None:
        """Close Chrome (safe to call twice)."""
        if self.driver is not None:
            quit_driver(self.driver)
            self.driver = None

    def __enter__(self) -> UI:
        return self.initBrowser()

    def __exit__(self, *exc_info: Any) -> None:
        self.closeBrowser()


def set_throttle(driver: webdriver.Chrome, kbps: int | None = None) -> None:
    """Throttle the network via CDP. kbps=None restores full speed.

    Use a low value (e.g. 100) to widen first-paint windows for loading-state checks.
    """
    driver.execute_cdp_cmd("Network.enable", {})
    if kbps is None:
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
        logger.info("Network throttle cleared")
        return
    speed = kbps * 1024 / 8.0
    driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
        "offline": False, "latency": 200, "downloadThroughput": speed, "uploadThroughput": speed})
    logger.info(f"Network throttled to ~{kbps} kbps")


def poll_until(driver: webdriver.Chrome, condition: Callable[[], bool], timeout: float = 15.0,
               interval: float = 0.25) -> bool:
    """Poll `condition()` until True or timeout. Returns whether it became True."""
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def set_offline(driver: webdriver.Chrome, offline: bool = True) -> None:
    """Simulate network on/off via Chrome DevTools Protocol (CDP).

    CDP emulation is disabled again by calling set_offline(driver, False).
    Requires a local Chrome (chromedriver) - not remote-grid compatible.
    """
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
        "offline": offline, "latency": 0,
        "downloadThroughput": 0 if offline else -1,
        "uploadThroughput": 0 if offline else -1,
    })
    logger.info(f"Network emulation: offline={offline}")


def page_resources(driver: webdriver.Chrome) -> list[str]:
    """URLs of every resource the page loaded (for HTTPS/mixed-content checks)."""
    return list(driver.execute_script(
        "return performance.getEntriesByType('resource').map(r => r.name)"))


__all__ = [
    "DEFAULT_TIMEOUT",
    "DEFAULT_WINDOW",
    "SUPPORTED_OUTCOMES",
    "app_url",
    "make_driver",
    "quit_driver",
    "open_app",
    "wait_visible",
    "wait_clickable",
    "find_all",
    "wait_for_content",
    "page_inventory",
    "console_errors",
    "screenshot",
    "set_offline",
    "set_throttle",
    "poll_until",
    "page_resources",
    "odds_buttons",
    "select_outcome",
    "set_stake",
    "place_bet",
    "ParallelOutcome",
    "run_parallel",
    "load_user_id",
    "UI",
]
