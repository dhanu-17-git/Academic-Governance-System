"""Application package for the Academic Governance System."""

import logging
import os
import traceback
from datetime import timedelta

from flask import Flask, abort, render_template, request, send_from_directory, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from academic_governance import config
from academic_governance import models  # noqa: F401
from academic_governance.auth.google_oauth import init_google_oauth
from academic_governance.db import db, migrate
from academic_governance.routes.admin import admin_bp
from academic_governance.routes.auth import auth_bp
from academic_governance.routes.health import health_bp
from academic_governance.routes.student import student_bp
from academic_governance.services import academic_service
from academic_governance.services import complaint_service
from academic_governance.services import notification_service
from academic_governance.utils.logging_config import setup_logging
from academic_governance.utils.request_logging import init_request_logging
from academic_governance.utils.sentry_config import init_sentry

csrf = CSRFProtect()


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(config.ROOT_DIR, "templates"),
        static_folder=os.path.join(config.ROOT_DIR, "static"),
    )

    app.secret_key = config.SECRET_KEY
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE
    app.config["DEBUG"] = config.DEBUG
    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
    app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
    app.config["WTF_CSRF_ENABLED"] = config.WTF_CSRF_ENABLED
    app.config["WTF_CSRF_TIME_LIMIT"] = config.WTF_CSRF_TIME_LIMIT
    app.config["GOOGLE_CLIENT_ID"] = config.GOOGLE_CLIENT_ID
    app.config["GOOGLE_CLIENT_SECRET"] = config.GOOGLE_CLIENT_SECRET

    setup_logging(logging.DEBUG if config.DEBUG else logging.INFO)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    init_sentry(app)
    init_google_oauth(app)
    init_request_logging(app)

    @app.context_processor
    def inject_notifications():
        if "user_email" in session and session.get("role") == config.ROLE_STUDENT:
            try:
                return {
                    "notifications": notification_service.get_notifications(limit=10)
                }
            except Exception:
                app.logger.warning(
                    "Unable to load notifications for %s",
                    session.get("user_email"),
                    exc_info=True,
                )
        return {"notifications": []}

    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    from academic_governance.routes.chatbot import chatbot_bp

    app.register_blueprint(chatbot_bp)

    @app.errorhandler(400)
    def bad_request(error):
        desc = (
            error.description
            if hasattr(error, "description")
            else "Please check your input."
        )
        if "CSRF" in desc:
            desc += " Please go back, refresh the page, and try again."
        return (
            render_template(
                "error.html", error_code=400, error_message=f"Bad request. {desc}"
            ),
            400,
        )

    @app.errorhandler(403)
    def forbidden(error):
        return (
            render_template(
                "error.html",
                error_code=403,
                error_message="Access denied. You do not have permission.",
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "error.html", error_code=404, error_message="Page not found."
        ), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return (
            render_template(
                "error.html",
                error_code=429,
                error_message="Too many requests. Please slow down.",
            ),
            429,
        )

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(
            "500 error: %s\n%s", error, traceback.format_exc(), exc_info=True
        )
        return (
            render_template(
                "error.html",
                error_code=500,
                error_message="Internal server error. Our team has been notified.",
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.error("Unhandled exception: %s", error, exc_info=True)
        return (
            render_template(
                "error.html",
                error_code=500,
                error_message="Internal server error. Our team has been notified.",
            ),
            500,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(error):
        from flask import flash, redirect

        flash("File too large. Maximum allowed size is 16 MB.", "danger")
        return redirect(request.referrer or "/raise-complaint")

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        if "user_email" not in session:
            abort(403)

        current_email = session["user_email"]
        role = session.get("role")

        if role == config.ROLE_ADMIN:
            return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

        norm = filename.replace("\\", "/")
        if norm.startswith("notes/"):
            note = academic_service.get_note_by_path(norm)
            if note is None:
                abort(403)
            enrolled = academic_service.get_student_attendance(current_email)
            enrolled_subject_ids = {r["subject_id"] for r in enrolled}
            if note["subject_id"] not in enrolled_subject_ids:
                abort(403)
            return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

        if "/" in norm or "\\" in norm:
            complaint_id = norm.split("/")[0]
            owner = complaint_service.get_complaint_owner(complaint_id)
            if owner != current_email:
                abort(403)
        else:
            abort(403)

        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.after_request
    def set_security_headers(response):
        is_prod = os.environ.get("FLASK_ENV", "development") == "production"

        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com;"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"

        if is_prod:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    return app
