# Droppin EG – Automated Regression Tests

Automated regression tests covering validation bugs on [droppin-eg.com](https://droppin-eg.com) and API bugs on [aiesec-pace.duckdns.org](https://aiesec-pace.duckdns.org).

---

## API Tests — aiesec-pace.duckdns.org (`test_pickups_api.py`)

Pure HTTP tests using `requests`. No browser required. Credentials are baked in — just run:

```
pytest test_pickups_api.py -v -s
```

Override resource IDs if the defaults (pickup=3, driver=1, package=3) don't exist in the current DB:

```
pytest test_pickups_api.py -v -s --pickup-id 5 --driver-id 2 --package-id 7
```

### BUG-05 – No Duplicate Prevention on Pickup Scheduling
**`test_bug05_duplicate_pickup_returns_conflict`**

Posts the same pickup payload twice in succession. The second request should be rejected because the package is already linked to an active pickup.

- **PASS** → second request returned `409 Conflict` — idempotency guard is in place
- **FAIL** → bug confirmed, second request returned `201` and a duplicate pickup was created

> **Note:** If the test fails (bug is present), a duplicate pickup will exist in the DB after the run. Clean it up via the admin UI.

### BUG-06 – Server Accepts Past Scheduling Dates
**`test_bug06_past_date_rejected`** (runs twice: `2024-01-01` and `2020-06-15`)

Posts a pickup with a `scheduledTime` in the past, bypassing any frontend date-picker restrictions.

- **PASS** → server returned `400 Bad Request` — date validation exists on the backend
- **FAIL** → bug confirmed, server accepted the past date and returned `201`

### BUG-07 – Lack of Idempotency on Driver Assignment
**`test_bug07_driver_assignment_is_idempotent`**

Sends the same driver assignment PATCH twice. The second call should be a no-op, returning `304` or a `200` body indicating the driver is already assigned.

- **PASS** → second PATCH returned `304`, or `200` with an "already assigned" message
- **FAIL** → bug confirmed, second PATCH silently wrote to the DB with no no-op signal

---

## Selenium Tests — droppin-eg.com (`test_droppin_validation.py`)

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

### API tests
- Python 3
- [requests](https://pypi.org/project/requests/) Python package

### Selenium tests
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

### API tests
```
pytest test_pickups_api.py -v -s
```

### Selenium tests — with just (recommended)
```
just           # run all tests, headed
just headless  # run all tests, no browser window
just phone     # Bug 4 only
just email     # Bug 7 only
just fail-fast # stop on first failure
just list      # show tests without running
```

### Selenium tests — with pytest directly
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
