# Live Setup Checklist

This guide covers the remaining operator work for staging or production. The application code is ready; the remaining tasks are credentials, Docker startup, migrations, and final manual verification.

## 1. Fill the Environment Files

Use these files:
- Production: `.env.production`
- Staging: `.env.staging`

Generate a strong `SECRET_KEY` in PowerShell:
```powershell
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Replace the placeholder values in the env files with real values for:
- `SECRET_KEY`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `EMAIL_HOST`
- `EMAIL_USER`
- `EMAIL_PASSWORD`
- `EMAIL_FROM`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SENTRY_DSN` if you want Sentry enabled

Make sure the password inside `DATABASE_URL` matches `POSTGRES_PASSWORD`.

## 2. Google OAuth Setup

Create credentials in [Google Cloud Console](https://console.cloud.google.com/):
1. Create or select a project.
2. Configure the OAuth consent screen.
3. Create an OAuth 2.0 Client ID for a web application.
4. Add these redirect URIs as needed:
   - Local: `http://127.0.0.1:5000/auth/google/callback`
   - Staging without proxy: `http://your-staging-host:5001/auth/google/callback`
   - Staging with proxy: `https://staging.yourdomain.com/auth/google/callback`
   - Production without proxy: `http://your-production-host:5000/auth/google/callback`
   - Production with proxy: `https://yourdomain.com/auth/google/callback`
5. Copy the client ID and secret into the matching env file.

## 3. SMTP Setup

Use your mail provider's SMTP settings.

Example for Gmail:
- `EMAIL_HOST=smtp.gmail.com`
- `EMAIL_PORT=587`
- `EMAIL_USE_TLS=true`
- `EMAIL_USER=youraddress@gmail.com`
- `EMAIL_PASSWORD=your-app-password`
- `EMAIL_FROM=youraddress@gmail.com`

If you use Gmail, enable 2-step verification and generate an App Password.

## 4. TLS Certificates for Optional Nginx Proxy

If you want HTTPS through the included nginx profile, place these files in [deployment/certs](C:/Users/User/Desktop/academic-governance-system/deployment/certs):
- `fullchain.pem`
- `privkey.pem`

If you are not using the proxy, you can skip this.

## 5. Docker Commands

Open PowerShell in [academic-governance-system](C:/Users/User/Desktop/academic-governance-system).

Production without proxy:
```powershell
docker compose --env-file .env.production -f docker-compose.yml up --build -d
```

Production with proxy:
```powershell
docker compose --env-file .env.production -f docker-compose.yml --profile proxy up --build -d
```

Staging without proxy:
```powershell
docker compose --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml up --build -d
```

Staging with proxy:
```powershell
docker compose --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml --profile proxy up --build -d
```

## 6. Apply Migrations

Production:
```powershell
docker compose --env-file .env.production -f docker-compose.yml exec web flask db upgrade
```

Staging:
```powershell
docker compose --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml exec web flask db upgrade
```

## 7. Final Manual Checks

Production checks:
- Open `http://127.0.0.1:5000/health` or your production domain `/health`
- Verify OTP email arrives
- Verify Google login succeeds and redirects back correctly
- Submit a complaint and verify it appears
- Update complaint status as admin and verify complaint-status email arrives
- Verify complaint upload access is restricted to owner/admin

Staging checks:
- Open `http://127.0.0.1:5001/health` or your staging domain `/health`
- Repeat the same OTP, Google login, complaint, and upload checks

## 8. Operator Checklist

- [ ] `.env.production` or `.env.staging` has real values
- [ ] `SECRET_KEY` is replaced
- [ ] DB password placeholders are replaced
- [ ] Google OAuth credentials are set
- [ ] SMTP credentials are set
- [ ] Docker Desktop is installed and running
- [ ] TLS cert files are present if proxy mode is used
- [ ] Containers start successfully
- [ ] `flask db upgrade` succeeds
- [ ] `/health` returns HTTP 200
- [ ] OTP email works
- [ ] Google OAuth works
- [ ] Complaint status email works