default: test

# Run all 3 tests (headed browser)
test:
    python3 -m pytest test_droppin_validation.py -v

# Run all 3 tests headless
headless:
    python3 -m pytest test_droppin_validation.py -v --headless

# Bug 4 only – phone number validation
phone:
    python3 -m pytest test_droppin_validation.py -v -k "phone"

# Bug 7 only – email frontend bypass
email:
    python3 -m pytest test_droppin_validation.py -v -k "email"


# Stop on first failure
fail-fast:
    python3 -m pytest test_droppin_validation.py -v -x

# Show collected tests without running them
list:
    python3 -m pytest test_droppin_validation.py --collect-only
