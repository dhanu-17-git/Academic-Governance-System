"""Structured logging configuration for the Academic Governance System.

Call ``setup_logging()`` once during application startup (e.g. inside
``create_app()``) to configure the root logger with both a console handler
and a rotating file handler that writes to ``logs/app.log``.
"""

import logging
import os

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs"
)
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging.

    * Logs to **console** (stdout).
    * Logs to **logs/app.log** (creates the directory if missing).
    * Uses the format ``%(asctime)s [%(levelname)s] %(name)s: %(message)s``.

    Parameters
    ----------
    level:
        The minimum severity level to capture.  Defaults to ``logging.INFO``.
    """
    os.makedirs(_LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if called more than once.
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
