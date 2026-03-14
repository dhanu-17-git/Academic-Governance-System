"""Tests for the /health endpoint."""

import pytest


class TestHealthEndpoint:
    """Verify /health returns clean JSON and does not leak internal details."""

    def test_health_returns_200_when_db_connected(self, client):
        """Happy path: database is reachable."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_health_response_is_json(self, client):
        """Content-Type must be application/json."""
        response = client.get("/health")
        assert response.content_type.startswith("application/json")

    def test_health_no_detail_key_on_success(self, client):
        """Success response must not include a 'detail' key."""
        response = client.get("/health")
        data = response.get_json()
        assert "detail" not in data

    def test_health_does_not_leak_exceptions(self, app_with_client, monkeypatch):
        """When the DB is down, the response must NOT contain raw exception text."""
        app, c = app_with_client

        def _failing_execute(*args, **kwargs):
            raise RuntimeError("connection refused on port 5432")

        from academic_governance.db import db as _db

        with app.app_context():
            monkeypatch.setattr(_db.session, "execute", _failing_execute)
            response = c.get("/health")

        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "unreachable"
        # Must NOT leak the actual exception string
        assert "detail" not in data
        raw_text = response.get_data(as_text=True)
        assert "connection refused" not in raw_text
        assert "port 5432" not in raw_text
