"""User repository layer."""

from __future__ import annotations

from datetime import datetime

from academic_governance.db import db
from academic_governance.models import User


def get_user_by_email(email: str) -> User | None:
    return db.session.query(User).filter(User.email == email).first()


def list_user_emails() -> set[str]:
    return {email for (email,) in db.session.query(User.email).all()}


def create_user(
    email: str,
    role: str,
    created_at: datetime | None = None,
    *,
    commit: bool = True,
) -> User:
    user = User(email=email, role=role)
    if created_at is not None:
        user.created_at = created_at
    db.session.add(user)
    if commit:
        db.session.commit()
    return user


def get_or_create_user(
    email: str,
    role: str,
    created_at: datetime | None = None,
) -> tuple[User, bool]:
    user = get_user_by_email(email)
    if user is not None:
        return user, False
    return create_user(email, role, created_at=created_at), True


def commit() -> None:
    db.session.commit()
