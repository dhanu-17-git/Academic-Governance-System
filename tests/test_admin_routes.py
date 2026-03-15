import os
import sys

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import config
from tests.helpers import login_as


ADMIN_PATHS = [
    "/admin",
    "/admin/academic/attendance",
    "/admin/academic/marks",
    "/admin/academic/materials",
    "/admin/academic/timetable",
    "/admin/labs",
    "/admin/notifications",
    "/admin/students/create",
    "/admin/at-risk",
]


class TestAdminRoutes:
    @pytest.mark.parametrize("path", ADMIN_PATHS)
    def test_admin_pages_render_for_admin_users(self, client, path):
        login_as(client, "admin@college.edu", config.ROLE_ADMIN)
        response = client.get(path)
        assert response.status_code == 200

    def test_admin_routes_redirect_anonymous_users_to_login(self, client):
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    @pytest.mark.parametrize("path", ["/admin", "/admin/notifications"])
    def test_admin_routes_forbid_student_users(self, client, path):
        login_as(client, "student@college.edu", config.ROLE_STUDENT)
        response = client.get(path)
        assert response.status_code == 403
