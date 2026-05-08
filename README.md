# Droppin EG – Selenium Validation Tests

Automated regression tests for validation bugs found during exploratory testing of [droppin-eg.com](https://droppin-eg.com).

## Tests

### Bug 4 – Phone Number Accepts Invalid Input
**`test_bug4_phone_rejects_invalid_number`** (runs twice: once with `033633`, once with `013`)

Navigates to the driver registration page, enters a short/invalid phone number, submits the form, and asserts that a validation error appears.

- **PASS** → form correctly rejects the number
- **FAIL** → bug confirmed, invalid number was accepted

## Dependencies

- Python 3
- Firefox
- [geckodriver](https://github.com/mozilla/geckodriver/releases) — must be on your PATH
- [selenium](https://pypi.org/project/selenium/) Python package
- [just](https://github.com/casey/just) — optional, for the shortcut commands

Install geckodriver 

## Running the Tests

### With just (recommended)
```
just          # run both tests, headed
just headless # run both tests, no browser window
just phone    # run phone tests only
just fail-fast # stop on first failure
just list     # show tests without running
```

### With pytest directly
```
pytest test_droppin_validation.py -v
pytest test_droppin_validation.py -v --headless
```

## Result Interpretation

| Result | Meaning |
|--------|---------|
| PASSED | Validation is working correctly for that input |
| FAILED | Bug confirmed — the invalid input was accepted |
| ERROR  | Test setup failed (field not found, page didn't load, etc.) |
