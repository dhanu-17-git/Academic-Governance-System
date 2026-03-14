# Operations Runbook

## Health checks

- Verify the process is running: `systemctl status academic-governance-system`
- Verify Gunicorn is listening on port `8000`
- Verify Nginx can reach Gunicorn through the configured upstream
- Load `/login` and confirm a `200` response

## Logs

- Gunicorn stdout/stderr should be collected by `journald` or your process log pipeline
- Nginx access/error logs should be shipped to centralized logging
- Application errors should be monitored for repeated `403`, `429`, and `500` spikes

## Backup and restore

- Back up the primary database daily
- Back up uploaded files on the same schedule
- Test restoring both database contents and the uploads directory together

## Incident handling

- If `SECRET_KEY` is suspected leaked, rotate it immediately and invalidate sessions
- If database credentials are leaked, rotate the credentials and revoke the old account
- If uploads are suspected compromised, restrict access and review authorization logs

## Safe deploy checklist

1. Apply database changes before switching traffic
2. Restart Gunicorn
3. Reload Nginx
4. Verify login, OTP, complaint submission, admin dashboard, and secure upload access

## Known current limitations

- Test coverage is improving but not yet comprehensive for all admin/student flows
