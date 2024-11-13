#!/bin/bash
pip install -r requirements.txt
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --log-level=debug \
    --access-logfile - \
    --error-logfile -
