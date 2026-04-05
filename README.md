# Legacy Loan Servicing Flask Backend

Production-style simulation of a legacy loan servicing system acting as the system of record in a multi-system enterprise integration architecture (Salesforce + MuleSoft + AWS + customer app).

## Project Structure

```text
app/
  models/
  routes/
  services/
  db/
  utils/
config/
run/
scripts/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_data.py
PORT=5001 python run/server.py
```

Local UI: `http://localhost:5001/login`

## Auth

All integration endpoints require bearer token auth:

- Header: `Authorization: Bearer <API_TOKEN>`
- Default token: `dev-integration-token`
- Override via `.env` (`API_TOKEN=...`)

## Internal Servicing UI

The project now includes a basic employee-facing servicing interface:

- `GET /servicing` - dashboard with key metrics
- `GET /servicing/applications` - search/filter applications
- `GET/POST /servicing/applications/new` - create application
- `GET /servicing/applications/<external_id>` - view/approve/deny/book
- `GET /servicing/loans` - search/filter loans
- `GET /servicing/loans/<external_id>` - loan detail view

Use this for internal servicing workflows while integrations continue to use `/api/v1/*`.

The servicing UI now requires login:

- Login page: `GET /login`
- Default username: `servicing`
- Default password: `servicing123`
- Override via `.env`:
  - `UI_USERNAME=...`
  - `UI_PASSWORD=...`

## Key Endpoints (MuleSoft Integration)

- `POST /api/v1/applications` - Create/update application (UPSERT by `external_id`)
- `POST /api/v1/applications/<external_id>/decision` - Approve/deny application
- `POST /api/v1/applications/<external_id>/book-loan` - Book loan from approved application
- `POST /api/v1/activities` - Create/update activity task
- `GET /api/v1/loans/<external_id>` - Loan details
- `GET /api/v1/contacts/<external_id>` - Contact details

## Example Requests

### 1) UPSERT Application

```bash
curl -X POST http://localhost:5001/api/v1/applications \
  -H "Authorization: Bearer dev-integration-token" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: corr-1234" \
  -d '{
    "external_id": "A-9001",
    "loan_amount": 18000,
    "credit_score": 702,
    "first_name": "Jordan",
    "last_name": "Hayes",
    "ssn": "222-44-1111",
    "email": "jordan.hayes@example.com"
  }'
```

### 2) Approve Application

```bash
curl -X POST http://localhost:5001/api/v1/applications/A-9001/decision \
  -H "Authorization: Bearer dev-integration-token" \
  -H "Content-Type: application/json" \
  -d '{"decision":"APPROVED"}'
```

### 3) Book Loan

```bash
curl -X POST http://localhost:5001/api/v1/applications/A-9001/book-loan \
  -H "Authorization: Bearer dev-integration-token"
```

### 4) Create Activity

```bash
curl -X POST http://localhost:5001/api/v1/activities \
  -H "Authorization: Bearer dev-integration-token" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "T-9991",
    "account_external_id": "C-A-9001",
    "subject": "Customer Follow-up",
    "description": "Discuss payment schedule",
    "status": "OPEN",
    "due_date": "2026-04-05"
  }'
```

## Batch Export

Daily extract for reconciliation / downstream sync:

```bash
python scripts/batch_export.py --format json
python scripts/batch_export.py --format csv
```

Exports all entities (`contacts`, `loans`, `applications`, `activities`, `branches`) with `created_date` + `updated_date` fields for watermarking.

## Logging

Structured JSON logs include:

- `correlation_id`
- `entity_type`
- `operation`
- `status`
- `timestamp`

SSN data is masked in audit logs.

## Deployment Readiness

This repo is now prepared for AWS deployment:

- `Procfile` for process startup with Gunicorn
- `wsgi.py` as production app entrypoint
- `runtime.txt` for Python runtime pinning
- Postgres driver support in `requirements.txt` (`psycopg[binary]`)
- Production-aware config in `config/settings.py`
- Existing `/health` endpoint for load balancer health checks

### Recommended Target

Use **AWS Elastic Beanstalk (Python 3.12)** for the first live dev environment.

### Deploy Steps (Elastic Beanstalk)

```bash
# 1) Install and configure EB CLI (one-time)
pip install awsebcli
eb init -p python-3.12 legacy-flask-app

# 2) Create environment
eb create legacy-flask-dev

# 3) Set application environment variables
eb setenv APP_ENV=production DEBUG=false SESSION_COOKIE_SECURE=true \
  SECRET_KEY=replace-me API_TOKEN=replace-me UI_USERNAME=replace-me UI_PASSWORD=replace-me \
  DATABASE_URL=replace-with-rds-url \
  IP_ALLOWLIST=203.0.113.10 TRUST_PROXY_HEADERS=true

# 4) Deploy
eb deploy
eb open
```

### Environment Variables for AWS

Required:

- `APP_ENV=production`
- `DEBUG=false`
- `SECRET_KEY=<strong-random-string>`
- `API_TOKEN=<integration-token>`
- `UI_USERNAME=<servicing-login-user>`
- `UI_PASSWORD=<servicing-login-password>`
- `DATABASE_URL=<RDS PostgreSQL connection string>`

Optional tuning:

- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=Lax`
- `GUNICORN_WORKERS=3`
- `GUNICORN_THREADS=2`
- `GUNICORN_TIMEOUT=60`
- `BATCH_EXPORT_DIR=/tmp/exports`
- `IP_ALLOWLIST=<comma-separated-ips>` — if set, only those client IPs may use the app (others get 403). **`GET /health` is not restricted** so Elastic Beanstalk / ALB health checks keep working.
- `TRUST_PROXY_HEADERS=true` — read the client IP from `X-Forwarded-For` (last hop, as appended by AWS ALB). Defaults to **on** when `APP_ENV=production`; set `false` for direct local access without a load balancer.

### Database Notes

- For AWS, use **RDS PostgreSQL** (do not use SQLite in live dev).
- Run seed after first deploy:

```bash
eb ssh
source /var/app/venv/*/bin/activate
cd /var/app/current
python scripts/seed_data.py --contacts 60 --applications 180 --loans 90 --activities 360 --branches 12
```
