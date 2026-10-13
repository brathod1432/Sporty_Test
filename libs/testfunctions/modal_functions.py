"""UI modal handling for betting app: dismiss receipts/errors, clear slip with retry logic."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import time

from selenium.webdriver.common.by import By

from testfunctions.ui_helper import find_all

DISMISS_LABELS: tuple[str, ...] = ("Close", "CLOSE", "close", "x", "X")
STALE_RETRIES: int = 3


def _safe_text(element) -> str:
    """Element text, or an empty string when the node has gone stale."""
    try:
        return (element.text or "").strip()
    except Exception:
        return ""


def _safe_click(element) -> bool:
    """Click an element, treating stale references and interception as failure."""
    try:
        element.click()
        return True
    except Exception:
        return False


def _safe_displayed(element) -> bool:
    """Whether an element is displayed, treating stale references as not shown."""
    try:
        return bool(element.is_displayed())
    except Exception:
        return False


def _dialogs(ui) -> list:
    """Every currently visible modal element."""
    out = []
    for el in find_all(ui._need_driver(), By.CSS_SELECTOR, "[role='dialog'], [class*='modal' i]"):
        if _safe_displayed(el):
            out.append(el)
    return out


def is_modal_open(ui) -> bool:
    """Whether any modal is currently displayed.

    Args:
        ui: the UI facade.
    Returns:
        True when a visible modal exists.
    """
    return bool(_dialogs(ui))


def close_receipt(ui) -> bool:
    """Dismiss an open modal (receipt or error) so the page is interactive again.

    Args:
        ui: the UI facade.
    Returns:
        True when a dismissing control was clicked, False when no modal was open.
    """
    for _ in range(STALE_RETRIES):
        for dialog in _dialogs(ui):
            for button in dialog.find_elements(By.TAG_NAME, "button"):
                if _safe_text(button) in DISMISS_LABELS and _safe_click(button):
                    time.sleep(0.8)
                    return True
            for button in dialog.find_elements(By.TAG_NAME, "button"):
                if not _safe_text(button) and _safe_click(button):
                    time.sleep(0.8)
                    return True
        time.sleep(0.3)
    return False


def clear_slip(ui) -> bool:
    """Clear any active selection using Remove All; tolerates modals and re-renders.

    Args:
        ui: the UI facade.
    Returns:
        True when a selection was cleared, False when the slip was already empty.
    """
    for _ in range(STALE_RETRIES):
        target = None
        for button in find_all(ui._need_driver(), By.TAG_NAME, "button"):
            if _safe_text(button) == "Remove All" and _safe_displayed(button):
                target = button
                break
        if target is None:
            return False
        if _safe_click(target):
            time.sleep(0.8)
            return True
        # Click was intercepted (a modal) or the node went stale: dismiss and retry.
        close_receipt(ui)
    return False


__all__ = ["DISMISS_LABELS", "clear_slip", "close_receipt", "is_modal_open"]