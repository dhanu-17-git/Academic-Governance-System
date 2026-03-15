"""Centralized configuration for the Academic Governance System."""

import os
import secrets

from dotenv import load_dotenv


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
BASE_DIR = ROOT_DIR

load_dotenv(os.path.join(ROOT_DIR, ".env"))
load_dotenv(os.path.join(ROOT_DIR, ".env.local"), override=True)


def _database_uri() -> str:
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
    if not uri:
        raise RuntimeError(
            "Set DATABASE_URL or SQLALCHEMY_DATABASE_URI to a PostgreSQL connection string."
        )
    if not uri.startswith("postgresql"):
        raise RuntimeError(
            "Only PostgreSQL is supported. Configure a PostgreSQL DATABASE_URL or "
            "SQLALCHEMY_DATABASE_URI."
        )
    return uri


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_EMAILS = [email.lower() for email in ["admin@college.edu"]]

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(ROOT_DIR, "uploads"))
    MAX_FILE_SIZE = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

    ROLE_STUDENT = "student"
    ROLE_ADMIN = "admin"
    VALID_STATUSES = ("Submitted", "Under Review", "Resolved")
    STATUS_TRANSITIONS: dict[str, set] = {
        "Submitted": {"Under Review"},
        "Under Review": {"Resolved"},
        "Resolved": set(),
    }

    SESSION_PERMANENT = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    RATE_LOGIN_MAX = 5
    RATE_LOGIN_WINDOW = 60
    RATE_OTP_MAX = 5
    RATE_OTP_WINDOW = 300
    RATE_COMPLAINT_MAX = 10
    RATE_COMPLAINT_WIN = 3600
    RATE_FEEDBACK_MAX = 5
    RATE_FEEDBACK_WIN = 3600

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "10"))
    EMAIL_USER = os.environ.get("EMAIL_USER", "").strip()
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "").strip()

    HOST = os.environ.get("AGS_HOST", "127.0.0.1")
    PORT = int(os.environ.get("AGS_PORT", "5000"))


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = Config.SECRET_KEY or secrets.token_hex(32)


class StagingConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


env = os.environ.get("FLASK_ENV", "development").strip().lower()
if env == "production":
    active_config = ProductionConfig
elif env == "staging":
    active_config = StagingConfig
else:
    active_config = DevelopmentConfig

if env in {"production", "staging"} and not active_config.SECRET_KEY:
    raise RuntimeError(f"SECRET_KEY not set in {env}")


ENVIRONMENT = env
SECRET_KEY = active_config.SECRET_KEY
ADMIN_EMAILS = active_config.ADMIN_EMAILS
DEBUG = active_config.DEBUG
SQLALCHEMY_DATABASE_URI = active_config.SQLALCHEMY_DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = active_config.SQLALCHEMY_TRACK_MODIFICATIONS
UPLOAD_FOLDER = active_config.UPLOAD_FOLDER
MAX_FILE_SIZE = active_config.MAX_FILE_SIZE
ALLOWED_EXTENSIONS = active_config.ALLOWED_EXTENSIONS
ROLE_STUDENT = active_config.ROLE_STUDENT
ROLE_ADMIN = active_config.ROLE_ADMIN
VALID_STATUSES = active_config.VALID_STATUSES
STATUS_TRANSITIONS = active_config.STATUS_TRANSITIONS
SESSION_PERMANENT = active_config.SESSION_PERMANENT
SESSION_COOKIE_HTTPONLY = active_config.SESSION_COOKIE_HTTPONLY
SESSION_COOKIE_SECURE = active_config.SESSION_COOKIE_SECURE
SESSION_COOKIE_SAMESITE = active_config.SESSION_COOKIE_SAMESITE
WTF_CSRF_ENABLED = active_config.WTF_CSRF_ENABLED
WTF_CSRF_TIME_LIMIT = active_config.WTF_CSRF_TIME_LIMIT
RATE_LOGIN_MAX = active_config.RATE_LOGIN_MAX
RATE_LOGIN_WINDOW = active_config.RATE_LOGIN_WINDOW
RATE_OTP_MAX = active_config.RATE_OTP_MAX
RATE_OTP_WINDOW = active_config.RATE_OTP_WINDOW
RATE_COMPLAINT_MAX = active_config.RATE_COMPLAINT_MAX
RATE_COMPLAINT_WIN = active_config.RATE_COMPLAINT_WIN
RATE_FEEDBACK_MAX = active_config.RATE_FEEDBACK_MAX
RATE_FEEDBACK_WIN = active_config.RATE_FEEDBACK_WIN
GOOGLE_CLIENT_ID = active_config.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = active_config.GOOGLE_CLIENT_SECRET
EMAIL_HOST = active_config.EMAIL_HOST
EMAIL_PORT = active_config.EMAIL_PORT
EMAIL_USE_TLS = active_config.EMAIL_USE_TLS
EMAIL_USE_SSL = active_config.EMAIL_USE_SSL
EMAIL_TIMEOUT = active_config.EMAIL_TIMEOUT
EMAIL_USER = active_config.EMAIL_USER
EMAIL_PASSWORD = active_config.EMAIL_PASSWORD
EMAIL_FROM = active_config.EMAIL_FROM
HOST = active_config.HOST
PORT = active_config.PORT
