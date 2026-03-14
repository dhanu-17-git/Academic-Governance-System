"""WSGI entrypoint for production servers such as Gunicorn."""

from academic_governance import create_app

app = create_app()
