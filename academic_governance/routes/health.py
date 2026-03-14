"""Health-check endpoint for the Academic Governance System.

Provides ``GET /health`` which verifies database connectivity and returns a
JSON response.  The route is intentionally unauthenticated so that load
balancers, container orchestrators, and monitoring tools can probe it freely.
"""

import logging

from flask import Blueprint, jsonify
from sqlalchemy import text

from academic_governance.db import db

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return service health including database connectivity.

    Returns
    -------
    tuple
        A ``(response, status_code)`` pair.

        * **200** – service and database are healthy.
        * **503** – database is unreachable or returned an error.
    """
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as exc:
        logger.error("Health check failed: %s", exc, exc_info=True)
        return (
            jsonify({"status": "unhealthy", "database": "unreachable"}),
            503,
        )
