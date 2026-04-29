"""Chatbot support built on the PostgreSQL-backed service layer."""

from __future__ import annotations

import logging

import requests

from academic_governance.repositories import complaint_repository
from academic_governance.services import academic_service

logger = logging.getLogger(__name__)


def build_student_context(student_email: str) -> str:
    profile_lines = [f"Email: {student_email}"]

    attendance_rows = academic_service.get_student_attendance(student_email)
    attendance_lines = []
    low_attendance_subjects = []

    for row in attendance_rows:
        total = row["total_classes"]
        attended = row["attended_classes"]
        pct = round((attended * 100.0 / total), 1) if total else 0
        if pct >= 75:
            status = "Safe"
        elif pct >= 65:
            status = "At Risk"
        else:
            status = "Critical"

        attendance_lines.append(
            f"  - {row['subject_name']}: {pct}% ({attended}/{total} classes) [{status}]"
        )

        if pct < 75 and total > 0:
            needed = max(0, int((0.75 * total - attended) / 0.25) + 1)
            low_attendance_subjects.append(
                f"{row['subject_name']} ({pct}% - needs {needed} more consecutive classes to reach 75%)"
            )

    marks_rows = academic_service.get_student_marks(student_email)
    marks_lines = []
    weak_subjects = []

    for row in marks_rows:
        internal = row["internal_marks"] or 0
        assignment = row["assignment_marks"] or 0
        total_internal = internal + assignment
        pct = round((total_internal / 50.0) * 100, 1)

        if pct >= 60:
            flag = "Healthy"
        elif pct >= 40:
            flag = "Watch"
        else:
            flag = "Weak"

        marks_lines.append(
            f"  - {row['subject_name']}: Internal {internal}/30, "
            f"Assignments {assignment}/20 -> Total: {total_internal}/50 ({pct}%) [{flag}]"
        )
        if pct < 50:
            weak_subjects.append(row["subject_name"])

    grievances = complaint_repository.list_student_grievances(student_email, limit=5)

    grievance_lines = []
    for grievance in grievances:
        created_date = (
            grievance.created_at.strftime("%Y-%m-%d")
            if grievance.created_at is not None
            else "Unknown Date"
        )
        grievance_lines.append(
            f"  - [{grievance.status.upper()}] {grievance.category} (Filed: {created_date})"
        )

    if not grievance_lines:
        grievance_lines = ["  No grievances filed."]

    return f"""
You are ARIA (Academic Resource & Intelligence Assistant), a friendly academic advisor embedded inside a student portal.
You only answer questions based on the student data provided below.
Be concise, warm, and always give actionable advice. Use bullet points for lists.
Never make up data. If something is missing, say "I don't have that info right now."

========================================
STUDENT PROFILE
========================================
{chr(10).join(profile_lines)}

========================================
ATTENDANCE STATUS
========================================
{chr(10).join(attendance_lines) if attendance_lines else "  No attendance data found."}

Subjects below 75% attendance:
{chr(10).join(f"  - {subject}" for subject in low_attendance_subjects) if low_attendance_subjects else "  None - all subjects are safe."}

========================================
MARKS AND PERFORMANCE
========================================
{chr(10).join(marks_lines) if marks_lines else "  No marks data found."}

Weak subjects (below 50% internal):
{chr(10).join(f"  - {subject}" for subject in weak_subjects) if weak_subjects else "  None - performance looks good."}

========================================
RECENT GRIEVANCES
========================================
{chr(10).join(grievance_lines)}
""".strip()


def ask_ai(context: str, user_message: str) -> str:
    from academic_governance import config

    api_key = config.AI_API_KEY
    if not api_key:
        return (
            "Chatbot is not configured. Please add AI_API_KEY to your environment."
        )

    # Standard OpenAI Chat Completions endpoint structure
    base_url = config.AI_BASE_URL.rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": config.AI_MODEL,
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Academic Governance System"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "The AI took too long to respond. Please try again."
    except requests.exceptions.RequestException as exc:
        logger.warning("AI request failed: %s", exc)
        if getattr(exc, "response", None) is not None:
            logger.warning("AI response status: %s", exc.response.status_code)
            logger.warning("AI response body: %s", exc.response.text)
        return "Connection error. Please verify your API key and try again."
    except (KeyError, IndexError, TypeError):
        return "Unexpected response from AI. Please try again."
