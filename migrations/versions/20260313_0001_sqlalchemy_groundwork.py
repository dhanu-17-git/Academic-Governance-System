"""sqlalchemy groundwork

Revision ID: 20260313_0001
Revises:
Create Date: 2026-03-13 21:05:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260313_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=32), server_default="Submitted", nullable=False
        ),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "otp_codes",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("otp", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("email"),
    )
    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("identifier", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rate_limit_lookup",
        "rate_limit_events",
        ["action", "identifier", "created_at"],
        unique=False,
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "sentiment", sa.String(length=32), server_default="Neutral", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "campus_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_email", sa.String(length=255), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_name", sa.String(length=255), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "role", sa.String(length=32), server_default="student", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "labs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lab_name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_name"),
    )
    op.create_table(
        "complaint_ownership",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=32), nullable=False),
        sa.Column("student_email", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_complaint_ownership_student_email"),
        "complaint_ownership",
        ["student_email"],
        unique=False,
    )
    op.create_table(
        "student_subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_email", sa.String(length=255), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_student_subjects_student_email"),
        "student_subjects",
        ["student_email"],
        unique=False,
    )
    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_email", sa.String(length=255), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("total_classes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attended_classes", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attendance_student_email"),
        "attendance",
        ["student_email"],
        unique=False,
    )
    op.create_table(
        "marks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_email", sa.String(length=255), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("internal_marks", sa.Integer(), server_default="0", nullable=False),
        sa.Column("assignment_marks", sa.Integer(), server_default="0", nullable=False),
        sa.Column("exam_marks", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_marks_student_email"), "marks", ["student_email"], unique=False
    )
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_path"),
    )
    op.create_table(
        "timetable",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.String(length=32), nullable=False),
        sa.Column("time_slot", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("room", sa.String(length=120), nullable=True),
        sa.Column(
            "slot_type", sa.String(length=32), server_default="class", nullable=False
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lab_systems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("row_label", sa.String(length=16), nullable=False),
        sa.Column("seat_number", sa.Integer(), nullable=False),
        sa.Column("system_code", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default="working", nullable=False
        ),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_id", "row_label", "seat_number"),
    )
    op.create_index("idx_lab_sys", "lab_systems", ["lab_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_lab_sys", table_name="lab_systems")
    op.drop_table("lab_systems")
    op.drop_table("timetable")
    op.drop_table("notes")
    op.drop_index(op.f("ix_marks_student_email"), table_name="marks")
    op.drop_table("marks")
    op.drop_index(op.f("ix_attendance_student_email"), table_name="attendance")
    op.drop_table("attendance")
    op.drop_index(
        op.f("ix_student_subjects_student_email"), table_name="student_subjects"
    )
    op.drop_table("student_subjects")
    op.drop_index(
        op.f("ix_complaint_ownership_student_email"), table_name="complaint_ownership"
    )
    op.drop_table("complaint_ownership")
    op.drop_table("labs")
    op.drop_table("users")
    op.drop_table("notifications")
    op.drop_table("subjects")
    op.drop_table("audit_log")
    op.drop_table("campus_updates")
    op.drop_table("feedback")
    op.drop_index("idx_rate_limit_lookup", table_name="rate_limit_events")
    op.drop_table("rate_limit_events")
    op.drop_table("otp_codes")
    op.drop_table("complaints")
