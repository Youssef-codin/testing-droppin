import os
import pytest
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

REGISTER_URL = "https://droppin-eg.com/register/driver"
WAIT = 15


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", default=False,
                     help="Run Firefox in headless mode")
    parser.addoption("--pickup-id", default="3", type=int,
                     help="Existing pickup ID to use in driver-assignment tests (default: 3)")
    parser.addoption("--driver-id", default="1", type=int,
                     help="Driver ID to assign in driver-assignment tests (default: 1)")
    parser.addoption("--package-id", default="3", type=int,
                     help="Package ID to use when scheduling test pickups (default: 3)")


# ── shared helpers ────────────────────────────────────────────────────────────

def wait_for_page(driver, timeout=WAIT):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input"))
    )


def url_changed(driver, before_url, timeout=6):
    try:
        WebDriverWait(driver, timeout).until(EC.url_changes(before_url))
        return True
    except TimeoutException:
        return False


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def register_url():
    return REGISTER_URL


@pytest.fixture(scope="session")
def pickup_id(request):
    return request.config.getoption("--pickup-id")


@pytest.fixture(scope="session")
def driver_id(request):
    return request.config.getoption("--driver-id")


@pytest.fixture(scope="session")
def package_id(request):
    return request.config.getoption("--package-id")


@pytest.fixture(scope="function")
def driver(request):
    opts = Options()
    if request.config.getoption("--headless"):
        opts.add_argument("--headless")
    browser = webdriver.Firefox(options=opts)
    browser.implicitly_wait(3)

    yield browser

    os.makedirs("images", exist_ok=True)
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join("images", f"{test_name}_{timestamp}.png")
    try:
        browser.save_screenshot(screenshot_path)
        print(f"\n[Screenshot] Saved result to: {screenshot_path}")
    except Exception as e:
        print(f"\n[Screenshot] Failed to save screenshot: {e}")

    browser.quit()
