"""
Selenium regression tests for three validation bugs on https://droppin-eg.com

Bug 4  – Phone field accepts short/invalid numbers
Bug 5  – National ID field accepts non-numeric input
Bug 7  – Email validation is frontend-only (bypassable via JS)

Run:
    pytest test_droppin_validation.py -v
    pytest test_droppin_validation.py -v -k "phone"   # single test
"""

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

WAIT = 15  # seconds for explicit waits


# ── helpers ───────────────────────────────────────────────────────────────────

def wait_for_page(driver, timeout=WAIT):
    """Wait until the page has at least one visible <input>."""
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
    )


def find_input(driver, selectors, timeout=WAIT):
    """
    Try each (By, value) pair in order; return the first visible element found.
    Raises AssertionError with a helpful message if nothing matches.
    """
    wait = WebDriverWait(driver, timeout / len(selectors))
    for by, value in selectors:
        try:
            el = wait.until(EC.visibility_of_element_located((by, value)))
            return el
        except TimeoutException:
            continue
    tried = [v for _, v in selectors]
    raise AssertionError(
        f"Could not find any input matching: {tried}\n"
        f"Page title: {driver.title}\n"
        f"Current URL: {driver.current_url}"
    )


def find_submit(driver):
    selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH,        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'register')]"),
        (By.XPATH,        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sign up')]"),
        (By.XPATH,        "//button[contains(text(),'تسجيل')]"),
        (By.XPATH,        "//input[@type='submit']"),
    ]
    for by, value in selectors:
        try:
            return driver.find_element(by, value)
        except NoSuchElementException:
            continue
    raise AssertionError("Submit button not found on page")


def error_present(driver, timeout=5):
    """Return True if any visible error/alert element appears within timeout."""
    error_selectors = [
        "[class*='error']",
        "[class*='invalid']",
        "[class*='alert']",
        "[role='alert']",
        "[class*='danger']",
        "[class*='warning']",
        "span.help-block",
        ".form-error",
        ".field-error",
    ]
    css = ", ".join(error_selectors)
    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css))
        )
        return True
    except TimeoutException:
        return False


def url_changed_to_success(driver, before_url, timeout=5):
    """Return True if the URL changed (indicating a successful form submission)."""
    try:
        WebDriverWait(driver, timeout).until(EC.url_changes(before_url))
        return True
    except TimeoutException:
        return False


# ── Bug 4: Phone Number Field Accepts Invalid Inputs ──────────────────────────

PHONE_SELECTORS = [
    (By.CSS_SELECTOR, "input[type='tel']"),
    (By.CSS_SELECTOR, "input[placeholder*='phone' i]"),
    (By.CSS_SELECTOR, "input[placeholder*='mobile' i],  input[placeholder*='هاتف' i]"),
    (By.CSS_SELECTOR, "input[name*='phone' i], input[id*='phone' i]"),
    (By.CSS_SELECTOR, "input[placeholder*='رقم' i]"),
]


@pytest.mark.parametrize("bad_number", ["033633", "013"])
def test_bug4_phone_rejects_invalid_number(driver, register_url, bad_number):
    """
    Bug 4 – Phone field must reject short/invalid numbers.
    Test FAILS  → bug is present  (invalid number accepted, no error shown)
    Test PASSES → bug is fixed    (error message appears)
    """
    driver.get(register_url)
    wait_for_page(driver)

    phone_field = find_input(driver, PHONE_SELECTORS)
    phone_field.clear()
    phone_field.send_keys(bad_number)
    phone_field.send_keys(Keys.TAB)   # blur to trigger inline validation

    submit_btn = find_submit(driver)
    before_url = driver.current_url
    submit_btn.click()

    accepted = not error_present(driver) and not url_changed_to_success(driver, before_url)

    assert not accepted, (
        f"BUG 4 CONFIRMED: Phone field accepted invalid number '{bad_number}' "
        f"without showing a validation error."
    )



