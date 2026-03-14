"""Academic domain service layer."""

from __future__ import annotations

import csv
import io
import os
import random
import string as _str
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from sqlalchemy import case
from werkzeug.utils import secure_filename

from academic_governance import config
from academic_governance.models import Attendance, Mark, Note, Subject, TimetableSlot
from academic_governance.repositories import academic_repository, user_repository
from academic_governance.services.security import sanitize_text, validate_mime_type


DEFAULT_SUBJECTS = [
    ("Data Structures", 4),
    ("Database Management Systems", 4),
    ("Operating Systems", 4),
    ("Computer Networks", 3),
]

DEFAULT_TIMETABLE = [
    ("Monday", "09:00-10:00", 0, "Room 101", "class"),
    ("Monday", "10:00-11:00", 1, "Room 102", "class"),
    ("Tuesday", "09:00-10:00", 2, "Room 103", "class"),
    ("Tuesday", "11:00-12:00", 3, "Room 104", "class"),
    ("Wednesday", "09:00-10:00", 0, "Room 101", "class"),
    ("Wednesday", "14:00-15:00", 1, "Room 102", "class"),
    ("Thursday", "09:00-10:00", 2, "Room 103", "class"),
    ("Thursday", "11:00-12:00", 3, "Room 104", "class"),
    ("Friday", "09:00-10:00", 0, "Room 101", "class"),
    ("Friday", "10:00-11:00", 2, "Room 103", "class"),
]

NOTE_EXTS = {"pdf", "pptx", "ppt", "docx", "doc", "xlsx", "txt", "png", "jpg", "jpeg"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _attendance_dict(attendance: Attendance, subject_name: str, credits: int) -> dict:
    return {
        "id": attendance.id,
        "student_email": attendance.student_email,
        "subject_id": attendance.subject_id,
        "total_classes": attendance.total_classes,
        "attended_classes": attendance.attended_classes,
        "last_updated": _serialize_dt(attendance.last_updated),
        "subject_name": subject_name,
        "credits": credits,
    }


def _mark_dict(mark: Mark, subject_name: str) -> dict:
    return {
        "id": mark.id,
        "student_email": mark.student_email,
        "subject_id": mark.subject_id,
        "internal_marks": mark.internal_marks,
        "assignment_marks": mark.assignment_marks,
        "exam_marks": mark.exam_marks,
        "last_updated": _serialize_dt(mark.last_updated),
        "subject_name": subject_name,
    }


def _note_dict(note: Note, subject_name: str) -> dict:
    return {
        "id": note.id,
        "subject_id": note.subject_id,
        "title": note.title,
        "file_path": note.file_path,
        "uploaded_by": note.uploaded_by,
        "uploaded_at": _serialize_dt(note.uploaded_at),
        "subject_name": subject_name,
    }


def _ensure_default_subjects() -> list[Subject]:
    subjects = academic_repository.list_subjects()
    if subjects:
        return subjects

    for subject_name, credits in DEFAULT_SUBJECTS:
        academic_repository.create_subject(subject_name, credits)
    academic_repository.commit()
    return academic_repository.list_subjects()


def _ensure_default_timetable(subjects: list[Subject]) -> None:
    if academic_repository.count_timetable_slots() > 0 or not subjects:
        return

    for day, time_slot, subject_index, room, slot_type in DEFAULT_TIMETABLE:
        if subject_index < len(subjects):
            academic_repository.create_timetable_slot(
                day_of_week=day,
                time_slot=time_slot,
                subject_id=subjects[subject_index].id,
                room=room,
                slot_type=slot_type,
            )
    academic_repository.commit()


def get_student_attendance(student_email: str) -> list[dict]:
    rows = academic_repository.list_student_attendance_rows(student_email)
    return [_attendance_dict(attendance, subject_name, credits) for attendance, subject_name, credits in rows]


def get_student_marks(student_email: str) -> list[dict]:
    rows = academic_repository.list_student_mark_rows(student_email)
    return [_mark_dict(mark, subject_name) for mark, subject_name in rows]


def seed_student_academic_data(student_email: str) -> None:
    subjects = _ensure_default_subjects()
    _ensure_default_timetable(subjects)

    existing_subject_ids = academic_repository.get_attendance_subject_ids(student_email)
    enrolled_subject_ids = academic_repository.get_student_subject_ids(student_email)

    for subject in subjects:
        if subject.id not in enrolled_subject_ids:
            academic_repository.add_student_subject(student_email, subject.id)

        if subject.id not in existing_subject_ids:
            academic_repository.add_attendance_record(
                student_email=student_email,
                subject_id=subject.id,
                total_classes=40,
                attended_classes=random.randint(25, 40),
                last_updated=_now(),
            )
            academic_repository.add_mark_record(
                student_email=student_email,
                subject_id=subject.id,
                internal_marks=random.randint(15, 30),
                assignment_marks=random.randint(10, 20),
                exam_marks=random.randint(30, 50),
                last_updated=_now(),
            )

    academic_repository.commit()



def get_student_dashboard_context(student_email: str) -> dict:
    seed_student_academic_data(student_email)
    attendance_records = get_student_attendance(student_email)
    marks_records = get_student_marks(student_email)

    total_attended = sum(record["attended_classes"] for record in attendance_records)
    total_classes = sum(record["total_classes"] for record in attendance_records)
    overall_attendance_pct = round((total_attended / total_classes) * 100, 2) if total_classes else 0.0

    total_marks_across_subjects = 0
    top_subject_name = "N/A"
    highest_marks = -1
    for record in marks_records:
        subject_total = record["internal_marks"] + record["assignment_marks"] + record["exam_marks"]
        total_marks_across_subjects += subject_total
        if subject_total > highest_marks:
            highest_marks = subject_total
            top_subject_name = record["subject_name"]

    avg_marks_pct = round(total_marks_across_subjects / len(marks_records), 2) if marks_records else 0.0
    subjects_below_75 = sum(
        1
        for record in attendance_records
        if record["total_classes"] > 0
        and (record["attended_classes"] / record["total_classes"]) * 100 < 75
    )

    return {
        "has_academic_data": bool(attendance_records or marks_records),
        "overall_attendance_pct": overall_attendance_pct,
        "avg_marks_pct": avg_marks_pct,
        "subjects_below_75": subjects_below_75,
        "top_subject_name": top_subject_name,
        "highest_marks": highest_marks,
        "attendance_records": attendance_records,
        "timetable": get_full_timetable(),
    }


def get_student_progress_context(student_email: str) -> dict:
    attendance_records = get_student_attendance(student_email)
    marks_records = get_student_marks(student_email)

    total_attended = sum(record["attended_classes"] for record in attendance_records)
    total_classes = sum(record["total_classes"] for record in attendance_records)
    overall_attendance_pct = round((total_attended / total_classes) * 100, 2) if total_classes else 0.0

    attendance_by_subject = {record["subject_id"]: record for record in attendance_records}
    progress_data = []
    top_subject = {"name": "N/A", "marks": -1}
    weakest_subject = {"name": "N/A", "marks": 999}

    for record in marks_records:
        attendance = attendance_by_subject.get(record["subject_id"])
        attendance_pct = 0.0
        if attendance and attendance["total_classes"] > 0:
            attendance_pct = round((attendance["attended_classes"] / attendance["total_classes"]) * 100, 1)

        total_marks = record["internal_marks"] + record["assignment_marks"] + record["exam_marks"]
        if total_marks > top_subject["marks"]:
            top_subject = {"name": record["subject_name"], "marks": total_marks}
        if total_marks < weakest_subject["marks"]:
            weakest_subject = {"name": record["subject_name"], "marks": total_marks}

        progress_data.append(
            {
                "subject_id": record["subject_id"],
                "subject_name": record["subject_name"],
                "attendance_pct": attendance_pct,
                "internal": record["internal_marks"],
                "assignment": record["assignment_marks"],
                "exam": record["exam_marks"],
                "total_marks": total_marks,
            }
        )

    if weakest_subject["marks"] == 999:
        weakest_subject["marks"] = 0

    return {
        "overall_attendance_pct": overall_attendance_pct,
        "top_subject": top_subject,
        "weakest_subject": weakest_subject,
        "progress_data": progress_data,
    }


def get_attendance_overview_context(student_email: str) -> dict:
    records = get_student_attendance(student_email)
    total_classes = sum(record["total_classes"] for record in records)
    attended_classes = sum(record["attended_classes"] for record in records)
    overall_pct = round((attended_classes / total_classes) * 100, 1) if total_classes else 0

    labels = [f"BCS-{record['subject_id']}0{index + 1}: {record['subject_name']}" for index, record in enumerate(records)]
    percentages = [
        round((record["attended_classes"] / record["total_classes"]) * 100, 1) if record["total_classes"] else 0
        for record in records
    ]

    return {
        "records": records,
        "overall_pct": overall_pct,
        "labels": labels,
        "percentages": percentages,
    }


def get_student_attendance_record(student_email: str, subject_id: int) -> dict | None:
    return next(
        (record for record in get_student_attendance(student_email) if record["subject_id"] == subject_id),
        None,
    )


def _build_attendance_sessions(total_classes: int, attended_classes: int) -> list[dict]:
    absent_classes = max(0, total_classes - attended_classes)
    statuses = ["Present"] * attended_classes + ["Absent"] * absent_classes
    random.shuffle(statuses)

    current_date = datetime.now() - timedelta(days=90)
    sessions = []
    time_slots = [
        "09:00 AM - 10:00 AM",
        "10:00 AM - 11:00 AM",
        "11:30 AM - 12:30 PM",
        "12:30 PM - 01:30 PM",
        "02:00 PM - 03:00 PM",
    ]

    for index in range(total_classes):
        current_date += timedelta(days=random.randint(1, 3))
        if current_date.weekday() == 6:
            current_date += timedelta(days=1)

        sessions.append(
            {
                "sl_no": index + 1,
                "date": current_date.strftime("%d-%b-%Y"),
                "time": random.choice(time_slots),
                "status": statuses[index],
            }
        )

    return sessions


def get_attendance_detail_context(student_email: str, subject_id: int) -> dict | None:
    attendance_records = get_student_attendance(student_email)
    record_row = next((record for record in attendance_records if record["subject_id"] == subject_id), None)
    if record_row is None:
        return None

    record = dict(record_row)
    if attendance_records and record["subject_id"] == attendance_records[0]["subject_id"]:
        record["attended_classes"] = int(record["total_classes"] * 0.55)

    return {
        "record": record,
        "sessions": _build_attendance_sessions(record["total_classes"], record["attended_classes"]),
    }


def get_marks_overview_context(student_email: str) -> dict:
    records = get_student_marks(student_email)
    labels = [f"BCS-{record['subject_id']}0{index + 1}: {record['subject_name']}" for index, record in enumerate(records)]
    obtained_marks = [record["internal_marks"] + record["assignment_marks"] + record["exam_marks"] for record in records]

    overall_obtained = sum(obtained_marks)
    overall_max = len(records) * 100
    overall_pct = round((overall_obtained / overall_max) * 100, 1) if overall_max else 0

    return {
        "records": records,
        "overall_pct": overall_pct,
        "labels": labels,
        "obtained_marks": obtained_marks,
    }


def get_marks_detail_context(student_email: str, subject_id: int) -> dict | None:
    record = next((row for row in get_student_marks(student_email) if row["subject_id"] == subject_id), None)
    if record is None:
        return None

    max_internal = 30
    max_assignment = 20
    max_exam = 50
    total_max = max_internal + max_assignment + max_exam
    total_obtained = record["internal_marks"] + record["assignment_marks"] + record["exam_marks"]

    return {
        "record": record,
        "max_internal": max_internal,
        "max_assignment": max_assignment,
        "max_exam": max_exam,
        "total_max": total_max,
        "total_obtained": total_obtained,
    }


def _group_records_by(records: list[dict], field_name: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for record in records:
        group_key = record[field_name]
        grouped.setdefault(group_key, []).append(record)
    return grouped


def get_all_attendance_grouped_by_student() -> dict[str, list[dict]]:
    return _group_records_by(get_all_attendance(), "student_email")


def apply_attendance_updates(form_data: Mapping[str, str]) -> int:
    updated = 0
    for key, value in form_data.items():
        if not key.startswith("total_"):
            continue

        parts = key.split("_", 2)
        if len(parts) != 3:
            continue

        _, email, subject_id_raw = parts
        try:
            total = int(value)
            attended = int(form_data.get(f"attended_{email}_{subject_id_raw}", 0))
            subject_id = int(subject_id_raw)
        except (TypeError, ValueError):
            continue

        if total < 0 or attended < 0 or attended > total:
            continue

        update_attendance(email, subject_id, total, attended)
        updated += 1

    return updated


def get_all_marks_grouped_by_student() -> dict[str, list[dict]]:
    return _group_records_by(get_all_marks(), "student_email")


def apply_mark_updates(form_data: Mapping[str, str]) -> int:
    updated = 0
    for key, value in form_data.items():
        if not key.startswith("internal_"):
            continue

        parts = key.split("_", 2)
        if len(parts) != 3:
            continue

        _, email, subject_id_raw = parts
        try:
            internal = max(0, min(30, int(value)))
            assignment = max(0, min(20, int(form_data.get(f"assignment_{email}_{subject_id_raw}", 0))))
            exam = max(0, min(50, int(form_data.get(f"exam_{email}_{subject_id_raw}", 0))))
            subject_id = int(subject_id_raw)
        except (TypeError, ValueError):
            continue

        update_marks(email, subject_id, internal, assignment, exam)
        updated += 1

    return updated


def get_notes_grouped_by_subject() -> dict[str, list[dict]]:
    return _group_records_by(get_all_notes(), "subject_name")


def get_materials_management_context() -> dict:
    return {
        "subjects": get_all_subjects(),
        "notes_by_subject": get_notes_grouped_by_subject(),
    }


def upload_note_from_form(subject_id_raw: str, title_raw: str, file_storage, admin_email: str) -> dict:
    title = sanitize_text(title_raw, max_length=200)

    try:
        subject_id = int(subject_id_raw)
    except (TypeError, ValueError):
        return {"success": False, "flash_category": "danger", "message": "Invalid subject selected."}

    if not title:
        return {"success": False, "flash_category": "danger", "message": "Please provide a title for the material."}

    if file_storage is None or not file_storage.filename:
        return {"success": False, "flash_category": "danger", "message": "Please select a file to upload."}

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in NOTE_EXTS:
        return {
            "success": False,
            "flash_category": "danger",
            "message": f'File type ".{ext}" not allowed. Allowed: {", ".join(sorted(NOTE_EXTS))}',
        }

    mime_valid, mime_error = validate_mime_type(file_storage)
    if not mime_valid:
        return {"success": False, "flash_category": "danger", "message": mime_error}

    notes_dir = os.path.join(config.UPLOAD_FOLDER, "notes")
    os.makedirs(notes_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique = "".join(random.choices(_str.ascii_lowercase + _str.digits, k=6))
    filename = f'{timestamp}_{unique}_{secure_filename(file_storage.filename)}'
    save_path = os.path.join(notes_dir, filename)
    relative_path = f"notes/{filename}"

    try:
        file_storage.save(save_path)
        note_id = add_note(subject_id, title, relative_path, admin_email)
    except Exception:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise

    return {
        "success": True,
        "flash_category": "success",
        "message": f'Material "{title}" uploaded successfully!',
        "title": title,
        "subject_id": subject_id,
        "note_id": note_id,
    }


def remove_note_with_file(note_id: int) -> bool:
    file_path = delete_note(note_id)
    if not file_path:
        return False

    full_path = os.path.join(config.UPLOAD_FOLDER, file_path)
    if os.path.exists(full_path):
        os.remove(full_path)
    return True


def get_timetable_grouped_by_day(valid_days: list[str]) -> dict[str, list[dict]]:
    grouped = {day: [] for day in valid_days}
    for slot in get_full_timetable():
        if slot["day_of_week"] in grouped:
            grouped[slot["day_of_week"]].append(slot)
    return grouped


def get_all_notes() -> list[dict]:
    rows = academic_repository.list_note_rows()
    return [_note_dict(note, subject_name) for note, subject_name in rows]


def get_notes_for_subject(subject_id: int) -> list[dict]:
    rows = academic_repository.list_note_rows_for_subject(subject_id)
    return [_note_dict(note, subject_name) for note, subject_name in rows]


def add_note(subject_id: int, title: str, file_path: str, admin_email: str) -> int:
    note = academic_repository.create_note(subject_id, title, file_path, admin_email, _now())
    return note.id


def delete_note(note_id: int) -> str | None:
    note = academic_repository.get_note(note_id)
    if note is None:
        return None
    file_path = note.file_path
    academic_repository.delete_note(note)
    return file_path


def get_all_subjects() -> list[dict]:
    subjects = academic_repository.list_subjects()
    return [
        {"id": subject.id, "subject_name": subject.subject_name, "credits": subject.credits}
        for subject in subjects
    ]


def get_all_attendance() -> list[dict]:
    rows = academic_repository.list_all_attendance_rows()
    return [
        {
            "id": attendance.id,
            "student_email": attendance.student_email,
            "subject_id": attendance.subject_id,
            "total_classes": attendance.total_classes,
            "attended_classes": attendance.attended_classes,
            "last_updated": _serialize_dt(attendance.last_updated),
            "subject_name": subject_name,
        }
        for attendance, subject_name in rows
    ]


def update_attendance(student_email: str, subject_id: int, total: int, attended: int) -> None:
    row = academic_repository.get_attendance_record(student_email, subject_id)
    if row is not None:
        academic_repository.update_attendance_record(row, total, attended, _now())


def get_all_marks() -> list[dict]:
    rows = academic_repository.list_all_mark_rows()
    return [_mark_dict(mark, subject_name) for mark, subject_name in rows]


def update_marks(student_email: str, subject_id: int, internal: int, assignment: int, exam: int) -> None:
    row = academic_repository.get_mark_record(student_email, subject_id)
    if row is not None:
        academic_repository.update_mark_record(row, internal, assignment, exam, _now())


def get_full_timetable() -> list[dict]:
    ordering = case(
        (TimetableSlot.day_of_week == "Monday", 1),
        (TimetableSlot.day_of_week == "Tuesday", 2),
        (TimetableSlot.day_of_week == "Wednesday", 3),
        (TimetableSlot.day_of_week == "Thursday", 4),
        (TimetableSlot.day_of_week == "Friday", 5),
        (TimetableSlot.day_of_week == "Saturday", 6),
        else_=7,
    )
    rows = academic_repository.list_timetable_rows(ordering)
    return [
        {
            "id": slot.id,
            "day_of_week": slot.day_of_week,
            "time_slot": slot.time_slot,
            "room": slot.room,
            "slot_type": slot.slot_type,
            "subject_name": subject_name or "Break",
            "subject_id": slot.subject_id,
        }
        for slot, subject_name in rows
    ]


def add_timetable_slot_from_form(form_data: Mapping[str, str], valid_days: list[str]) -> dict:
    day = sanitize_text(form_data.get("day_of_week", ""), max_length=20)
    time_slot = sanitize_text(form_data.get("time_slot", ""), max_length=30)
    room = sanitize_text(form_data.get("room", "TBA"), max_length=50)
    subject_id_raw = form_data.get("subject_id", "")

    if day not in valid_days:
        return {"success": False, "flash_category": "danger", "message": "Invalid day selected."}
    if not time_slot:
        return {"success": False, "flash_category": "danger", "message": "Time slot cannot be empty."}

    try:
        subject_id = int(subject_id_raw)
    except (TypeError, ValueError):
        return {"success": False, "flash_category": "danger", "message": "Invalid subject selected."}

    add_timetable_slot(day, time_slot, subject_id, room or "TBA")
    return {
        "success": True,
        "flash_category": "success",
        "message": "Timetable slot added.",
        "day": day,
        "time_slot": time_slot,
    }


def add_timetable_slot(
    day: str,
    time_slot: str,
    subject_id: int,
    room: str,
    slot_type: str = "class",
) -> None:
    academic_repository.create_timetable_slot(day, time_slot, subject_id, room, slot_type)
    academic_repository.commit()


def delete_timetable_slot(slot_id: int) -> None:
    slot = academic_repository.get_timetable_slot(slot_id)
    if slot is not None:
        academic_repository.delete_timetable_slot(slot)


def bulk_create_users(rows: list[tuple[str, str]]) -> dict[str, int]:
    created = 0
    skipped = 0
    existing_emails = user_repository.list_user_emails()
    for email, role in rows:
        if email in existing_emails:
            skipped += 1
            continue
        user_repository.create_user(email=email, role=role, created_at=_now(), commit=False)
        existing_emails.add(email)
        created += 1
    user_repository.commit()
    return {"created": created, "skipped": skipped}


def bulk_create_users_from_csv(file_storage) -> dict:
    if file_storage is None or not file_storage.filename:
        return {"success": False, "flash_category": "danger", "message": "Please upload a CSV file."}
    if not file_storage.filename.lower().endswith(".csv"):
        return {"success": False, "flash_category": "danger", "message": "Only .csv files are accepted."}

    try:
        stream = io.StringIO(file_storage.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)

        if not reader.fieldnames or "email" not in reader.fieldnames:
            return {
                "success": False,
                "flash_category": "danger",
                "message": 'CSV must have an "email" column header.',
            }

        valid_roles = {"student", "admin"}
        rows_to_insert: list[tuple[str, str]] = []
        errors: list[str] = []

        for index, row in enumerate(reader, start=2):
            email = sanitize_text((row.get("email") or "").strip().lower(), max_length=254)
            role = sanitize_text((row.get("role") or "student").strip().lower(), max_length=20)

            if not email or "@" not in email or "." not in email.split("@")[-1]:
                errors.append(f'Row {index}: invalid email "{email}"')
                continue
            if role not in valid_roles:
                errors.append(f'Row {index}: invalid role "{role}" (must be student or admin)')
                continue

            rows_to_insert.append((email, role))
    except UnicodeDecodeError:
        return {
            "success": False,
            "flash_category": "danger",
            "message": "CSV must be UTF-8 encoded.",
        }
    except Exception as exc:
        return {
            "success": False,
            "flash_category": "danger",
            "message": f"Error processing CSV: {exc}",
        }

    if not rows_to_insert:
        preview = "; ".join(errors[:3])
        message = "No valid rows found in CSV."
        if preview:
            message = f"{message} {preview}"
        return {"success": False, "flash_category": "danger", "message": message}

    result = bulk_create_users(rows_to_insert)
    message = f'{result["created"]} account(s) created, {result["skipped"]} skipped (duplicates).'
    if errors:
        message += f' {len(errors)} row(s) had errors and were skipped.'

    return {
        "success": True,
        "flash_category": "success" if result["created"] > 0 else "warning",
        "message": message,
        "created": result["created"],
        "skipped": result["skipped"],
        "error_count": len(errors),
    }


def get_note_by_path(file_path: str):
    note = academic_repository.get_note_by_path(file_path)
    if note is None:
        return None
    return {
        "id": note.id,
        "subject_id": note.subject_id,
        "title": note.title,
        "file_path": note.file_path,
        "uploaded_by": note.uploaded_by,
        "uploaded_at": _serialize_dt(note.uploaded_at),
    }


def get_academic_summary_all_students() -> list[dict]:
    attendance_rows = academic_repository.get_attendance_summary_rows()
    mark_rows = academic_repository.get_mark_summary_rows()
    mark_map = {email: round(avg or 0, 1) for email, avg in mark_rows}
    summary = []
    for email, num_subjects, total_attended, total_classes in attendance_rows:
        total_classes = total_classes or 0
        attendance_pct = round((total_attended / total_classes) * 100, 1) if total_classes > 0 else 0.0
        summary.append(
            {
                "email": email,
                "avg_attendance_pct": attendance_pct,
                "avg_marks_total": mark_map.get(email, 0.0),
                "num_subjects": num_subjects,
            }
        )
    summary.sort(key=lambda item: item["avg_attendance_pct"])
    return summary