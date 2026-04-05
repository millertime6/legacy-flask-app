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

- `Procfile` + `gunicorn_start.sh` for Gunicorn (reliable `PORT` handling on Elastic Beanstalk)
- `wsgi.py` as production app entrypoint
- `runtime.txt` for Python runtime pinning
- Postgres driver support in `requirements.txt` (`psycopg[binary]`)
- Production-aware config in `config/settings.py`
- Existing `/health` endpoint for load balancer health checks
- **`.platform/nginx/conf.d/elasticbeanstalk/proxy_timeouts.conf`** — longer nginx proxy timeouts to reduce spurious **499** / client timeouts when the app is slow

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
  DATABASE_URL=replace-with-rds-url

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

To **limit access by IP**, do it in AWS (for example **AWS WAF** on the load balancer with an IP allowlist, or network rules that fit your architecture). The app no longer enforces client IP; that avoids breaking health checks and mis-detection of client IPs behind proxies.

### If you see HTTP 502 (Bad Gateway)

The load balancer reached the instance, but the app process was not accepting connections or crashed on startup.

1. **Logs** — In the EB console: *Logs* → *Request full logs* (or **SSH** and read `/var/log/web.stdout.log`, `/var/log/web.stderr.log`, `/var/log/nginx/error.log`).
2. **`DATABASE_URL`** — Must be set to RDS PostgreSQL. The default SQLite path is a poor fit on EB (and `db.create_all()` at startup will fail if the DB is unreachable). Ensure the RDS security group allows the EB environment’s instances (or their security group) on port 5432.
3. **RDS TLS** — If the engine requires SSL, append query params to the URL, for example: `?sslmode=require` (psycopg3 / libpq).
4. **Port** — On the **Python** platform, EB’s nginx forwards to **`PORT`**, which defaults to **8000** (see [AWS Python Procfile](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/python-configuration-procfile.html)). `gunicorn_start.sh` uses the same default so Gunicorn and nginx stay aligned. If you set `PORT` in the EB console, it must match on both sides; remove a wrong value (e.g. `5000`) if you see `connect() failed ... 127.0.0.1:8000` while the app listens elsewhere.

### If you see HTTP 499 or “timeout” in the browser

**499** (Nginx) means the **client closed the connection** before the response finished — often because something upstream (ALB, browser) gave up while **Gunicorn was still working** or was stuck.

1. **`GET /health`** — Should return JSON quickly. If even this hangs, check **`web.stderr.log`** for worker crashes, DB connection errors, or **Gunicorn `[CRITICAL] WORKER TIMEOUT`**.
2. **Load balancer idle timeout** — Application Load Balancer default is often **60 seconds**. In the **EB console** → *Configuration* → *Load balancer* (or edit the ALB in EC2), increase **Idle timeout** (e.g. **120** seconds) if pages legitimately take longer.
3. **Nginx → app timeouts** — This repo ships **`.platform/nginx/conf.d/elasticbeanstalk/proxy_timeouts.conf`** (120s read/send/connect). Redeploy so it is included in the bundle; it extends how long nginx waits on Gunicorn.
4. **Gunicorn** — Set **`GUNICORN_TIMEOUT=120`** (or higher) in EB environment properties if workers are killed mid-request; keep it **≥** the ALB idle timeout if possible.
5. **Small instance / many workers** — On **t3.micro** etc., **`GUNICORN_WORKERS=3`** can starve memory and make everything slow; try **`GUNICORN_WORKERS=1`** and **`GUNICORN_THREADS=4`** temporarily.

### Database Notes

- For AWS, use **RDS PostgreSQL** (do not use SQLite in live dev).
- **`DATABASE_URL` format** — Use a single line, **no surrounding quotes** in the Elastic Beanstalk console (quotes are stripped if present). This project uses **psycopg3**; a typical RDS URL looks like:
  - `postgresql+psycopg://USERNAME:PASSWORD@your-rds.region.rds.amazonaws.com:5432/dbname?sslmode=require`
  - If the master password contains **`@`, `#`, `:`, `/`, `%`, or spaces**, those must be [**percent-encoded**](https://en.wikipedia.org/wiki/Percent-encoding) (e.g. `@` → `%40`). A password `p@ss#word` is invalid in the URL until encoded.
  - The app normalizes `postgresql://` and `postgres://` to `postgresql+psycopg://` automatically.
  - On **Elastic Beanstalk** with an attached RDS database, AWS also sets **`RDS_HOSTNAME`**, **`RDS_USERNAME`**, **`RDS_PASSWORD`**, **`RDS_PORT`**, and **`RDS_DB_NAME`**. If **`DATABASE_URL` is missing** or you mistakenly set it to **only the hostname** (no `postgresql://...`), the app builds the URL from those variables and enables **`sslmode=require`** in the URL.
  - **`DATABASE_SSLMODE`** — For PostgreSQL, the engine also passes **`sslmode`** to psycopg (`require` when the host contains **`rds.amazonaws.com`**, otherwise **`prefer`** unless you set this). If logs show **`server closed the connection unexpectedly`** on connect, set **`DATABASE_SSLMODE=require`** explicitly or add **`?sslmode=require`** to **`DATABASE_URL`**.
- Run seed after first deploy:

```bash
eb ssh
source /var/app/venv/*/bin/activate
cd /var/app/current
python scripts/seed_data.py --contacts 60 --applications 180 --loans 90 --activities 360 --branches 12
```
