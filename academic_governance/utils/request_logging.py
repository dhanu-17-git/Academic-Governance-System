"""Request-level logging middleware for the Academic Governance System.

Register the middleware by calling ``init_request_logging(app)`` inside
``create_app()``.  Every request/response cycle will be logged with method,
path, status code, and duration.  The output goes through the standard
``logging`` module, so it respects whatever handlers ``setup_logging()``
has configured (console + file).
"""

import logging
import time

from flask import Flask, g, request

logger = logging.getLogger("academic_governance.request")


def init_request_logging(app: Flask) -> None:
    """Attach ``before_request`` / ``after_request`` hooks for access logging.

    Parameters
    ----------
    app:
        The Flask application instance.
    """

    @app.before_request
    def _start_timer() -> None:
        g._request_start = time.perf_counter()

    @app.after_request
    def _log_request(response):
        duration_ms = (time.perf_counter() - getattr(g, "_request_start", 0)) * 1000
        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
