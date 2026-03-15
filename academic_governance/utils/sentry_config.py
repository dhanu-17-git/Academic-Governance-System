"""Optional Sentry error-tracking bootstrap for the Academic Governance System.

Call ``init_sentry(app)`` during application startup.  Sentry is initialised
**only** when the ``SENTRY_DSN`` environment variable is set; otherwise the
function is a silent no-op, keeping local development unaffected.

Requirements
------------
Install the SDK before use::

    pip install sentry-sdk[flask]

This dependency is intentionally **not** added to ``requirements.txt`` by this
module.  See the handoff note for the exact line to add.
"""

import logging
import os

logger = logging.getLogger(__name__)


def init_sentry(app) -> None:  # noqa: ANN001 – Flask app
    """Initialise Sentry if ``SENTRY_DSN`` is present in the environment.

    Parameters
    ----------
    app:
        The Flask application instance (used by the Flask integration).
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        logger.debug("SENTRY_DSN not set — Sentry disabled.")
        return

    try:
        import sentry_sdk  # noqa: WPS433 — conditional import by design
        from sentry_sdk.integrations.flask import FlaskIntegration
    except ImportError:
        logger.warning(
            "SENTRY_DSN is set but sentry-sdk is not installed.  "
            "Run: pip install sentry-sdk[flask]"
        )
        return

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_RATE", "0.1")),
        environment=os.environ.get("FLASK_ENV", "development"),
        send_default_pii=False,
    )
    logger.info(
        "Sentry initialised (env=%s).", os.environ.get("FLASK_ENV", "development")
    )
