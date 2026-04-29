"""
routes/student.py ΓÇô Blueprint for student-facing routes.

Phase 4 hardening:
  - student_required returns 403 for logged-in non-students
  - Rate limiting on complaint and feedback submissions
  - All user text inputs sanitized via sanitize_text()
  - MIME-type validation on file uploads
  - Unique per-complaint upload subfolder
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
from academic_governance.services.validators import (
    validate_complaint_input,
    validate_feedback_input,
    validate_file_extension,
    sanitize_complaint_id,
)
from academic_governance.services.security import (
    sanitize_text,
    sanitize_url,
    validate_mime_type,
    rate_limiter,
)

student_bp = Blueprint("student", __name__)


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Access-control guard
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def _student_required():
    if "user_email" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login") + "?guard=2")
    if session.get("role") != config.ROLE_STUDENT:
        abort(403)
    return None


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Routes
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
@student_bp.route("/dashboard")
def dashboard():
    guard = _student_required()
    if guard:
        return guard

    email = session["user_email"]
    updates = complaint_service.get_campus_updates()
    stats = complaint_service.get_student_complaints(email)
    academic_context = academic_service.get_student_dashboard_context(email)
    lab_summary = lab_service.get_lab_summary()

    return render_template(
        "dashboard.html",
        updates=updates,
        total_complaints=stats["total"],
        pending_complaints=stats["pending"],
        resolved_complaints=stats["resolved"],
        lab_working=lab_summary["working"],
        lab_broken=lab_summary["not_working"],
        **academic_context,
    )


@student_bp.route("/progress")
def student_progress():
    guard = _student_required()
    if guard:
        return guard

    context = academic_service.get_student_progress_context(session["user_email"])
    return render_template("student_progress.html", **context)


@student_bp.route("/attendance")
def attendance_overview():
    guard = _student_required()
    if guard:
        return guard

    context = academic_service.get_attendance_overview_context(session["user_email"])
    return render_template("attendance_overview.html", **context)


@student_bp.route("/attendance/<int:subject_id>")
def attendance_details(subject_id):
    guard = _student_required()
    if guard:
        return guard

    context = academic_service.get_attendance_detail_context(
        session["user_email"], subject_id
    )
    if context is None:
        flash("Attendance record not found for this subject.", "danger")
        return redirect(url_for("student.dashboard"))

    return render_template("attendance_module.html", **context)


@student_bp.route("/marks")
def marks_overview():
    guard = _student_required()
    if guard:
        return guard

    context = academic_service.get_marks_overview_context(session["user_email"])
    return render_template("marks_overview.html", **context)


@student_bp.route("/marks/<int:subject_id>")
def marks_details(subject_id):
    guard = _student_required()
    if guard:
        return guard

    context = academic_service.get_marks_detail_context(
        session["user_email"], subject_id
    )
    if context is None:
        flash("Marks record not found for this subject.", "danger")
        return redirect(url_for("student.dashboard"))

    return render_template("marks_module.html", **context)


@student_bp.route("/course-plan")
def course_plan_overview():
    guard = _student_required()
    if guard:
        return guard

    email = session["user_email"]
    # Use attendance records simply to fetch the list of registered subjects
    attendance_records = academic_service.get_student_attendance(email)

    return render_template("course_plan_overview.html", records=attendance_records)


@student_bp.route("/course-plan/<int:subject_id>")
def course_plan_details(subject_id):
    guard = _student_required()
    if guard:
        return guard

    record = academic_service.get_student_attendance_record(
        session["user_email"], subject_id
    )
    if not record:
        flash("Subject record not found.", "danger")
        return redirect(url_for("student.dashboard"))

    return render_template("course_plan_module.html", record=record)


@student_bp.route("/course-plan/<int:subject_id>/materials")
def course_plan_materials(subject_id):
    guard = _student_required()
    if guard:
        return guard

    record = academic_service.get_student_attendance_record(
        session["user_email"], subject_id
    )
    if not record:
        flash("Subject record not found.", "danger")
        return redirect(url_for("student.dashboard"))

    notes = academic_service.get_notes_for_subject(subject_id)
    return render_template("course_materials.html", record=record, notes=notes)


@student_bp.route("/raise-complaint", methods=["GET", "POST"])
def raise_complaint():
    guard = _student_required()
    if guard:
        return guard

    if request.method == "POST":
        email = session["user_email"]

        # Rate-limit complaint submissions per student
        if not rate_limiter.is_allowed(
            "complaint", email, config.RATE_COMPLAINT_MAX, config.RATE_COMPLAINT_WIN
        ):
            flash(
                "You have submitted too many complaints recently. Please try again later.",
                "danger",
            )
            return render_template("raise_complaint.html")

        # Sanitize & validate
        category = sanitize_text(request.form.get("category", ""), max_length=50)
        description = sanitize_text(
            request.form.get("description", ""), max_length=2000
        )
        url_ref = sanitize_url(request.form.get("url", ""))

        valid, err = validate_complaint_input(category, description)
        if not valid:
            flash(err, "danger")
            return render_template("raise_complaint.html")

        # File upload ΓÇô hardened
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                # Extension check
                fvalid, ferr = validate_file_extension(file.filename)
                if not fvalid:
                    flash(ferr, "danger")
                    return render_template("raise_complaint.html")

                # MIME magic-byte check
                mvalid, merr = validate_mime_type(file)
                if not mvalid:
                    flash(merr, "danger")
                    return render_template("raise_complaint.html")

                complaint_id = complaint_service.create_complaint_with_upload(
                    category=category,
                    description=description,
                    student_email=email,
                    file_storage=file,
                    url=url_ref,
                )
            else:
                complaint_id = complaint_service.create_complaint(
                    category=category,
                    description=description,
                    student_email=email,
                    url=url_ref,
                )
        else:
            complaint_id = complaint_service.create_complaint(
                category=category,
                description=description,
                student_email=email,
                url=url_ref,
            )

        rate_limiter.record("complaint", email)
        flash("Complaint submitted successfully!", "success")
        return redirect(
            url_for("student.complaint_confirmation", complaint_id=complaint_id)
        )

    return render_template("raise_complaint.html")


@student_bp.route("/complaint-confirmation/<complaint_id>")
def complaint_confirmation(complaint_id):
    guard = _student_required()
    if guard:
        return guard

    clean_id = sanitize_complaint_id(complaint_id)
    if not clean_id:
        flash("Invalid complaint ID.", "danger")
        return redirect(url_for("student.dashboard"))
    return render_template("complaint_confirmation.html", complaint_id=clean_id)


@student_bp.route("/track-complaint", methods=["GET", "POST"])
def track_complaint():
    guard = _student_required()
    if guard:
        return guard

    complaint = None

    if request.method == "POST":
        raw_id = request.form.get("complaint_id", "")
        complaint_id = sanitize_complaint_id(raw_id)

        if not complaint_id:
            flash("Please enter a valid Complaint ID.", "warning")
        else:
            complaint = complaint_service.get_complaint_by_id(complaint_id)
            if not complaint:
                flash("Complaint ID not found. Please check and try again.", "warning")
            elif complaint.get("student_email") != session["user_email"]:
                flash("Complaint ID not found. Please check and try again.", "warning")
                complaint = None

    return render_template("track_complaint.html", complaint=complaint)


@student_bp.route("/academic-feedback", methods=["GET", "POST"])
def academic_feedback():
    guard = _student_required()
    if guard:
        return guard

    if request.method == "POST":
        email = session["user_email"]

        # Rate-limit feedback submissions per student
        if not rate_limiter.is_allowed(
            "feedback", email, config.RATE_FEEDBACK_MAX, config.RATE_FEEDBACK_WIN
        ):
            flash(
                "You have submitted too much feedback recently. Please try again later.",
                "danger",
            )
            return render_template("academic_feedback.html")

        subject = sanitize_text(request.form.get("subject", ""), max_length=200)
        comment = sanitize_text(request.form.get("comment", ""), max_length=2000)
        rating = request.form.get("rating", 0)

        valid, err = validate_feedback_input(subject, rating)
        if not valid:
            flash(err, "danger")
            return render_template("academic_feedback.html")

        sentiment = complaint_service.analyze_sentiment(comment)
        complaint_service.create_feedback(subject, int(rating), comment, sentiment)
        rate_limiter.record("feedback", email)

        flash("Thank you for your feedback!", "success")
        return redirect(url_for("student.feedback_success"))

    return render_template("academic_feedback.html")


@student_bp.route("/feedback-success")
def feedback_success():
    guard = _student_required()
    if guard:
        return guard
    return render_template("feedback_success.html")


# ---------------------------------------------------------
# Placement Portal Routes
# ---------------------------------------------------------


@student_bp.route("/placement")
def placement_index():
    guard = _student_required()
    if guard:
        return guard
    return redirect(url_for("student.placement_profile"))


@student_bp.route("/placement/profile")
def placement_profile():
    guard = _student_required()
    if guard:
        return guard
    return render_template("placement_profile.html", active_page="profile")


@student_bp.route("/placement/drives")
def placement_drives():
    guard = _student_required()
    if guard:
        return guard
    return render_template("placement_drives.html", active_page="drives")


@student_bp.route("/placement/applications")
def placement_applications():
    guard = _student_required()
    if guard:
        return guard
    return render_template("placement_applications.html", active_page="applications")


@student_bp.route("/placement/career")
def placement_career():
    guard = _student_required()
    if guard:
        return guard
    return render_template("placement_career.html", active_page="career")


# ---------------------------------------------------------
# New Features: Lab Status, Course Plan
# ---------------------------------------------------------


@student_bp.route("/labs")
def lab_index():
    guard = _student_required()
    if guard:
        return guard

    # Render the new standalone React Lab Module
    return render_template("student_labs_index.html")


@student_bp.route("/labs/<int:lab_id>")
def lab_layout(lab_id):
    guard = _student_required()
    if guard:
        return guard

    layout_data = lab_service.get_lab_layout(lab_id)
    if not layout_data:
        flash("Lab not found.", "danger")
        return redirect(url_for("student.lab_index"))

    return render_template("student_labs_layout.html", layout_data=layout_data)


# ─────────────────────────────────────────────────────────────────────────────
# AG-02: Student Notifications Page
# ─────────────────────────────────────────────────────────────────────────────
@student_bp.route("/notifications")
def student_notifications():
    guard = _student_required()
    if guard:
        return guard

    notifications = notification_service.get_notifications(limit=50)
    return render_template("student_notifications.html", notifications=notifications)
