"""Complaint repository layer."""

from __future__ import annotations

from datetime import datetime

from academic_governance.db import db
from academic_governance.models import AuditLog, CampusUpdate, Complaint, ComplaintOwnership, Feedback


def create_complaint(
    complaint_id: str,
    category: str,
    description: str,
    student_email: str,
    file_path: str | None = None,
    url: str = "",
) -> Complaint:
    complaint = Complaint(
        id=complaint_id,
        category=category,
        description=description,
        file_path=file_path,
        url=url,
    )
    ownership = ComplaintOwnership(
        complaint_id=complaint_id,
        student_email=student_email,
    )
    db.session.add(complaint)
    db.session.add(ownership)
    db.session.commit()
    return complaint


def update_complaint_file_path(complaint_id: str, file_path: str) -> Complaint | None:
    complaint = db.session.get(Complaint, complaint_id)
    if complaint is None:
        return None
    complaint.file_path = file_path
    db.session.commit()
    return complaint


def count_student_complaints(student_email: str) -> int:
    return (
        db.session.query(ComplaintOwnership)
        .filter(ComplaintOwnership.student_email == student_email)
        .count()
    )


def count_student_complaints_by_statuses(student_email: str, statuses: tuple[str, ...]) -> int:
    return (
        db.session.query(Complaint)
        .join(ComplaintOwnership, Complaint.id == ComplaintOwnership.complaint_id)
        .filter(ComplaintOwnership.student_email == student_email)
        .filter(Complaint.status.in_(statuses))
        .count()
    )


def count_student_complaints_by_status(student_email: str, status: str) -> int:
    return (
        db.session.query(Complaint)
        .join(ComplaintOwnership, Complaint.id == ComplaintOwnership.complaint_id)
        .filter(ComplaintOwnership.student_email == student_email)
        .filter(Complaint.status == status)
        .count()
    )


def get_complaint_with_owner(complaint_id: str):
    return (
        db.session.query(Complaint, ComplaintOwnership.student_email)
        .outerjoin(ComplaintOwnership, Complaint.id == ComplaintOwnership.complaint_id)
        .filter(Complaint.id == complaint_id)
        .first()
    )


def get_complaint(complaint_id: str) -> Complaint | None:
    return db.session.get(Complaint, complaint_id)


def update_complaint_status(
    complaint_id: str,
    new_status: str,
    admin_response: str,
    updated_at: datetime,
) -> Complaint | None:
    complaint = db.session.get(Complaint, complaint_id)
    if complaint is None:
        return None
    complaint.status = new_status
    complaint.admin_response = admin_response
    complaint.updated_at = updated_at
    db.session.commit()
    return complaint


def get_complaint_owner(complaint_id: str) -> str | None:
    return (
        db.session.query(ComplaintOwnership.student_email)
        .filter(ComplaintOwnership.complaint_id == complaint_id)
        .scalar()
    )


def create_audit_log(admin_email: str, action: str) -> AuditLog:
    entry = AuditLog(admin_email=admin_email, action=action)
    db.session.add(entry)
    db.session.commit()
    return entry


def count_all_complaints() -> int:
    return db.session.query(Complaint).count()


def count_complaints_by_statuses(statuses: tuple[str, ...]) -> int:
    return db.session.query(Complaint).filter(Complaint.status.in_(statuses)).count()


def count_complaints_by_status(status: str) -> int:
    return db.session.query(Complaint).filter(Complaint.status == status).count()


def count_complaints_by_category(category: str) -> int:
    return db.session.query(Complaint).filter(Complaint.category == category).count()


def list_recent_complaints(limit: int = 10) -> list[Complaint]:
    return db.session.query(Complaint).order_by(Complaint.created_at.desc()).limit(limit).all()


def create_feedback(subject: str, rating: int, comment: str, sentiment: str) -> Feedback:
    feedback = Feedback(
        subject=subject,
        rating=rating,
        comment=comment,
        sentiment=sentiment,
    )
    db.session.add(feedback)
    db.session.commit()
    return feedback


def get_average_rating() -> float | None:
    return db.session.query(db.func.avg(Feedback.rating)).scalar()


def get_sentiment_distribution_rows():
    return (
        db.session.query(Feedback.sentiment, db.func.count(Feedback.id).label("count"))
        .group_by(Feedback.sentiment)
        .all()
    )


def list_campus_updates(limit: int = 5) -> list[CampusUpdate]:
    return db.session.query(CampusUpdate).order_by(CampusUpdate.created_at.desc()).limit(limit).all()


def list_student_grievances(student_email: str, limit: int = 5):
    return (
        db.session.query(Complaint.category, Complaint.status, Complaint.created_at)
        .join(ComplaintOwnership, Complaint.id == ComplaintOwnership.complaint_id)
        .filter(ComplaintOwnership.student_email == student_email)
        .order_by(Complaint.created_at.desc())
        .limit(limit)
        .all()
    )