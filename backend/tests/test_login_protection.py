"""Tests für Login-Schutz."""

from app.core.security.login_protection import (
    check_login_allowed,
    record_login_failure,
    record_login_success,
    reset_login_protection_state,
)


def test_login_lockout_after_max_failures():
    reset_login_protection_state()
    ip = "203.0.113.10"
    email = "user@example.com"

    for _ in range(5):
        record_login_failure(ip, email)

    blocked = check_login_allowed(ip, email)
    assert blocked is not None
    assert "gesperrt" in blocked.lower()


def test_success_clears_lockout():
    reset_login_protection_state()
    ip = "203.0.113.11"
    email = "clear@example.com"

    for _ in range(3):
        record_login_failure(ip, email)

    record_login_success(email)
    assert check_login_allowed(ip, email) is None
