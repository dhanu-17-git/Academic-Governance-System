import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import config
from academic_governance.services import notification_service
from tests.helpers import extract_csrf_token, login_as


class TestNotificationRoutes:
    def test_student_notifications_page_shows_existing_notifications(
        self, app_with_client
    ):
        app, client = app_with_client

        with app.app_context():
            notification_service.create_notification(
                "Campus Alert",
                "Library will close early today.",
                "https://example.com/library",
            )

        login_as(client, "student@college.edu", config.ROLE_STUDENT)
        response = client.get("/notifications")

        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Campus Alert" in body
        assert "Library will close early today." in body

    def test_admin_notifications_page_forbids_non_admins(self, client):
        login_as(client, "student@college.edu", config.ROLE_STUDENT)
        response = client.get("/admin/notifications")
        assert response.status_code == 403

    def test_admin_can_create_notification(self, app_with_client):
        app, client = app_with_client
        login_as(client, "admin@college.edu", config.ROLE_ADMIN)

        page = client.get("/admin/notifications")
        assert page.status_code == 200
        csrf_token = extract_csrf_token(page.get_data(as_text=True))

        response = client.post(
            "/admin/notifications",
            data={
                "title": "Exam Hall Update",
                "message": "Exam hall allocation is live.",
                "link": "https://example.com/exams",
                "csrf_token": csrf_token,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        with app.app_context():
            notifications = notification_service.get_notifications(limit=5)
            assert any(
                item["title"] == "Exam Hall Update"
                and item["link"] == "https://example.com/exams"
                for item in notifications
            )
