import re
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


WORKSPACE_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".tmp_test_artifacts"


def extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None, "CSRF token not found in form response."
    return match.group(1)


def login_as(client, email: str, role: str) -> None:
    with client.session_transaction() as session_data:
        session_data["user_email"] = email
        session_data["role"] = role
        session_data["login_time"] = "2026-01-01 00:00:00"


@contextmanager
def managed_temp_dir(prefix: str):
    WORKSPACE_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    temp_dir = WORKSPACE_TEMP_ROOT / f"{prefix}{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)