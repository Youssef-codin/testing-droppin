import pytest
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

REGISTER_URL = "https://droppin-eg.com/register/driver"


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", default=False,
                     help="Run Firefox in headless mode")
    parser.addoption("--pickup-id", default="3", type=int,
                     help="Existing pickup ID to use in driver-assignment tests (default: 3)")
    parser.addoption("--driver-id", default="1", type=int,
                     help="Driver ID to assign in driver-assignment tests (default: 1)")
    parser.addoption("--package-id", default="3", type=int,
                     help="Package ID to use when scheduling test pickups (default: 3)")


@pytest.fixture(scope="function")
def register_url():
    return REGISTER_URL


@pytest.fixture(scope="function")
def driver(request):
    import os
    from datetime import datetime
    
    opts = Options()
    if request.config.getoption("--headless"):
        opts.add_argument("--headless")
    browser = webdriver.Firefox(options=opts)
    browser.implicitly_wait(3)
    
    yield browser
    
    # Take screenshot of the result
    if not os.path.exists("images"):
        os.makedirs("images")
    
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_name = f"{test_name}_{timestamp}.png"
    screenshot_path = os.path.join("images", screenshot_name)
    
    try:
        browser.save_screenshot(screenshot_path)
        print(f"\n[Screenshot] Saved result to: {screenshot_path}")
    except Exception as e:
        print(f"\n[Screenshot] Failed to save screenshot: {e}")

    browser.quit()
