"""Email delivery helpers for authentication and notifications."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from academic_governance import config


class EmailDeliveryError(RuntimeError):
    """Raised when an email could not be delivered."""


def is_email_configured() -> bool:
    sender = config.EMAIL_FROM or config.EMAIL_USER
    return bool(config.EMAIL_HOST and sender)


def send_email(
    recipient: str,
    subject: str,
    text_body: str,
    *,
    html_body: str | None = None,
) -> None:
    if not is_email_configured():
        raise EmailDeliveryError("Email delivery is not configured.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.EMAIL_FROM or config.EMAIL_USER
    message["To"] = recipient
    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    smtp_factory = smtplib.SMTP_SSL if config.EMAIL_USE_SSL else smtplib.SMTP

    try:
        with smtp_factory(
            config.EMAIL_HOST,
            config.EMAIL_PORT,
            timeout=config.EMAIL_TIMEOUT,
        ) as smtp:
            smtp.ehlo()
            if config.EMAIL_USE_TLS and not config.EMAIL_USE_SSL:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if config.EMAIL_USER:
                smtp.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - exercised via monkeypatching
        raise EmailDeliveryError("Unable to send email.") from exc


def send_otp_email(recipient: str, otp: str, *, expires_in_minutes: int = 5) -> None:
    subject = "Your Academic Governance System OTP"
    text_body = (
        "Your Academic Governance System verification code is "
        f"{otp}. It expires in {expires_in_minutes} minutes."
    )
    html_body = (
        "<p>Your Academic Governance System verification code is "
        f"<strong>{otp}</strong>.</p>"
        f"<p>It expires in {expires_in_minutes} minutes.</p>"
    )
    send_email(recipient, subject, text_body, html_body=html_body)


def send_complaint_status_email(
    recipient: str,
    complaint_id: str,
    status: str,
    *,
    admin_response: str = "",
) -> None:
    subject = f"Complaint {complaint_id} status update"
    response_block = ""
    html_response_block = ""
    if admin_response:
        response_block = f"\n\nAdmin response:\n{admin_response}"
        html_response_block = f"<p><strong>Admin response:</strong> {admin_response}</p>"

    text_body = (
        f"Your complaint {complaint_id} is now marked as {status}."
        f"{response_block}\n\nPlease log in to the Academic Governance System for more details."
    )
    html_body = (
        f"<p>Your complaint <strong>{complaint_id}</strong> is now marked as "
        f"<strong>{status}</strong>.</p>"
        f"{html_response_block}"
        "<p>Please log in to the Academic Governance System for more details.</p>"
    )
    send_email(recipient, subject, text_body, html_body=html_body)