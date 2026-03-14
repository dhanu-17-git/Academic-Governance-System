import os
import re
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.services import auth_service
from tests.postgres_test_utils import postgres_client_app


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise AssertionError("CSRF token not found in form response.")
    return match.group(1)


def _login(client, app, email: str, expected_redirect: str) -> None:
    login_page = client.get("/login")
    assert login_page.status_code == 200, f"GET /login failed: {login_page.status_code}"
    login_csrf = _extract_csrf_token(login_page.get_data(as_text=True))

    login_post = client.post(
        "/login",
        data={"email": email, "csrf_token": login_csrf},
        follow_redirects=False,
    )
    assert login_post.status_code == 302, f"POST /login failed: {login_post.status_code}"
    assert login_post.headers["Location"].endswith("/verify-otp"), login_post.headers["Location"]

    with app.app_context():
        otp_record = auth_service.get_otp_record(email)
        assert otp_record is not None, f"OTP record not created for {email}"
        otp = otp_record["otp"]

    verify_page = client.get("/verify-otp")
    assert verify_page.status_code == 200, f"GET /verify-otp failed: {verify_page.status_code}"
    verify_csrf = _extract_csrf_token(verify_page.get_data(as_text=True))

    verify_post = client.post(
        "/verify-otp",
        data={"otp": otp, "csrf_token": verify_csrf},
        follow_redirects=False,
    )
    assert verify_post.status_code == 302, f"POST /verify-otp failed: {verify_post.status_code}"
    assert verify_post.headers["Location"].endswith(expected_redirect), verify_post.headers["Location"]


def main() -> None:
    with postgres_client_app() as app:
        client = app.test_client()

        login_page = client.get("/login")
        print("GET /login:", login_page.status_code)
        assert login_page.status_code == 200

        _login(client, app, "student@college.edu", "/dashboard")
        dashboard = client.get("/dashboard")
        dashboard_text = dashboard.get_data(as_text=True)
        print("GET /dashboard:", dashboard.status_code)
        assert dashboard.status_code == 200
        assert "Dashboard" in dashboard_text

        logout = client.get("/logout", follow_redirects=False)
        assert logout.status_code == 302, f"GET /logout failed: {logout.status_code}"
        assert logout.headers["Location"].endswith("/login"), logout.headers["Location"]

        _login(client, app, "admin@college.edu", "/admin")
        admin_dashboard = client.get("/admin")
        admin_text = admin_dashboard.get_data(as_text=True)
        print("GET /admin:", admin_dashboard.status_code)
        assert admin_dashboard.status_code == 200
        assert "Live Dashboard" in admin_text or "Dashboard" in admin_text

    print("test_quick.py: PASS")


if __name__ == "__main__":
    main()
