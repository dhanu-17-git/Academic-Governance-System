"""SQLAlchemy models that define the migration-managed schema."""

from __future__ import annotations

from academic_governance.db import db


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.String(32), primary_key=True)
    category = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.Text)
    url = db.Column(db.Text)
    status = db.Column(db.String(32), nullable=False, server_default="Submitted")
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False,
    )


class ComplaintOwnership(db.Model):
    __tablename__ = "complaint_ownership"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(32), db.ForeignKey("complaints.id"), nullable=False)
    student_email = db.Column(db.String(255), nullable=False, index=True)


class OtpCode(db.Model):
    __tablename__ = "otp_codes"

    email = db.Column(db.String(255), primary_key=True)
    otp = db.Column(db.String(16), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    attempts = db.Column(db.Integer, nullable=False, server_default="0")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class RateLimitEvent(db.Model):
    __tablename__ = "rate_limit_events"
    __table_args__ = (
        db.Index("idx_rate_limit_lookup", "action", "identifier", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(64), nullable=False)
    identifier = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    sentiment = db.Column(db.String(32), nullable=False, server_default="Neutral")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class CampusUpdate(db.Model):
    __tablename__ = "campus_updates"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(120))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    admin_email = db.Column(db.String(255), nullable=False)
    action = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(255), nullable=False)
    credits = db.Column(db.Integer, nullable=False)


class StudentSubject(db.Model):
    __tablename__ = "student_subjects"

    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(255), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(255), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    total_classes = db.Column(db.Integer, nullable=False, server_default="0")
    attended_classes = db.Column(db.Integer, nullable=False, server_default="0")
    last_updated = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Mark(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(255), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    internal_marks = db.Column(db.Integer, nullable=False, server_default="0")
    assignment_marks = db.Column(db.Integer, nullable=False, server_default="0")
    exam_marks = db.Column(db.Integer, nullable=False, server_default="0")
    last_updated = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False, unique=True)
    uploaded_by = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class TimetableSlot(db.Model):
    __tablename__ = "timetable"

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(32), nullable=False)
    time_slot = db.Column(db.String(64), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    room = db.Column(db.String(120))
    slot_type = db.Column(db.String(32), nullable=False, server_default="class")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.Text, nullable=False, server_default="")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    role = db.Column(db.String(32), nullable=False, server_default="student")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class Lab(db.Model):
    __tablename__ = "labs"

    id = db.Column(db.Integer, primary_key=True)
    lab_name = db.Column(db.String(255), nullable=False, unique=True)


class LabSystem(db.Model):
    __tablename__ = "lab_systems"
    __table_args__ = (
        db.Index("idx_lab_sys", "lab_id"),
        db.UniqueConstraint("lab_id", "row_label", "seat_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey("labs.id"), nullable=False)
    row_label = db.Column(db.String(16), nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    system_code = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False, server_default="working")
    last_updated = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
