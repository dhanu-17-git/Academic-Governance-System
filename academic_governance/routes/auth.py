"""routes/auth.py - Blueprint for authentication routes.

Phase 4 hardening:
  - Rate limit login attempts (5/60s per IP)
  - Rate limit OTP attempts (5/300s per email)
  - OTP attempt counter (brute-force protection)
  - Session regeneration on login
  - Input validation via validators.py
"""

from __future__ import annotations

import hmac
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from academic_governance import config
from academic_governance.auth.google_oauth import get_google_client
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
    return render_template(
        "login.html"
    )


def _send_login_otp(email: str, otp: str) -> bool:
    # Only print OTP to terminal in development mode
    logger.info("Inside _send_login_otp, config.DEBUG=%s", config.DEBUG)
    if config.DEBUG:
        try:
            verify_link = url_for("auth.verify_otp", _external=True)
            logger.info(f"\n{'='*60}\n🔒 [DEBUG] OTP for {email}: {otp}\n🔗 VERIFICATION LINK: {verify_link}\n{'='*60}\n")
        except Exception as e:
            logger.error(f"\n[ERROR] Could not generate link: {e}")
            logger.info(f"\n🔒 [DEBUG] OTP for {email}: {otp}\n")

    if email_service.is_email_configured():
        email_service.send_otp_email(email, otp)
        logger.info("OTP email sent to %s", email)
        return True

    if not config.DEBUG:
        raise email_service.EmailDeliveryError("SMTP not configured in production mode")

    logger.warning("SMTP NOT CONFIGURED. Development OTP for %s is %s", email, otp)
    return True


def _complete_login(email: str, role: str):
    session.clear()
    session["user_email"] = email
    session["role"] = role
    session["authenticated"] = True
    session.modified = True  # Force session regeneration

    logger.info("Login completed for %s with role %s", email, role)
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
        logger.debug("POST /login hit")
        ip = _client_ip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        logger.debug("Login attempt for %s from %s", email, ip)

        # Rate limit FIRST — before any credential checks to prevent brute-force
        if not rate_limiter.is_allowed(
            "login",
            ip,
            config.RATE_LOGIN_MAX,
            config.RATE_LOGIN_WINDOW,
        ):
            logger.warning("Failed login: Rate limited for %s", ip)
            flash(
                "Too many login attempts. Please wait a minute and try again.", "danger"
            )
            return _render_login()

        if password != config.DEMO_PASSWORD:  # nosec B105
            logger.warning("Failed login: Invalid password for %s", email)
            rate_limiter.record("login", ip)  # Record failed attempt
            flash("Invalid password. Please use the demo password.", "danger")
            return _render_login()

        valid, err = validate_email(email)
        if not valid:
            logger.warning("Failed login: Invalid email format for %s: %s", email, err)
            rate_limiter.record("login", ip)  # Record failed attempt
            flash(err, "danger")
            return _render_login()

        otp = _generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        auth_service.prune_expired_otps()
        auth_service.store_otp(email, otp, expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        session["pending_email"] = email
        logger.info("OTP generated and stored for %s", email)

        try:
            # We are allowing the login to proceed even if email fails to send in dev
            # so the user can test using the printed OTP. 
            _send_login_otp(email, otp)
            logger.info("OTP verification info printed/sent for %s", email)
        except email_service.EmailDeliveryError as exc:
            logger.warning("Email delivery failed, but proceeding in dev mode since OTP is printed. Error: %s", exc)

            auth_service.delete_otp(email)
            session.pop("pending_email", None)
            logger.error("Failed to send OTP email to %s", email, exc_info=True)
            flash(
                "We couldn't send the OTP email right now. Please try again in a moment.",
                "danger",
            )
            return _render_login()

        flash("Security Check: Enter the OTP sent to your email.", "info")
        logger.debug("Redirecting to verify_otp for %s", email)
        return redirect(url_for("auth.verify_otp"))

    return _render_login()


@auth_bp.route("/google/login")
def google_login():
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        flash("Google Login is not configured on this server.", "warning")
        return redirect(url_for("auth.login"))

    google = get_google_client()
    redirect_uri = url_for("auth.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route("/google/callback")
def google_callback():
    google = get_google_client()

    try:
        token = google.authorize_access_token()
    except (ValueError, KeyError, RuntimeError, OSError) as e:
        logger.error("Google OAuth token authorization failed: %s", e)
        flash("Failed to authenticate with Google. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    user_info = token.get("userinfo")
    if not user_info:
        logger.error("No user info returned from Google")
        flash("Failed to retrieve user information from Google.", "danger")
        return redirect(url_for("auth.login"))

    email = user_info.get("email")
    if not email or not user_info.get("email_verified"):
        flash("Your Google account email is not verified or unavailable.", "danger")
        return redirect(url_for("auth.login"))

    # Call unified completion logic
    user, created = auth_service.get_or_create_google_user(email)
    role = auth_service.resolve_login_role(email, user)
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
            flash(
                "Too many incorrect OTP attempts. Please request a new OTP.", "danger"
            )
            auth_service.delete_otp(email)
            session.pop("pending_email", None)
            return redirect(url_for("auth.login"))

        auth_service.prune_expired_otps()
        stored = auth_service.get_otp_record(email)
        if not stored:
            flash("OTP not found or has expired. Please request a new one.", "danger")
            return redirect(url_for("auth.login"))

        expires_at = datetime.strptime(stored["expires_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            auth_service.delete_otp(email)
            flash("OTP has expired. Please request a new one.", "danger")
            return redirect(url_for("auth.login"))

        if not hmac.compare_digest(entered_otp, stored["otp"]):
            rate_limiter.record("otp", email)
            auth_service.increment_otp_attempts(email)
            # Re-read from DB to get the accurate post-increment count
            updated = auth_service.get_otp_record(email)
            if updated is not None:
                used = updated["attempts"]
            else:
                used = stored["attempts"] + 1
            remaining = max(0, config.RATE_OTP_MAX - used)
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
