default: test

# Run all tests (headed browser)
test:
     pytest test_droppin_validation.py test_droppin_extended.py test_pickups_api.py -v

# Run all tests headless
headless:
     pytest test_droppin_validation.py test_droppin_extended.py test_pickups_api.py -v --headless

# Run only Selenium validation tests (Bug 4 & 7)
validation:
     pytest test_droppin_validation.py -v

# Run only extended Selenium tests
extended:
     pytest test_droppin_extended.py -v

# Run only API regression tests (Bug 5, 6, 7)
api:
     pytest test_pickups_api.py -v -s

# Bug 4 only – phone number validation
phone:
     pytest test_droppin_validation.py -v -k "phone"

# Bug 7 only – email frontend bypass
email:
     pytest test_droppin_validation.py -v -k "email"

# Stop on first failure
fail-fast:
     pytest test_droppin_validation.py test_droppin_extended.py test_pickups_api.py -v -x

# Show collected tests without running them
list:
     pytest test_droppin_validation.py test_droppin_extended.py test_pickups_api.py --collect-only
