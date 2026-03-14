"""routes/auth.py - Blueprint for authentication routes.

Phase 4 hardening:
  - Rate limit login attempts (5/60s per IP)
  - Rate limit OTP attempts (5/300s per email)
  - OTP attempt counter (brute-force protection)
  - Session regeneration on login
  - Input validation via validators.py
"""

from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from academic_governance import config
from academic_governance.auth.google_oauth import OAuthError, get_google_client, is_google_oauth_configured
from academic_governance.services import auth_service, email_service
from academic_governance.services.security import rate_limiter
from academic_governance.services.validators import validate_email

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _generate_otp() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


def _client_ip() -> str:
    # Security fix: prioritize remote_addr.
    # Only trust X-Forwarded-For if explicitly configured (which we haven't done here).
    return request.remote_addr or "unknown"


def _render_login():
    return render_template("login.html", google_oauth_enabled=is_google_oauth_configured())


def _send_login_otp(email: str, otp: str) -> bool:
    if email_service.is_email_configured():
        email_service.send_otp_email(email, otp)
        logger.info("OTP email sent to %s", email)
        return True

    if config.DEBUG:
        print(f"\n{'='*50}")
        print(f"  DEV OTP for {email}: {otp}")
        print(f"{'='*50}\n")
        logger.info("SMTP not configured; development OTP for %s is %s", email, otp)
        return True

    logger.error("OTP requested for %s but email delivery is not configured", email)
    return False


def _complete_login(email: str, role: str):
    session.clear()
    session["user_email"] = email
    session["role"] = role
    session["login_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.permanent = False

    flash("Login successful!", "success")
    if role == config.ROLE_ADMIN:
        return redirect(url_for("admin.admin_dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = _client_ip()
        email = request.form.get("email", "").strip().lower()

        if not rate_limiter.is_allowed(
            "login",
            ip,
            config.RATE_LOGIN_MAX,
            config.RATE_LOGIN_WINDOW,
        ):
            flash("Too many login attempts. Please wait a minute and try again.", "danger")
            return _render_login()

        rate_limiter.record("login", ip)

        valid, err = validate_email(email)
        if not valid:
            flash(err, "danger")
            return _render_login()

        otp = _generate_otp()
        expires_at = datetime.now() + timedelta(minutes=5)
        auth_service.prune_expired_otps()
        auth_service.store_otp(email, otp, expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        session["pending_email"] = email

        try:
            if not _send_login_otp(email, otp):
                auth_service.delete_otp(email)
                session.pop("pending_email", None)
                flash("Login is temporarily unavailable. Please contact support.", "danger")
                return _render_login()
        except email_service.EmailDeliveryError:
            auth_service.delete_otp(email)
            session.pop("pending_email", None)
            logger.error("Failed to send OTP email to %s", email, exc_info=True)
            flash("We couldn't send the OTP email right now. Please try again in a moment.", "danger")
            return _render_login()

        flash("Security Check: Enter the OTP sent to your email.", "info")
        return redirect(url_for("auth.verify_otp"))

    return _render_login()


@auth_bp.route("/login/google")
def google_login():
    client = get_google_client()
    if client is None:
        flash("Google login is not configured right now.", "warning")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.google_callback", _external=True)
    return client.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/google/callback")
def google_callback():
    client = get_google_client()
    if client is None:
        flash("Google login is not configured right now.", "warning")
        return redirect(url_for("auth.login"))

    try:
        token = client.authorize_access_token()
        user_info = token.get("userinfo")
        if user_info is None and hasattr(client, "userinfo"):
            user_info = client.userinfo()
            if hasattr(user_info, "json"):
                user_info = user_info.json()
    except OAuthError:
        flash("Google login failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    if not isinstance(user_info, dict):
        flash("Google login failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    email = str(user_info.get("email", "")).strip().lower()
    email_verified = bool(user_info.get("email_verified", False))
    valid, err = validate_email(email)
    if not valid or not email_verified:
        flash(err if not valid else "Google account email is not verified.", "danger")
        return redirect(url_for("auth.login"))

    user, created = auth_service.get_or_create_google_user(email)
    role = auth_service.resolve_login_role(email, user=user, allow_admin_fallback=False)

    logger.info("Google login succeeded for %s (created=%s)", email, created)
    return _complete_login(email, role)


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "pending_email" not in session:
        return redirect(url_for("auth.login"))

    email = session["pending_email"]

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()

        if not rate_limiter.is_allowed(
            "otp",
            email,
            config.RATE_OTP_MAX,
            config.RATE_OTP_WINDOW,
        ):
            flash("Too many incorrect OTP attempts. Please request a new OTP.", "danger")
            auth_service.delete_otp(email)
            session.pop("pending_email", None)
            return redirect(url_for("auth.login"))

        auth_service.prune_expired_otps()
        stored = auth_service.get_otp_record(email)
        if not stored:
            flash("OTP not found or has expired. Please request a new one.", "danger")
            return redirect(url_for("auth.login"))

        expires_at = datetime.strptime(stored["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires_at:
            auth_service.delete_otp(email)
            flash("OTP has expired. Please request a new one.", "danger")
            return redirect(url_for("auth.login"))

        if entered_otp != stored["otp"]:
            rate_limiter.record("otp", email)
            auth_service.increment_otp_attempts(email)
            remaining = max(0, config.RATE_OTP_MAX - (stored["attempts"] + 1))
            flash(f"Invalid OTP. {remaining} attempt(s) remaining.", "danger")
            return render_template("verify_otp.html", email=email)

        auth_service.delete_otp(email)
        rate_limiter.reset("otp", email)
        rate_limiter.reset("login", _client_ip())

        role = auth_service.resolve_login_role(email)
        return _complete_login(email, role)

    return render_template("verify_otp.html", email=email)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))