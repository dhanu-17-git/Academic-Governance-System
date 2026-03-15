"""Notification service layer."""

from datetime import datetime

from academic_governance.db import db
from academic_governance.models import Notification
from academic_governance.services.security import sanitize_text, sanitize_url


def _serialize_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def create_notification(title: str, message: str, link: str = "") -> int:
    notification = Notification(title=title, message=message, link=link)
    db.session.add(notification)
    db.session.commit()
    return notification.id


def create_notification_from_form(
    title_raw: str, message_raw: str, link_raw: str = ""
) -> dict:
    title = sanitize_text(title_raw, max_length=150)
    message = sanitize_text(message_raw, max_length=1000)
    link = sanitize_url(link_raw, max_length=300)

    if not title or not message:
        return {
            "success": False,
            "flash_category": "danger",
            "message": "Title and message are required.",
        }

    notification_id = create_notification(title, message, link)
    return {
        "success": True,
        "flash_category": "success",
        "message": f'Notification "{title}" sent to all students!',
        "title": title,
        "notification_id": notification_id,
    }


def get_notifications(limit: int = 10) -> list[dict]:
    notifications = (
        db.session.query(Notification)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "link": notification.link,
            "created_at": _serialize_dt(notification.created_at),
        }
        for notification in notifications
    ]
