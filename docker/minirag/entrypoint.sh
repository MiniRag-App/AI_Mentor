#!/bin/bash
set -e

echo "Database is up - running migrations..."
cd /app/models/db_schemes/mini_rag/
alembic upgrade head
cd /app

# run the command passed by CMD
exec "$@"
