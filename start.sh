#!/usr/bin/env bash

# start.sh

# Debugging: Print Python version and path
echo "Python version:"
python --version
echo "Python executable location:"
which python

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Debugging: List installed packages
echo "Installed packages:"
pip list

# Debugging: Check if uvicorn is installed
echo "Uvicorn location:"
which uvicorn

# Run migrations (if using Alembic)
# alembic upgrade head

# Start the application with uvicorn using python -m
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
