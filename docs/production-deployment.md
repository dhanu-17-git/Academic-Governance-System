# Production Deployment

## Prerequisites

- Linux host with `systemd`
- Python 3.14-compatible runtime
- `uv`
- Nginx
- A PostgreSQL instance reachable from the application host

## Current deployment status

The repository is configured for a PostgreSQL-only runtime with SQLAlchemy models and Alembic migrations.

## Required environment variables

- `FLASK_ENV=production`
- `SECRET_KEY=<strong-random-value>`
- `DATABASE_URL=<postgresql-connection-string>`
- `UPLOAD_FOLDER=/opt/academic-governance-system/uploads`
- `AGS_HOST=127.0.0.1`
- `AGS_PORT=8000`

## Install steps

1. Create the app directory at `/opt/academic-governance-system`.
2. Install `uv` and ensure the target host has Python `3.14` available.
3. Run `uv sync --locked` in the project root.
4. Provide secrets through `.env.production` or your secret manager.
5. Run `uv run flask --app app db upgrade`.
6. Ensure `/opt/academic-governance-system/uploads` exists and is writable by the service user.
7. Start Gunicorn with `uv run gunicorn -c deployment/gunicorn.conf.py wsgi:app`.

## Reverse proxy

- Use [nginx.conf](/C:/Users/User/Desktop/academic-governance-system/deployment/nginx.conf) as the starting template.
- Terminate TLS at Nginx or at the load balancer.
- Forward `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto`.

## Service management

- Use [systemd.service](/C:/Users/User/Desktop/academic-governance-system/deployment/systemd.service) as the starting unit file.
- Reload units with `systemctl daemon-reload`.
- Enable startup with `systemctl enable academic-governance-system`.
- Start with `systemctl start academic-governance-system`.