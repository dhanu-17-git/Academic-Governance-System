"""Authentication service layer."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from academic_governance import config
from academic_governance.db import db
from academic_governance.models import OtpCode, RateLimitEvent, User
from academic_governance.repositories import user_repository


def _now() -> datetime:
    return datetime.now(timezone.utc)


def store_otp(email: str, otp: str, expires_at: str) -> None:
    from datetime import timezone
    parsed_expires_at = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    existing = db.session.get(OtpCode, email)
    if existing is None:
        db.session.add(
            OtpCode(
                email=email,
                otp=otp,
                expires_at=parsed_expires_at,
                attempts=0,
            )
        )
    else:
        existing.otp = otp
        existing.expires_at = parsed_expires_at
        existing.attempts = 0
        existing.created_at = _now()
    db.session.commit()


def get_otp_record(email: str):
    from datetime import timezone
    record = db.session.get(OtpCode, email)
    if record is None:
        return None
    
    # Ensure expires_at treats the DB datetime as UTC
    exp_at = record.expires_at
    if exp_at.tzinfo is None:
        exp_at = exp_at.replace(tzinfo=timezone.utc)
        
    return {
        "email": record.email,
        "otp": record.otp,
        "expires_at": exp_at.strftime("%Y-%m-%d %H:%M:%S"),
        "attempts": record.attempts,
    }


def increment_otp_attempts(email: str) -> None:
    record = db.session.get(OtpCode, email)
    if record is not None:
        record.attempts += 1
        db.session.commit()


def delete_otp(email: str) -> None:
    record = db.session.get(OtpCode, email)
    if record is not None:
        db.session.delete(record)
        db.session.commit()


def prune_expired_otps() -> None:
    threshold = _now()
    (
        db.session.query(OtpCode)
        .filter(OtpCode.expires_at <= threshold)
        .delete(synchronize_session=False)
    )
    db.session.commit()


def record_rate_limit_attempt(action: str, identifier: str) -> None:
    db.session.add(
        RateLimitEvent(
            action=action,
            identifier=identifier,
            created_at=_now(),
        )
    )
    db.session.commit()


def prune_rate_limit_entries(action: str, identifier: str, window: int) -> None:
    threshold = _now() - timedelta(seconds=window)
    (
        db.session.query(RateLimitEvent)
        .filter(RateLimitEvent.action == action)
        .filter(RateLimitEvent.identifier == identifier)
        .filter(RateLimitEvent.created_at <= threshold)
        .delete(synchronize_session=False)
    )
    db.session.commit()


def get_rate_limit_count(action: str, identifier: str, window: int) -> int:
    threshold = _now() - timedelta(seconds=window)
    return (
        db.session.query(RateLimitEvent)
        .filter(RateLimitEvent.action == action)
        .filter(RateLimitEvent.identifier == identifier)
        .filter(RateLimitEvent.created_at > threshold)
        .count()
    )


def reset_rate_limit(action: str, identifier: str) -> None:
    (
        db.session.query(RateLimitEvent)
        .filter(RateLimitEvent.action == action)
        .filter(RateLimitEvent.identifier == identifier)
        .delete(synchronize_session=False)
    )
    db.session.commit()


def get_user(email: str) -> User | None:
    return user_repository.get_user_by_email(email)


def get_or_create_google_user(email: str) -> tuple[User, bool]:
    return user_repository.get_or_create_user(
        email, config.ROLE_STUDENT, created_at=_now()
    )


def resolve_login_role(
    email: str,
    user: User | None = None,
    *,
    allow_admin_fallback: bool = True,
) -> str:
    if user is not None and user.role:
        return user.role
    if allow_admin_fallback and email in config.ADMIN_EMAILS:
        return config.ROLE_ADMIN
    return config.ROLE_STUDENT
