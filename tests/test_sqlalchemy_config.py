import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import create_app
from academic_governance import config


def main() -> None:
    app = create_app()

    assert app.config["SQLALCHEMY_DATABASE_URI"] == config.SQLALCHEMY_DATABASE_URI
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql")
    assert "sqlalchemy" in app.extensions, "SQLAlchemy extension was not initialized."
    assert "migrate" in app.extensions, "Flask-Migrate extension was not initialized."

    print("test_sqlalchemy_config.py: PASS")


if __name__ == "__main__":
    main()
