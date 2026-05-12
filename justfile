default: test

# Rul new test cases 
test:
     pytest test_droppin_extended.py -v
# Run all 3 tests (headed browser)
test:
     pytest test_droppin_validation.py -v

# Run all 3 tests headless
headless:
     pytest test_droppin_validation.py -v --headless

# Bug 4 only – phone number validation
phone:
     pytest test_droppin_validation.py -v -k "phone"

# Bug 7 only – email frontend bypass
email:
     pytest test_droppin_validation.py -v -k "email"


# Stop on first failure
fail-fast:
     pytest test_droppin_validation.py -v -x

# Show collected tests without running them
list:
     pytest test_droppin_validation.py --collect-only
