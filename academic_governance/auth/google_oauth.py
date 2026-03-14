"""Google OAuth client wiring."""

from __future__ import annotations

from flask import current_app

try:
    from authlib.integrations.base_client.errors import OAuthError as _OAuthError
    from authlib.integrations.flask_client import OAuth
except ImportError:  # pragma: no cover - keeps app bootable until dependency is installed.
    OAuth = None

    class _OAuthError(Exception):
        """Fallback OAuth error when Authlib is unavailable."""


oauth = OAuth() if OAuth is not None else None
OAuthError = _OAuthError


def is_google_oauth_configured(app=None) -> bool:
    app = app or current_app
    return bool(app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"))


def init_google_oauth(app) -> None:
    if oauth is None:
        return

    oauth.init_app(app)
    if not is_google_oauth_configured(app):
        return

    if oauth.create_client("google") is not None:
        return

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def get_google_client():
    if oauth is None:
        return None
    return oauth.create_client("google")