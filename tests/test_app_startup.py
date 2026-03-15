"""Tests for application startup and route availability."""

from flask import Flask


class TestAppStartup:
    """Verify the app creates correctly and core routes are wired."""

    def test_app_is_flask_instance(self, app):
        assert isinstance(app, Flask)

    def test_app_has_secret_key(self, app):
        assert app.secret_key is not None
        assert len(app.secret_key) > 0

    def test_core_routes_registered(self, app):
        """All expected route prefixes must be present in the url map."""
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        expected = ["/health", "/login", "/dashboard", "/logout"]
        for route in expected:
            assert any(route in r for r in rules), f"Route {route} not registered"

    def test_health_blueprint_registered(self, app):
        assert "health" in app.blueprints

    def test_auth_blueprint_registered(self, app):
        assert "auth" in app.blueprints

    def test_student_blueprint_registered(self, app):
        assert "student" in app.blueprints

    def test_admin_blueprint_registered(self, app):
        assert "admin" in app.blueprints


class TestSecurityHeaders:
    """Verify security headers are set on responses."""

    def test_csp_header_present(self, client):
        response = client.get("/health")
        assert "Content-Security-Policy" in response.headers

    def test_x_frame_options_deny(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_nosniff(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_referrer_policy(self, client):
        response = client.get("/health")
        assert response.headers.get("Referrer-Policy") == "no-referrer"


class TestErrorHandlers:
    """Verify custom error handlers return correct status codes."""

    def test_404_returns_proper_status(self, client):
        response = client.get("/this-route-definitely-does-not-exist-xyz")
        assert response.status_code == 404
