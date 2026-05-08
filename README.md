# Droppin EG – Selenium Validation Tests

Automated regression tests for validation bugs found during exploratory testing of [droppin-eg.com](https://droppin-eg.com).

## Tests

### Bug 4 – Phone Number Accepts Invalid Input
**`test_bug4_phone_rejects_invalid_number`** (runs twice: once with `033633`, once with `013`)

Fills the entire driver registration form with valid data, then overwrites the phone field with a short/invalid number and submits. Checks whether the form stays on the registration page (validation worked) or redirects away (invalid number was accepted).

- **PASS** → URL did not change, form correctly rejected the number
- **FAIL** → bug confirmed, form submitted successfully with an invalid phone number

---

### Bug 7 – Email Validation Only on Frontend
**`test_bug7_email_validation_not_frontend_only`**

Fills the entire form with valid data including a valid email, then uses JavaScript to bypass browser and framework validation and inject `notanemail` into the email field before submitting. This replicates what a tester would do manually via DevTools.

- **PASS** → URL did not change, backend rejected the invalid email
- **FAIL** → bug confirmed, backend accepted the garbage email and submitted the form

#### How the bypass works
Normally you can't type an invalid email into a `type="email"` field — the browser blocks submission. The test strips the `type`, `pattern`, and `required` attributes via JS, then sets the value using the native DOM setter and fires synthetic events so the framework sees the change. This is identical to running the following in the DevTools console:

```javascript
var el = document.querySelector("input[placeholder='Email *']");
el.removeAttribute('type');
el.removeAttribute('pattern');
el.removeAttribute('required');
var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(el, 'notanemail');
el.dispatchEvent(new Event('input',  { bubbles: true }));
el.dispatchEvent(new Event('change', { bubbles: true }));
el.dispatchEvent(new Event('blur',   { bubbles: true }));
```

---

## Dependencies

- Python 3
- Firefox
- [geckodriver](https://github.com/mozilla/geckodriver/releases) — must be on your PATH
- [selenium](https://pypi.org/project/selenium/) Python package
- [just](https://github.com/casey/just) — optional, for the shortcut commands

Install geckodriver on Arch Linux:
```
sudo pacman -S geckodriver
```

## Running the Tests

### With just (recommended)
```
just           # run all tests, headed
just headless  # run all tests, no browser window
just phone     # Bug 4 only
just email     # Bug 7 only
just fail-fast # stop on first failure
just list      # show tests without running
```

### With pytest directly
```
pytest test_droppin_validation.py -v
pytest test_droppin_validation.py -v -s    # also print debug output
pytest test_droppin_validation.py -v --headless
```

## Result Interpretation

| Result | Meaning |
|--------|---------|
| PASSED | Validation is working correctly — form rejected the invalid input |
| FAILED | Bug confirmed — form submitted successfully with invalid input |
| ERROR  | Test setup failed (field not found, page didn't load, etc.) |
