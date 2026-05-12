import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

WAIT = 20

# --- helpers (matching test_droppin_validation.py style) ---

def wait_for_page(driver, timeout=WAIT):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
    )

def fill(driver, placeholder, value):
    # Try different ways to find fields
    try:
        # Case-insensitive placeholder match if possible, but standard CSS is case-sensitive
        # We'll try exact match first, then some variations
        field = driver.find_element(By.CSS_SELECTOR, f"input[placeholder='{placeholder}']")
    except NoSuchElementException:
        try:
            # Try lowercase variation for some fields
            field = driver.find_element(By.CSS_SELECTOR, f"input[placeholder='{placeholder.lower()}']")
        except NoSuchElementException:
            # Try contains (case-sensitive)
            field = driver.find_element(By.CSS_SELECTOR, f"input[placeholder*='{placeholder}']")
            
    field.clear()
    field.send_keys(value)
    return field

def find_submit(driver, text=None):
    if text:
        selectors = [
            (By.XPATH, f"//button[contains(text(),'{text}')]"),
            (By.XPATH, f"//input[@value='{text}']"),
        ]
    else:
        selectors = []
    
    selectors += [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(@class, 'submit')]"),
        (By.XPATH, "//button[contains(text(),'Register')]"),
        (By.XPATH, "//button[contains(text(),'Login')]"),
        (By.XPATH, "//button[contains(text(),'Track')]"),
    ]
    
    for by, val in selectors:
        try:
            return driver.find_element(by, val)
        except NoSuchElementException:
            continue
    raise NoSuchElementException("Submit button not found")

def url_changed(driver, before_url, timeout=6):
    try:
        WebDriverWait(driver, timeout).until(EC.url_changes(before_url))
        return True
    except TimeoutException:
        return False

# --- Test Cases ---

def test_password_mismatch_registration(driver):
    """
    Test that registration fails when password and confirm password do not match.
    """
    url = "https://droppin-eg.com/register/driver"
    driver.get(url)
    wait_for_page(driver)

    fill(driver, "First Name *", "Test")
    fill(driver, "Last Name *", "User")
    fill(driver, "Email *", "testmismatch@example.com")
    fill(driver, "Phone Number *", "01012345678")
    
    fill(driver, "Create a password", "Password123!")
    fill(driver, "Confirm your password", "Different456!")

    before_url = driver.current_url
    find_submit(driver).click()

    # It should NOT redirect if validation works
    redirected = url_changed(driver, before_url, timeout=4)
    assert not redirected, "Form submitted despite password mismatch!"

def test_login_invalid_credentials(driver):
    """
    Test that login fails with incorrect credentials.
    """
    url = "https://droppin-eg.com/login"
    driver.get(url)
    wait_for_page(driver)

    fill(driver, "Enter your email", "nonexistent@example.com")
    fill(driver, "Enter your password", "wrongpassword")

    before_url = driver.current_url
    find_submit(driver, "Login").click()

    redirected = url_changed(driver, before_url, timeout=4)
    if redirected:
        assert "login" in driver.current_url.lower(), f"Redirected to unexpected page: {driver.current_url}"

def test_track_package_empty_input(driver):
    """
    Test that the tracking page handles empty or invalid tracking numbers gracefully.
    """
    url = "https://droppin-eg.com/track"
    driver.get(url)
    # The tracking page might have a different structure, let's wait for any input
    wait_for_page(driver)

    before_url = driver.current_url
    try:
        find_submit(driver, "Track").click()
    except NoSuchElementException:
        # If no button, maybe it's an icon or just enter. We'll try finding any button.
        driver.find_element(By.TAG_NAME, "button").click()

    redirected = url_changed(driver, before_url, timeout=3)
    if not redirected:
        assert "track" in driver.current_url.lower()

def test_shop_registration_required_fields(driver):
    """
    Test that shop registration fails if required fields are missing.
    """
    url = "https://droppin-eg.com/register/shop"
    driver.get(url)
    wait_for_page(driver)

    fill(driver, "Enter your business name", "Test Shop")

    before_url = driver.current_url
    find_submit(driver, "Register").click()

    redirected = url_changed(driver, before_url, timeout=4)
    assert not redirected, "Shop registration submitted with missing required fields!"

def test_shop_password_mismatch(driver):
    """
    Test that shop registration fails when passwords do not match.
    """
    url = "https://droppin-eg.com/register/shop"
    driver.get(url)
    wait_for_page(driver)

    fill(driver, "Enter your business name", "Test Shop Mismatch")
    fill(driver, "Enter business email", "shopmismatch@example.com")
    fill(driver, "01xxxxxxxxx", "01122334455")
    fill(driver, "Create a password", "Pass123!")
    fill(driver, "Confirm your password", "Wrong456!")

    before_url = driver.current_url
    find_submit(driver, "Register").click()

    redirected = url_changed(driver, before_url, timeout=4)
    assert not redirected, "Shop registration submitted despite password mismatch!"

def test_contact_form_invalid_email(driver):
    """
    Test that the contact form rejects an invalid email address.
    """
    url = "https://droppin-eg.com/contact"
    driver.get(url)
    wait_for_page(driver)

    fill(driver, "Your full name", "Test User")
    fill(driver, "your.email@example.com", "invalid-email")
    fill(driver, "What can we help you with?", "Testing")
    
    try:
        msg = driver.find_element(By.TAG_NAME, "textarea")
        msg.send_keys("This is a test message.")
    except NoSuchElementException:
        pass

    before_url = driver.current_url
    find_submit(driver, "Submit").click()

    redirected = url_changed(driver, before_url, timeout=4)
    assert not redirected, "Contact form submitted with invalid email!"

def test_driver_registration_single_field_only(driver):
    """
    Test that driver registration fails when only the 'First Name' is filled.
    This ensures that the form correctly validates the absence of other required fields.
    """
    url = "https://droppin-eg.com/register/driver"
    driver.get(url)
    wait_for_page(driver)

    # Fill ONLY the First Name field
    fill(driver, "First Name *", "OnlyFirstName")

    before_url = driver.current_url
    find_submit(driver).click()

    # The form should stay on the same page because other required fields are missing
    redirected = url_changed(driver, before_url, timeout=4)
    assert not redirected, "Form submitted successfully with only one field filled!"
