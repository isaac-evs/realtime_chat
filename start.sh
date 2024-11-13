# start.sh alternative

# Run migrations (if using Alembic)
# alembic upgrade head

# Start the application with uvicorn
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
