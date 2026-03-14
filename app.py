"""Compatibility entrypoint for local runs and simple imports."""

from academic_governance import create_app
from academic_governance import config

app = create_app()


if __name__ == "__main__":
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
