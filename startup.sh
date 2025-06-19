#!/bin/bash

echo "Waiting for database to be ready..."

# Wait for database to be ready
until poetry run python init_db_standalone.py; do
    echo "Database is not ready yet. Waiting..."
    sleep 2
done

echo "Database is ready! Starting FastAPI service..."

# Start the FastAPI service
exec uvicorn rag_microservice.api:app --host 0.0.0.0 --port 8000 