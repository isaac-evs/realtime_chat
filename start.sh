#!/usr/bin/env bash

exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --log-level=debug \
    --access-logfile - \
    --error-logfile -
