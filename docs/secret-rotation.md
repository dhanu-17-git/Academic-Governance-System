# Secret Rotation

## Secrets in scope

- `SECRET_KEY`
- Database credentials in `SQLALCHEMY_DATABASE_URI` or `DATABASE_URL`
- Any provider credentials added in future integrations

## Rotation procedure

1. Generate the replacement secret in your secret manager.
2. Update the deployment environment file or secret reference.
3. Restart the application process.
4. Confirm `/login` works and new sessions can be created.
5. Revoke the old credential after validation.

## Emergency rotation

- For a leaked `SECRET_KEY`, rotate immediately and expect all active sessions to be invalidated.
- For leaked database credentials, rotate the password and verify the old credential can no longer connect.

## Storage rules

- Do not commit live secrets to the repository
- Keep `.env.local` for local development only
- Prefer platform-managed secret injection in production
