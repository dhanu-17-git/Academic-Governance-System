"""
services/validators.py

Centralised validation helpers.
All route handlers must call these functions rather than
performing validation inline.
"""

import re
from academic_governance import config


# ─────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────
def validate_email(email: str) -> tuple[bool, str]:
    """
    Accept only @college.edu addresses.
    Returns (is_valid: bool, error_message: str).
    """
    if not email or not isinstance(email, str):
        return False, 'Email address is required.'
    email = email.strip().lower()
    if not email.endswith('@college.edu'):
        return False, 'Please use a valid college email (@college.edu).'
    if len(email) > 50:
        return False, 'Email is too long.'
    # basic format check
    pattern = r'^[a-zA-Z0-9._%+\-]+@college\.edu$'
    if not re.match(pattern, email):
        return False, 'Email format is invalid.'
    return True, ''


# ─────────────────────────────────────────────
# Complaint
# ─────────────────────────────────────────────
VALID_CATEGORIES = {
    'Academic', 'Cleaning', 'Parking',
    'Placement', 'Infrastructure', 'Ragging',
}

def validate_complaint_input(category: str, description: str) -> tuple[bool, str]:
    """
    Validate complaint form fields.
    Returns (is_valid: bool, error_message: str).
    """
    if not category or category not in VALID_CATEGORIES:
        return False, 'Please select a valid complaint category.'
    if not description or not description.strip():
        return False, 'Complaint description is required.'
    if len(description.strip()) < 20:
        return False, 'Description must be at least 20 characters.'
    if len(description) > 2000:
        return False, 'Description must not exceed 2000 characters.'
    return True, ''


# ─────────────────────────────────────────────
# Feedback
# ─────────────────────────────────────────────
def validate_feedback_input(subject: str, rating) -> tuple[bool, str]:
    """
    Validate feedback form fields.
    Returns (is_valid: bool, error_message: str).
    """
    if not subject or not subject.strip():
        return False, 'Feedback subject is required.'
    if len(subject.strip()) > 200:
        return False, 'Subject must not exceed 200 characters.'
    try:
        rating_int = int(rating)
    except (TypeError, ValueError):
        return False, 'Rating must be a number between 1 and 5.'
    if rating_int not in range(1, 6):
        return False, 'Rating must be between 1 and 5.'
    return True, ''


# ─────────────────────────────────────────────
# File upload
# ─────────────────────────────────────────────
def validate_file_extension(filename: str) -> tuple[bool, str]:
    """
    Check that the file extension is in the allowed set.
    Returns (is_valid: bool, error_message: str).
    """
    if not filename or '.' not in filename:
        return False, 'File has no extension.'
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(config.ALLOWED_EXTENSIONS))
        return False, f'File type not allowed. Allowed types: {allowed}.'
    return True, ''


# ─────────────────────────────────────────────
# Complaint ID
# ─────────────────────────────────────────────
def sanitize_complaint_id(raw: str) -> str:
    """
    Strip non-alphanumeric characters, uppercase, cap at 20 chars.
    Returns empty string if input is None / empty.
    """
    if not raw:
        return ''
    return re.sub(r'[^A-Za-z0-9]', '', raw)[:20].upper()
