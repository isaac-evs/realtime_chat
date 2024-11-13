#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Start the application
exec venv/bin/gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --log-level=debug \
    --access-logfile - \
    --error-logfile -
