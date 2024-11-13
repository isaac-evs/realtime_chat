#!/usr/bin/env bash

# start.sh

# Run migrations (if using Alembic)
# alembic upgrade head

# Start the application
exec gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4
