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
curl -X POST http://localhost:5000/api/v1/applications \
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
curl -X POST http://localhost:5000/api/v1/applications/A-9001/decision \
  -H "Authorization: Bearer dev-integration-token" \
  -H "Content-Type: application/json" \
  -d '{"decision":"APPROVED"}'
```

### 3) Book Loan

```bash
curl -X POST http://localhost:5000/api/v1/applications/A-9001/book-loan \
  -H "Authorization: Bearer dev-integration-token"
```

### 4) Create Activity

```bash
curl -X POST http://localhost:5000/api/v1/activities \
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

//url for homepage is http://localhost:5001/servicing
