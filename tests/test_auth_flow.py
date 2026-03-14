import os
import sys

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import academic_governance.routes.auth as auth_routes
from academic_governance import config
from academic_governance.repositories import user_repository
from academic_governance.services import auth_service
from tests.helpers import extract_csrf_token
from tests.postgres_test_utils import postgres_client_app


class FakeGoogleClient:
    def __init__(self, email: str, *, verified: bool = True):
        self._email = email
        self._verified = verified

    def authorize_access_token(self):
        return {
            "userinfo": {
                "email": self._email,
                "email_verified": self._verified,
            }
        }


@pytest.fixture()
def app_and_client():
    with postgres_client_app() as app:
        yield app, app.test_client()


def test_otp_login_flow(app_and_client):
    app, client = app_and_client

    login_page = client.get("/login")
    assert login_page.status_code == 200
    login_csrf = extract_csrf_token(login_page.get_data(as_text=True))

    login_post = client.post(
        "/login",
        data={"email": "student@college.edu", "csrf_token": login_csrf},
        follow_redirects=False,
    )
    assert login_post.status_code == 302
    assert login_post.headers["Location"].endswith("/verify-otp")

    with app.app_context():
        otp_record = auth_service.get_otp_record("student@college.edu")
        assert otp_record is not None
        otp = otp_record["otp"]

    verify_page = client.get("/verify-otp")
    assert verify_page.status_code == 200
    verify_csrf = extract_csrf_token(verify_page.get_data(as_text=True))

    verify_post = client.post(
        "/verify-otp",
        data={"otp": otp, "csrf_token": verify_csrf},
        follow_redirects=False,
    )
    assert verify_post.status_code == 302
    assert verify_post.headers["Location"].endswith("/dashboard")

    with client.session_transaction() as session_data:
        assert session_data["user_email"] == "student@college.edu"
        assert session_data["role"] == config.ROLE_STUDENT


def test_login_sends_otp_email_when_configured(monkeypatch, app_and_client):
    app, client = app_and_client
    delivered = {}

    monkeypatch.setattr(auth_routes.email_service, "is_email_configured", lambda: True)

    def fake_send_otp_email(recipient, otp, *, expires_in_minutes=5):
        delivered["recipient"] = recipient
        delivered["otp"] = otp
        delivered["expires_in_minutes"] = expires_in_minutes

    monkeypatch.setattr(auth_routes.email_service, "send_otp_email", fake_send_otp_email)

    login_page = client.get("/login")
    login_csrf = extract_csrf_token(login_page.get_data(as_text=True))

    response = client.post(
        "/login",
        data={"email": "student@college.edu", "csrf_token": login_csrf},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/verify-otp")
    assert delivered["recipient"] == "student@college.edu"
    assert delivered["expires_in_minutes"] == 5

    with app.app_context():
        otp_record = auth_service.get_otp_record("student@college.edu")
        assert otp_record is not None
        assert delivered["otp"] == otp_record["otp"]


def test_login_clears_otp_when_email_delivery_fails(monkeypatch, app_and_client):
    app, client = app_and_client

    monkeypatch.setattr(auth_routes.email_service, "is_email_configured", lambda: True)

    def failing_send_otp_email(*args, **kwargs):
        raise auth_routes.email_service.EmailDeliveryError("smtp unavailable")

    monkeypatch.setattr(auth_routes.email_service, "send_otp_email", failing_send_otp_email)

    login_page = client.get("/login")
    login_csrf = extract_csrf_token(login_page.get_data(as_text=True))

    response = client.post(
        "/login",
        data={"email": "student@college.edu", "csrf_token": login_csrf},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert auth_service.get_otp_record("student@college.edu") is None

    with client.session_transaction() as session_data:
        assert "pending_email" not in session_data


def test_login_fails_closed_without_email_delivery_in_non_debug(monkeypatch, app_and_client):
    app, client = app_and_client

    monkeypatch.setattr(auth_routes.config, "DEBUG", False)
    monkeypatch.setattr(auth_routes.email_service, "is_email_configured", lambda: False)

    login_page = client.get("/login")
    login_csrf = extract_csrf_token(login_page.get_data(as_text=True))

    response = client.post(
        "/login",
        data={"email": "student@college.edu", "csrf_token": login_csrf},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert auth_service.get_otp_record("student@college.edu") is None

    with client.session_transaction() as session_data:
        assert "pending_email" not in session_data


def test_google_callback_creates_student_user(monkeypatch, app_and_client):
    app, client = app_and_client
    monkeypatch.setattr(
        auth_routes,
        "get_google_client",
        lambda: FakeGoogleClient("google.student@college.edu"),
    )

    response = client.get("/auth/google/callback", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with app.app_context():
        user = user_repository.get_user_by_email("google.student@college.edu")
        assert user is not None
        assert user.role == config.ROLE_STUDENT

    with client.session_transaction() as session_data:
        assert session_data["user_email"] == "google.student@college.edu"
        assert session_data["role"] == config.ROLE_STUDENT


def test_google_callback_rejects_unverified_email(monkeypatch, app_and_client):
    _, client = app_and_client
    monkeypatch.setattr(
        auth_routes,
        "get_google_client",
        lambda: FakeGoogleClient("google.student@college.edu", verified=False),
    )

    response = client.get("/auth/google/callback", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with client.session_transaction() as session_data:
        assert "user_email" not in session_data


def test_google_callback_uses_existing_user_role(monkeypatch, app_and_client):
    app, client = app_and_client

    with app.app_context():
        user_repository.create_user("google.admin@college.edu", config.ROLE_ADMIN)

    monkeypatch.setattr(
        auth_routes,
        "get_google_client",
        lambda: FakeGoogleClient("google.admin@college.edu"),
    )

    response = client.get("/auth/google/callback", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")

    with client.session_transaction() as session_data:
        assert session_data["user_email"] == "google.admin@college.edu"
        assert session_data["role"] == config.ROLE_ADMIN