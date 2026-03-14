"""
services/security.py

Database-backed rate limiting and input sanitization utilities.
"""

import html
import re

from academic_governance.services import auth_service


class RateLimiter:
    """Database-backed sliding-window rate limiter keyed by (action, identifier)."""

    def is_allowed(self, action: str, key: str,
                   max_attempts: int = 5, window: int = 60) -> bool:
        auth_service.prune_rate_limit_entries(action, key, window)
        return auth_service.get_rate_limit_count(action, key, window) < max_attempts

    def record(self, action: str, key: str) -> None:
        auth_service.record_rate_limit_attempt(action, key)

    def reset(self, action: str, key: str) -> None:
        auth_service.reset_rate_limit(action, key)

    def remaining(self, action: str, key: str,
                  max_attempts: int = 5, window: int = 60) -> int:
        auth_service.prune_rate_limit_entries(action, key, window)
        used = auth_service.get_rate_limit_count(action, key, window)
        return max(0, max_attempts - used)


rate_limiter = RateLimiter()

_TAG_RE = re.compile(r'<[^>]+>')


def sanitize_text(raw: str, max_length: int = 5000) -> str:
    if not raw:
        return ''
    stripped = _TAG_RE.sub('', raw)
    escaped = html.escape(stripped, quote=True)
    return escaped[:max_length]


def sanitize_url(raw: str, max_length: int = 500) -> str:
    if not raw:
        return ''
    raw = raw.strip()[:max_length]
    if re.match(r'^https?://', raw, re.IGNORECASE):
        return html.escape(raw, quote=True)
    return ''


MIME_MAP = {
    'png':  'image/png',
    'jpg':  'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif':  'image/gif',
    'pdf':  'application/pdf',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'ppt':  'application/vnd.ms-powerpoint',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc':  'application/msword',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt':  'text/plain',
}

OFFICE_MAGIC = {
    'pptx': b'PK',
    'docx': b'PK',
    'xlsx': b'PK',
    'ppt': bytes.fromhex('D0CF11E0A1B11AE1'),
    'doc': bytes.fromhex('D0CF11E0A1B11AE1'),
}


def validate_mime_type(file_storage) -> tuple[bool, str]:
    filename = file_storage.filename or ''
    if '.' not in filename:
        return False, 'File has no extension.'

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in MIME_MAP:
        return False, f'Extension .{ext} is not allowed.'

    file_storage.stream.seek(0)
    header = file_storage.stream.read(261)
    file_storage.stream.seek(0)

    if ext == 'pdf' and not header.startswith(b'%PDF'):
        return False, 'File does not appear to be a valid PDF.'
    if ext == 'png' and not header.startswith(bytes.fromhex('89504E47')):
        return False, 'File does not appear to be a valid PNG.'
    if ext in ('jpg', 'jpeg') and not header.startswith(bytes.fromhex('FFD8FF')):
        return False, 'File does not appear to be a valid JPEG.'
    if ext == 'gif' and not (header.startswith(b'GIF87a') or header.startswith(b'GIF89a')):
        return False, 'File does not appear to be a valid GIF.'
    if ext in OFFICE_MAGIC and not header.startswith(OFFICE_MAGIC[ext]):
        return False, f'File does not appear to be a valid .{ext} document.'
    if ext == 'txt':
        allowed = set(range(32, 127)) | {9, 10, 13}
        if any(byte not in allowed for byte in header[:128]):
            return False, 'File does not appear to be a valid text document.'

    return True, ''
