"""Shared pytest fixtures for CI-safe tests."""

import os
import sys

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tests.postgres_test_utils import postgres_client_app, postgres_test_app


@pytest.fixture()
def app():
    """Provide a Flask app with a fresh PostgreSQL schema (inside app context)."""
    with postgres_test_app() as application:
        yield application


@pytest.fixture()
def app_with_client():
    """Provide (app, test_client) with a fresh PostgreSQL schema."""
    with postgres_client_app() as application:
        yield application, application.test_client()


@pytest.fixture()
def client(app_with_client):
    """Shortcut: just the test client."""
    _, c = app_with_client
    return c
