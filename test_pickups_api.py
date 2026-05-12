"""
API regression tests for https://aiesec-pace.duckdns.org/api/pickups

BUG-05 – No duplicate prevention (Idempotency) on pickup scheduling
BUG-06 – Server accepts past scheduling dates
BUG-07 – Lack of idempotency on driver assignment

Run:
    pytest test_pickups_api.py -v -s

    # Override resource IDs if defaults (pickup=3, driver=1, package=3) don't exist:
    pytest test_pickups_api.py -v -s --pickup-id 5 --driver-id 2 --package-id 7
"""

import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = "https://aiesec-pace.duckdns.org/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
PICKUPS_URL = f"{BASE_URL}/pickups"

_CREDENTIALS = {
    "admin":    {"email": "admin@droppin.com",   "password": "password"},
    "business": {"email": "joe@gmail.com",        "password": "password"},
    "driver":   {"email": "youssef@gmail.com",    "password": "password"},
}


# ── auth helpers ──────────────────────────────────────────────────────────────

def _login(role: str) -> dict:
    creds = _CREDENTIALS[role]
    resp = requests.post(LOGIN_URL, json=creds)
    assert resp.status_code == 200, (
        f"Login failed for role '{role}' ({creds['email']}): "
        f"{resp.status_code} {resp.text[:200]}"
    )
    data = resp.json()
    # token may be nested under 'token', 'accessToken', 'data.token', etc.
    token = (
        data.get("token")
        or data.get("accessToken")
        or data.get("access_token")
        or (data.get("data") or {}).get("token")
    )
    assert token, f"Could not find token in login response: {data}"
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def business_headers():
    return _login("business")


@pytest.fixture(scope="session")
def admin_headers():
    return _login("admin")


# ── resource ID fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def pickup_id(request):
    return request.config.getoption("--pickup-id")


@pytest.fixture(scope="session")
def driver_id(request):
    return request.config.getoption("--driver-id")


@pytest.fixture(scope="session")
def package_id(request):
    return request.config.getoption("--package-id")


# ── BUG-05: No duplicate prevention on pickup scheduling ──────────────────────

def test_bug05_duplicate_pickup_returns_conflict(business_headers, package_id):
    """
    Sends the exact same pickup payload twice. The second request should be
    rejected with 409 Conflict because the package is already in a scheduled pickup.

    FAILS  → bug present  (second request returns 201 — duplicate created)
    PASSES → bug fixed    (second request returns 409)

    NOTE: This test creates a real pickup in the DB. If the bug is present a
    duplicate will exist after the run — clean it up manually via the admin UI.
    """
    future_time = (datetime.now(timezone.utc) + timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    payload = {
        "scheduledTime": future_time,
        "pickupAddress": "Test St, Test City, TC, 00000, Testland",
        "packageIds": [package_id],
    }

    first = requests.post(PICKUPS_URL, json=payload, headers=business_headers)
    print(f"\n  [bug05] 1st POST → {first.status_code}: {first.text[:200]}")

    assert first.status_code == 201, (
        f"First request failed unexpectedly with {first.status_code}. "
        "Check that the package ID exists and is not already scheduled."
    )

    second = requests.post(PICKUPS_URL, json=payload, headers=business_headers)
    print(f"  [bug05] 2nd POST → {second.status_code}: {second.text[:200]}")

    assert second.status_code == 409, (
        f"BUG-05 CONFIRMED: Duplicate pickup created. "
        f"Second identical request returned {second.status_code} instead of 409 Conflict."
    )


# ── BUG-06: Server accepts past scheduling dates ──────────────────────────────

@pytest.mark.parametrize("past_date", [
    "2024-01-01T00:00:00.000Z",
    "2020-06-15T12:00:00.000Z",
])
def test_bug06_past_date_rejected(business_headers, package_id, past_date):
    """
    Submits a pickup with a scheduledTime in the past. The server must reject
    it with 400 Bad Request.

    FAILS  → bug present  (server returns 201 — past date accepted)
    PASSES → bug fixed    (server returns 400)
    """
    payload = {
        "scheduledTime": past_date,
        "pickupAddress": "Test St, Test City, TC, 00000, Testland",
        "packageIds": [package_id],
    }

    resp = requests.post(PICKUPS_URL, json=payload, headers=business_headers)
    print(f"\n  [bug06] scheduledTime={past_date} → {resp.status_code}: {resp.text[:200]}")

    assert resp.status_code == 400, (
        f"BUG-06 CONFIRMED: Server accepted a past scheduledTime ('{past_date}'). "
        f"Got {resp.status_code} instead of 400 Bad Request."
    )


# ── BUG-07: Lack of idempotency on driver assignment ─────────────────────────

def test_bug07_driver_assignment_is_idempotent(admin_headers, pickup_id, driver_id):
    """
    Assigns the same driver to the same pickup twice. The second call should
    detect no change and return 200/304 with an "already assigned" message
    rather than executing a redundant DB write.

    FAILS  → bug present  (second call silently writes to DB with no indication
                           it was a no-op)
    PASSES → bug fixed    (second call returns 304, or a 200 whose body contains
                           language like "already assigned")
    """
    assign_url = f"{BASE_URL}/pickups/admin/pickups/{pickup_id}/assign-driver"
    payload = {"driverId": driver_id}

    first = requests.patch(assign_url, json=payload, headers=admin_headers)
    print(f"\n  [bug07] 1st PATCH → {first.status_code}: {first.text[:200]}")

    assert first.status_code in (200, 201), (
        f"First assignment failed with {first.status_code}. "
        "Check that --pickup-id and --driver-id point to existing records."
    )

    second = requests.patch(assign_url, json=payload, headers=admin_headers)
    print(f"  [bug07] 2nd PATCH → {second.status_code}: {second.text[:200]}")

    already_assigned_hint = any(
        phrase in second.text.lower()
        for phrase in ("already assigned", "no change", "not modified", "already set")
    )
    is_idempotent = second.status_code == 304 or (
        second.status_code == 200 and already_assigned_hint
    )

    assert is_idempotent, (
        f"BUG-07 CONFIRMED: Driver re-assignment is not idempotent. "
        f"Second identical PATCH returned {second.status_code} with no indication "
        f"of a no-op (body: {second.text[:200]!r})."
    )
