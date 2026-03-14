"""Complaint and feedback service layer."""

from __future__ import annotations

import logging
import os
import random
import string
from datetime import datetime, timezone

from werkzeug.utils import secure_filename

from academic_governance import config
from academic_governance.repositories import complaint_repository
from academic_governance.services import email_service

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _generate_complaint_id() -> str:
    return "CMP" + "".join(random.choices(string.digits, k=8))


def _build_temp_upload_folder() -> tuple[str, str]:
    temp_id = "TMP" + "".join(random.choices(string.digits, k=8))
    folder = os.path.join(config.UPLOAD_FOLDER, temp_id)
    os.makedirs(folder, exist_ok=True)
    return temp_id, folder


def _build_upload_filename(original_name: str) -> str:
    filename = os.path.basename(secure_filename(original_name))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{unique}_{filename}"


def create_complaint(
    category: str,
    description: str,
    student_email: str,
    file_path: str | None = None,
    url: str = "",
) -> str:
    complaint_id = _generate_complaint_id()
    complaint = complaint_repository.create_complaint(
        complaint_id=complaint_id,
        category=category,
        description=description,
        student_email=student_email,
        file_path=file_path,
        url=url,
    )
    return complaint.id


def create_complaint_with_upload(
    category: str,
    description: str,
    student_email: str,
    file_storage,
    url: str = "",
) -> str:
    temp_id, temp_folder = _build_temp_upload_folder()
    filename = _build_upload_filename(file_storage.filename or "upload")
    save_path = os.path.join(temp_folder, filename)
    file_storage.save(save_path)

    file_path = "/" + save_path.replace("\\", "/")
    complaint_id = create_complaint(
        category,
        description,
        student_email,
        file_path=file_path,
        url=url,
    )
    real_folder = os.path.join(config.UPLOAD_FOLDER, complaint_id)
    os.rename(temp_folder, real_folder)
    final_file_path = file_path.replace(temp_id, complaint_id)

    complaint_repository.update_complaint_file_path(complaint_id, final_file_path)
    return complaint_id


def get_student_complaints(student_email: str) -> dict[str, int]:
    total = complaint_repository.count_student_complaints(student_email)
    pending = complaint_repository.count_student_complaints_by_statuses(
        student_email,
        ("Submitted", "Under Review"),
    )
    resolved = complaint_repository.count_student_complaints_by_status(
        student_email,
        "Resolved",
    )
    return {"total": total, "pending": pending, "resolved": resolved}


def get_complaint_by_id(complaint_id: str):
    row = complaint_repository.get_complaint_with_owner(complaint_id)
    if row is None:
        return None
    complaint, student_email = row
    return {
        "id": complaint.id,
        "category": complaint.category,
        "description": complaint.description,
        "file_path": complaint.file_path,
        "url": complaint.url,
        "status": complaint.status,
        "admin_response": complaint.admin_response,
        "created_at": _serialize_dt(complaint.created_at),
        "updated_at": _serialize_dt(complaint.updated_at),
        "student_email": student_email,
    }


def update_complaint_status(
    complaint_id: str,
    new_status: str,
    admin_response: str = "",
) -> tuple[bool, str]:
    if new_status not in config.VALID_STATUSES:
        return False, "Invalid status value."

    current = get_complaint_by_id(complaint_id)
    if not current:
        return False, "Complaint not found."

    current_status = current["status"]
    allowed_next = config.STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        return False, (
            f'Cannot move from "{current_status}" to "{new_status}". '
            f'Allowed transitions: {sorted(allowed_next) or "none (terminal state)"}'
        )

    updated = complaint_repository.update_complaint_status(
        complaint_id,
        new_status,
        admin_response,
        _now(),
    )
    if updated is None:
        return False, "Complaint not found."

    owner_email = complaint_repository.get_complaint_owner(complaint_id)
    if owner_email and email_service.is_email_configured():
        try:
            email_service.send_complaint_status_email(
                owner_email,
                complaint_id,
                new_status,
                admin_response=admin_response,
            )
        except email_service.EmailDeliveryError:
            logger.warning(
                "Complaint status email delivery failed for %s",
                complaint_id,
                exc_info=True,
            )

    return True, ""


def get_complaint_owner(complaint_id: str) -> str | None:
    return complaint_repository.get_complaint_owner(complaint_id)


def log_admin_action(admin_email: str, action: str) -> None:
    complaint_repository.create_audit_log(admin_email, action)


def get_all_complaint_stats() -> dict[str, int]:
    total = complaint_repository.count_all_complaints()
    pending = complaint_repository.count_complaints_by_statuses(("Submitted", "Under Review"))
    resolved = complaint_repository.count_complaints_by_status("Resolved")
    return {"total": total, "pending": pending, "resolved": resolved}


def get_complaints_by_category(categories: list[str]) -> list[int]:
    return [complaint_repository.count_complaints_by_category(category) for category in categories]


def get_recent_complaints(limit: int = 10) -> list[dict]:
    complaints = complaint_repository.list_recent_complaints(limit=limit)
    return [
        {
            "id": complaint.id,
            "category": complaint.category,
            "description": complaint.description,
            "file_path": complaint.file_path,
            "url": complaint.url,
            "status": complaint.status,
            "admin_response": complaint.admin_response,
            "created_at": _serialize_dt(complaint.created_at),
            "updated_at": _serialize_dt(complaint.updated_at),
        }
        for complaint in complaints
    ]


def get_admin_dashboard_context(categories: list[str], recent_limit: int = 10) -> dict:
    stats = get_all_complaint_stats()
    sentiments = get_sentiment_distribution()
    return {
        "total_complaints": stats["total"],
        "pending_issues": stats["pending"],
        "resolved_issues": stats["resolved"],
        "avg_rating": get_average_rating(),
        "categories": categories,
        "complaint_counts": get_complaints_by_category(categories),
        "sentiment_labels": [row["sentiment"] for row in sentiments],
        "sentiment_counts": [row["count"] for row in sentiments],
        "recent_complaints": get_recent_complaints(limit=recent_limit),
    }


def create_feedback(subject: str, rating: int, comment: str, sentiment: str) -> None:
    complaint_repository.create_feedback(subject, rating, comment, sentiment)


def get_average_rating() -> float:
    avg = complaint_repository.get_average_rating()
    return round(avg, 1) if avg else 0.0


def get_sentiment_distribution() -> list[dict]:
    rows = complaint_repository.get_sentiment_distribution_rows()
    return [{"sentiment": sentiment, "count": count} for sentiment, count in rows]


def get_campus_updates(limit: int = 5) -> list[dict]:
    updates = complaint_repository.list_campus_updates(limit=limit)
    return [
        {
            "id": update.id,
            "title": update.title,
            "content": update.content,
            "category": update.category,
            "created_at": _serialize_dt(update.created_at),
        }
        for update in updates
    ]