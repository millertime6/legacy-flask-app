#!/usr/bin/env bash
# Elastic Beanstalk Python platform proxies to PORT (default 8000 per AWS), not 5000.
# This script avoids Procfile shell-expansion issues with ${VAR:-default}.
set -euo pipefail
PORT="${PORT:-8000}"
exec gunicorn --bind "0.0.0.0:${PORT}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  wsgi:app
