"""Academic repository layer."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.sql.elements import ColumnElement

from academic_governance.db import db
from academic_governance.models import Attendance, Mark, Note, StudentSubject, Subject, TimetableSlot


def list_subjects() -> list[Subject]:
    return db.session.query(Subject).order_by(Subject.id).all()


def create_subject(subject_name: str, credits: int) -> Subject:
    subject = Subject(subject_name=subject_name, credits=credits)
    db.session.add(subject)
    return subject


def count_timetable_slots() -> int:
    return db.session.query(TimetableSlot).count()


def create_timetable_slot(
    day_of_week: str,
    time_slot: str,
    subject_id: int,
    room: str,
    slot_type: str = "class",
) -> TimetableSlot:
    slot = TimetableSlot(
        day_of_week=day_of_week,
        time_slot=time_slot,
        subject_id=subject_id,
        room=room,
        slot_type=slot_type,
    )
    db.session.add(slot)
    return slot


def list_student_attendance_rows(student_email: str):
    return (
        db.session.query(Attendance, Subject.subject_name, Subject.credits)
        .join(Subject, Attendance.subject_id == Subject.id)
        .filter(Attendance.student_email == student_email)
        .order_by(Subject.id)
        .all()
    )


def list_student_mark_rows(student_email: str):
    return (
        db.session.query(Mark, Subject.subject_name)
        .join(Subject, Mark.subject_id == Subject.id)
        .filter(Mark.student_email == student_email)
        .order_by(Subject.id)
        .all()
    )


def get_attendance_subject_ids(student_email: str) -> set[int]:
    return {
        subject_id
        for (subject_id,) in (
            db.session.query(Attendance.subject_id)
            .filter(Attendance.student_email == student_email)
            .all()
        )
    }


def get_student_subject_ids(student_email: str) -> set[int]:
    return {
        subject_id
        for (subject_id,) in (
            db.session.query(StudentSubject.subject_id)
            .filter(StudentSubject.student_email == student_email)
            .all()
        )
    }


def add_student_subject(student_email: str, subject_id: int) -> StudentSubject:
    row = StudentSubject(student_email=student_email, subject_id=subject_id)
    db.session.add(row)
    return row


def add_attendance_record(
    student_email: str,
    subject_id: int,
    total_classes: int,
    attended_classes: int,
    last_updated: datetime,
) -> Attendance:
    record = Attendance(
        student_email=student_email,
        subject_id=subject_id,
        total_classes=total_classes,
        attended_classes=attended_classes,
        last_updated=last_updated,
    )
    db.session.add(record)
    return record


def add_mark_record(
    student_email: str,
    subject_id: int,
    internal_marks: int,
    assignment_marks: int,
    exam_marks: int,
    last_updated: datetime,
) -> Mark:
    record = Mark(
        student_email=student_email,
        subject_id=subject_id,
        internal_marks=internal_marks,
        assignment_marks=assignment_marks,
        exam_marks=exam_marks,
        last_updated=last_updated,
    )
    db.session.add(record)
    return record


def commit() -> None:
    db.session.commit()


def list_note_rows():
    return (
        db.session.query(Note, Subject.subject_name)
        .join(Subject, Note.subject_id == Subject.id)
        .order_by(Note.subject_id, Note.uploaded_at.desc())
        .all()
    )


def list_note_rows_for_subject(subject_id: int):
    return (
        db.session.query(Note, Subject.subject_name)
        .join(Subject, Note.subject_id == Subject.id)
        .filter(Note.subject_id == subject_id)
        .order_by(Note.uploaded_at.desc())
        .all()
    )


def create_note(
    subject_id: int,
    title: str,
    file_path: str,
    uploaded_by: str,
    uploaded_at: datetime,
) -> Note:
    note = Note(
        subject_id=subject_id,
        title=title,
        file_path=file_path,
        uploaded_by=uploaded_by,
        uploaded_at=uploaded_at,
    )
    db.session.add(note)
    db.session.commit()
    return note


def get_note(note_id: int) -> Note | None:
    return db.session.get(Note, note_id)


def delete_note(note: Note) -> None:
    db.session.delete(note)
    db.session.commit()


def list_all_attendance_rows():
    return (
        db.session.query(Attendance, Subject.subject_name)
        .join(Subject, Attendance.subject_id == Subject.id)
        .order_by(Attendance.student_email, Subject.subject_name)
        .all()
    )


def get_attendance_record(student_email: str, subject_id: int) -> Attendance | None:
    return (
        db.session.query(Attendance)
        .filter(Attendance.student_email == student_email)
        .filter(Attendance.subject_id == subject_id)
        .first()
    )


def update_attendance_record(
    record: Attendance,
    total_classes: int,
    attended_classes: int,
    last_updated: datetime,
) -> Attendance:
    record.total_classes = total_classes
    record.attended_classes = attended_classes
    record.last_updated = last_updated
    db.session.commit()
    return record


def list_all_mark_rows():
    return (
        db.session.query(Mark, Subject.subject_name)
        .join(Subject, Mark.subject_id == Subject.id)
        .order_by(Mark.student_email, Subject.subject_name)
        .all()
    )


def get_mark_record(student_email: str, subject_id: int) -> Mark | None:
    return (
        db.session.query(Mark)
        .filter(Mark.student_email == student_email)
        .filter(Mark.subject_id == subject_id)
        .first()
    )


def update_mark_record(
    record: Mark,
    internal_marks: int,
    assignment_marks: int,
    exam_marks: int,
    last_updated: datetime,
) -> Mark:
    record.internal_marks = internal_marks
    record.assignment_marks = assignment_marks
    record.exam_marks = exam_marks
    record.last_updated = last_updated
    db.session.commit()
    return record


def list_timetable_rows(ordering: ColumnElement[int]):
    return (
        db.session.query(TimetableSlot, Subject.subject_name)
        .outerjoin(Subject, TimetableSlot.subject_id == Subject.id)
        .order_by(ordering, TimetableSlot.time_slot)
        .all()
    )


def get_timetable_slot(slot_id: int) -> TimetableSlot | None:
    return db.session.get(TimetableSlot, slot_id)


def delete_timetable_slot(slot: TimetableSlot) -> None:
    db.session.delete(slot)
    db.session.commit()


def get_note_by_path(file_path: str) -> Note | None:
    return db.session.query(Note).filter(Note.file_path == file_path).first()


def get_attendance_summary_rows():
    return (
        db.session.query(
            Attendance.student_email,
            db.func.count(Attendance.id),
            db.func.sum(Attendance.attended_classes),
            db.func.sum(Attendance.total_classes),
        )
        .group_by(Attendance.student_email)
        .all()
    )


def get_mark_summary_rows():
    return (
        db.session.query(
            Mark.student_email,
            db.func.avg(Mark.internal_marks + Mark.assignment_marks + Mark.exam_marks),
        )
        .group_by(Mark.student_email)
        .all()
    )