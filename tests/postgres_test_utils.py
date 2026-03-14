"""Helpers for isolated PostgreSQL-backed test scripts."""

from __future__ import annotations

import os
import secrets
import sys
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import create_app
from academic_governance import config
from academic_governance.db import db


def _base_database_uri() -> str:
    uri = config.SQLALCHEMY_DATABASE_URI
    if not uri.startswith("postgresql"):
        raise RuntimeError("PostgreSQL tests require a PostgreSQL SQLALCHEMY_DATABASE_URI.")
    return uri


@contextmanager
def _temporary_postgres_schema():
    base_url = make_url(_base_database_uri())
    schema_name = f"test_{secrets.token_hex(8)}"
    admin_engine = create_engine(base_url)
    original_uri = config.SQLALCHEMY_DATABASE_URI

    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))

        test_url = base_url.update_query_dict({"options": f"-csearch_path={schema_name}"})
        config.SQLALCHEMY_DATABASE_URI = test_url.render_as_string(hide_password=False)
        yield
    finally:
        config.SQLALCHEMY_DATABASE_URI = original_uri
        admin_engine.dispose()

        cleanup_engine = create_engine(base_url)
        try:
            with cleanup_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        finally:
            cleanup_engine.dispose()


@contextmanager
def postgres_test_app():
    with _temporary_postgres_schema():
        app = create_app()
        with app.app_context():
            db.create_all()
            try:
                yield app
            finally:
                db.session.remove()
                db.drop_all()
                db.engine.dispose()


@contextmanager
def postgres_client_app():
    with _temporary_postgres_schema():
        app = create_app()
        with app.app_context():
            db.create_all()

        try:
            yield app
        finally:
            with app.app_context():
                db.session.remove()
                db.drop_all()
                db.engine.dispose()
