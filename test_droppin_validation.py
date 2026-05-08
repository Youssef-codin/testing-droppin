"""
Selenium regression tests for validation bugs on https://droppin-eg.com/register/driver

Bug 4 – Phone field accepts short/invalid numbers
Bug 7 – Email validation is frontend-only (bypassable via JS)

Run:
    pytest test_droppin_validation.py -v -s
"""

import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

WAIT = 15


# ── helpers ───────────────────────────────────────────────────────────────────

def wait_for_page(driver, timeout=WAIT):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
    )


def fill(driver, placeholder, value):
    field = driver.find_element(By.CSS_SELECTOR, f"input[placeholder='{placeholder}']")
    field.clear()
    field.send_keys(value)
    return field


def find_submit(driver):
    for by, value in [
        (By.XPATH, "//button[contains(text(),'Register as Driver')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//input[@type='submit']"),
    ]:
        try:
            return driver.find_element(by, value)
        except NoSuchElementException:
            continue
    raise AssertionError("Submit button not found")


def fill_valid_form(driver):
    """Fill every required field with valid data."""
    fill(driver, "First Name *",         "Test")
    fill(driver, "Last Name *",          "User")
    fill(driver, "Email *",              "testdriver@example.com")
    fill(driver, "Phone Number *",       "01012345678")
    fill(driver, "Address *",            "123 Test Street")
    fill(driver, "City *",               "Cairo")
    fill(driver, "State *",              "Cairo")
    fill(driver, "ZIP Code *",           "11511")
    fill(driver, "License Number *",     "ABC12345")
    fill(driver, "Plate Number *",       "ABC 123")
    fill(driver, "Create a password",    "TestPass123!")
    fill(driver, "Confirm your password","TestPass123!")

    # Vehicle Type dropdown — pick the first real option
    dropdown = Select(driver.find_element(By.CSS_SELECTOR, "select"))
    if len(dropdown.options) > 1:
        dropdown.select_by_index(1)


def url_changed(driver, before_url, timeout=6):
    try:
        WebDriverWait(driver, timeout).until(EC.url_changes(before_url))
        return True
    except TimeoutException:
        return False


# ── Bug 4: Phone Number Field Accepts Invalid Inputs ──────────────────────────

@pytest.mark.parametrize("bad_number", ["033633", "013"])
def test_bug4_phone_rejects_invalid_number(driver, register_url, bad_number):
    """
    Fills the whole form with valid data, then replaces phone with a bad number.
    FAILS → bug present  (form submitted despite invalid phone)
    PASSES → bug fixed   (form stayed on page, validation rejected it)
    """
    driver.get(register_url)
    wait_for_page(driver)

    fill_valid_form(driver)
    fill(driver, "Phone Number *", bad_number)  # overwrite with bad value

    before_url = driver.current_url
    find_submit(driver).click()

    redirected = url_changed(driver, before_url)
    print(f"\n  [bug4] phone='{bad_number}' | url changed={redirected} | now at: {driver.current_url}")

    assert not redirected, (
        f"BUG 4 CONFIRMED: Form submitted successfully with invalid phone '{bad_number}'."
    )


# ── Bug 7: Email Validation Only on Frontend ──────────────────────────────────

INVALID_EMAIL = "notanemail"


def test_bug7_email_validation_not_frontend_only(driver, register_url):
    """
    Fills the whole form with valid data, then injects an invalid email via JS
    to bypass frontend validation before submitting.
    FAILS → bug present  (form submitted despite invalid email)
    PASSES → bug fixed   (backend rejected the invalid email)
    """
    driver.get(register_url)
    wait_for_page(driver)

    fill_valid_form(driver)

    # Bypass browser + framework validation on the email field
    email_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Email *']")
    driver.execute_script("""
        var el = arguments[0], val = arguments[1];
        el.removeAttribute('type');
        el.removeAttribute('pattern');
        el.removeAttribute('required');
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, val);
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur',   { bubbles: true }));
    """, email_field, INVALID_EMAIL)

    before_url = driver.current_url
    find_submit(driver).click()

    redirected = url_changed(driver, before_url)
    print(f"\n  [bug7] email='{INVALID_EMAIL}' | url changed={redirected} | now at: {driver.current_url}")

    assert not redirected, (
        f"BUG 7 CONFIRMED: Backend accepted '{INVALID_EMAIL}' after frontend bypass and submitted successfully."
    )
