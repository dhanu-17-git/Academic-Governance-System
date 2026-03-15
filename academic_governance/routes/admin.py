"""
routes/admin.py – Blueprint for admin-only routes.

Phase 4 hardening + Academic & Lab Resource extensions:
  - admin_required returns 403, not redirect, for logged-in non-admins
  - All status updates go through the complaint service
  - All admin actions logged to audit_log
  - Input sanitized via security.sanitize_text
  - Academic workflows delegated to the service layer
  - Lab resource management (add/update/delete PC systems) managed here
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)

from academic_governance import config
from academic_governance.services import academic_service
from academic_governance.services import complaint_service
from academic_governance.services import lab_service
from academic_governance.services import notification_service
from academic_governance.services.security import sanitize_text
from academic_governance.services.validators import sanitize_complaint_id

admin_bp = Blueprint("admin", __name__)

CATEGORIES = [
    "Academic",
    "Cleaning",
    "Parking",
    "Placement",
    "Infrastructure",
    "Ragging",
]

VALID_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _admin_required():
    """
    Return a response if the user cannot access admin routes:
      - Not logged in  → redirect to login
      - Logged in but not admin → 403 Forbidden
    Returns None if access is allowed.
    """
    if "user_email" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))
    if session.get("role") != config.ROLE_ADMIN:
        abort(403)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main Admin Dashboard
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin")
def admin_dashboard():
    guard = _admin_required()
    if guard:
        return guard

    dashboard_context = complaint_service.get_admin_dashboard_context(CATEGORIES)
    lab_summary = lab_service.get_lab_summary()

    return render_template(
        "admin_dashboard.html", lab_summary=lab_summary, **dashboard_context
    )


@admin_bp.route("/admin/update-status/<complaint_id>", methods=["POST"])
def update_status(complaint_id):
    guard = _admin_required()
    if guard:
        return guard

    new_status = sanitize_text(request.form.get("status", ""), max_length=50)
    admin_response = sanitize_text(
        request.form.get("admin_response", ""), max_length=2000
    )

    clean_id = sanitize_complaint_id(complaint_id)
    if not clean_id:
        flash("Invalid complaint ID.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    success, err = complaint_service.update_complaint_status(
        clean_id, new_status, admin_response
    )
    if not success:
        flash(f"Status update failed: {err}", "danger")
    else:
        admin_email = session["user_email"]
        complaint_service.log_admin_action(
            admin_email,
            f'Updated complaint {clean_id} → "{new_status}"'
            + (f" | Response: {admin_response[:80]}" if admin_response else ""),
        )
        flash("Complaint status updated!", "success")

    return redirect(url_for("admin.admin_dashboard"))


# ─────────────────────────────────────────────────────────────────────────────
# Academic: Attendance Management
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/academic/attendance", methods=["GET", "POST"])
def manage_attendance():
    guard = _admin_required()
    if guard:
        return guard

    if request.method == "POST":
        updated = academic_service.apply_attendance_updates(request.form)
        complaint_service.log_admin_action(
            session["user_email"], f"Updated attendance for {updated} records"
        )
        flash(f"Attendance updated for {updated} record(s).", "success")
        return redirect(url_for("admin.manage_attendance"))

    students = academic_service.get_all_attendance_grouped_by_student()
    return render_template("admin_attendance.html", students=students)


@admin_bp.route("/admin/academic/marks", methods=["GET", "POST"])
def manage_marks():
    guard = _admin_required()
    if guard:
        return guard

    if request.method == "POST":
        updated = academic_service.apply_mark_updates(request.form)
        complaint_service.log_admin_action(
            session["user_email"], f"Updated marks for {updated} records"
        )
        flash(f"Marks updated for {updated} record(s).", "success")
        return redirect(url_for("admin.manage_marks"))

    students = academic_service.get_all_marks_grouped_by_student()
    return render_template("admin_marks.html", students=students)


@admin_bp.route("/admin/academic/materials", methods=["GET", "POST"])
def manage_materials():
    guard = _admin_required()
    if guard:
        return guard

    if request.method == "POST":
        result = academic_service.upload_note_from_form(
            request.form.get("subject_id", ""),
            request.form.get("title", ""),
            request.files.get("file"),
            session["user_email"],
        )
        if result["success"]:
            complaint_service.log_admin_action(
                session["user_email"],
                f'Uploaded note "{result["title"]}" for subject {result["subject_id"]}',
            )
        flash(result["message"], result["flash_category"])
        return redirect(url_for("admin.manage_materials"))

    context = academic_service.get_materials_management_context()
    return render_template("admin_materials.html", **context)


@admin_bp.route("/admin/academic/materials/delete/<int:note_id>", methods=["POST"])
def delete_material(note_id):
    guard = _admin_required()
    if guard:
        return guard

    if academic_service.remove_note_with_file(note_id):
        complaint_service.log_admin_action(
            session["user_email"], f"Deleted note id={note_id}"
        )
        flash("Material deleted.", "success")
    else:
        flash("Material not found.", "danger")

    return redirect(url_for("admin.manage_materials"))


# ─────────────────────────────────────────────────────────────────────────────
# Academic: Timetable Management
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/academic/timetable", methods=["GET", "POST"])
def manage_timetable():
    guard = _admin_required()
    if guard:
        return guard

    subjects = academic_service.get_all_subjects()

    if request.method == "POST":
        result = academic_service.add_timetable_slot_from_form(request.form, VALID_DAYS)
        if result["success"]:
            complaint_service.log_admin_action(
                session["user_email"],
                f"Added timetable slot: {result['day']} {result['time_slot']}",
            )
        flash(result["message"], result["flash_category"])
        return redirect(url_for("admin.manage_timetable"))

    timetable_by_day = academic_service.get_timetable_grouped_by_day(VALID_DAYS)
    return render_template(
        "admin_timetable.html",
        subjects=subjects,
        timetable_by_day=timetable_by_day,
        valid_days=VALID_DAYS,
    )


@admin_bp.route("/admin/academic/timetable/delete/<int:slot_id>", methods=["POST"])
def delete_timetable_slot(slot_id):
    guard = _admin_required()
    if guard:
        return guard

    academic_service.delete_timetable_slot(slot_id)
    complaint_service.log_admin_action(
        session["user_email"], f"Deleted timetable slot id={slot_id}"
    )
    flash("Timetable slot deleted.", "success")
    return redirect(url_for("admin.manage_timetable"))


# ─────────────────────────────────────────────────────────────────────────────
# Lab Resource Management
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/labs")
def admin_labs_index():
    guard = _admin_required()
    if guard:
        return guard

    labs = lab_service.get_labs()
    lab_summary = lab_service.get_lab_summary()

    return render_template("admin_labs_index.html", labs=labs, lab_summary=lab_summary)


@admin_bp.route("/admin/labs/<int:lab_id>")
def admin_labs_layout(lab_id):
    guard = _admin_required()
    if guard:
        return guard

    layout_data = lab_service.get_lab_layout(lab_id)
    if not layout_data:
        flash("Lab not found.", "danger")
        return redirect(url_for("admin.admin_labs_index"))

    return render_template("admin_labs_layout.html", layout_data=layout_data)


@admin_bp.route("/admin/labs/update/<int:system_id>", methods=["POST"])
def update_lab_status(system_id):
    guard = _admin_required()
    if guard:
        return guard

    new_status = request.form.get("status", "")
    success, err = lab_service.update_lab_status(system_id, new_status)
    if success:
        complaint_service.log_admin_action(
            session["user_email"], f"Updated lab system id={system_id} → {new_status}"
        )
        # We don't have the lab_id here easily without another DB query,
        # but flash success and redirect back to the submitting page
    else:
        flash(err, "danger")

    # Return to the previous page where the POST came from
    return redirect(request.referrer or url_for("admin.admin_labs_index"))


# ─────────────────────────────────────────────────────────────────────────────
# AG-02: Admin Notifications Push
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/notifications", methods=["GET", "POST"])
def admin_notifications():
    guard = _admin_required()
    if guard:
        return guard

    if request.method == "POST":
        result = notification_service.create_notification_from_form(
            request.form.get("title", ""),
            request.form.get("message", ""),
            request.form.get("link", ""),
        )
        if result["success"]:
            complaint_service.log_admin_action(
                session["user_email"], f'Pushed notification: "{result["title"]}"'
            )
        flash(result["message"], result["flash_category"])
        return redirect(url_for("admin.admin_notifications"))

    notifications = notification_service.get_notifications(limit=20)
    return render_template("admin_notifications.html", notifications=notifications)


# ─────────────────────────────────────────────────────────────────────────────
# AG-03: Admin Bulk CSV Student Account Creation
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/students/create", methods=["GET", "POST"])
def bulk_create_students():
    guard = _admin_required()
    if guard:
        return guard

    if request.method == "POST":
        result = academic_service.bulk_create_users_from_csv(
            request.files.get("csv_file")
        )
        if result["success"]:
            complaint_service.log_admin_action(
                session["user_email"],
                f"Bulk created users: {result['created']} created, {result['skipped']} skipped",
            )
        flash(result["message"], result["flash_category"])
        return redirect(url_for("admin.bulk_create_students"))

    return render_template("admin_create_students.html")


# ─────────────────────────────────────────────────────────────────────────────
# AG-05: Admin At-Risk Student Summary
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route("/admin/at-risk")
def at_risk_students():
    guard = _admin_required()
    if guard:
        return guard

    summary = academic_service.get_academic_summary_all_students()
    return render_template("admin_at_risk.html", summary=summary)
