import pytest
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

REGISTER_URL = "https://droppin-eg.com/register/driver"


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", default=False,
                     help="Run Firefox in headless mode")


@pytest.fixture(scope="function")
def register_url():
    return REGISTER_URL


@pytest.fixture(scope="function")
def driver(request):
    opts = Options()
    if request.config.getoption("--headless"):
        opts.add_argument("--headless")
    browser = webdriver.Firefox(options=opts)
    browser.implicitly_wait(3)
    yield browser
    browser.quit()
