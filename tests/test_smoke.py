"""Smoke tests — converted from the script-style test_quick.py into proper pytest.

Covers student login → dashboard → logout and admin login → admin dashboard.
"""

import os
import re
import sys

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.services import auth_service


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None, "CSRF token not found in form response."
    return match.group(1)


def _login(client, app, email: str, expected_redirect: str) -> None:
    """Perform otp-based login flow and assert redirect."""
    login_page = client.get("/login")
    assert login_page.status_code == 200
    login_csrf = _extract_csrf_token(login_page.get_data(as_text=True))

    login_post = client.post(
        "/login",
        data={"email": email, "csrf_token": login_csrf},
        follow_redirects=False,
    )
    assert login_post.status_code == 302
    assert login_post.headers["Location"].endswith("/verify-otp")

    with app.app_context():
        otp_record = auth_service.get_otp_record(email)
        assert otp_record is not None
        otp = otp_record["otp"]

    verify_page = client.get("/verify-otp")
    assert verify_page.status_code == 200
    verify_csrf = _extract_csrf_token(verify_page.get_data(as_text=True))

    verify_post = client.post(
        "/verify-otp",
        data={"otp": otp, "csrf_token": verify_csrf},
        follow_redirects=False,
    )
    assert verify_post.status_code == 302
    assert verify_post.headers["Location"].endswith(expected_redirect)


class TestStudentSmoke:
    def test_student_login_dashboard_logout(self, app_with_client):
        app, client = app_with_client

        _login(client, app, "student@college.edu", "/dashboard")

        dashboard = client.get("/dashboard")
        assert dashboard.status_code == 200
        assert "Dashboard" in dashboard.get_data(as_text=True)

        logout = client.get("/logout", follow_redirects=False)
        assert logout.status_code == 302
        assert logout.headers["Location"].endswith("/login")


class TestAdminSmoke:
    def test_admin_login_dashboard(self, app_with_client):
        app, client = app_with_client

        _login(client, app, "admin@college.edu", "/admin")

        admin_dashboard = client.get("/admin")
        assert admin_dashboard.status_code == 200
        admin_text = admin_dashboard.get_data(as_text=True)
        assert "Dashboard" in admin_text
