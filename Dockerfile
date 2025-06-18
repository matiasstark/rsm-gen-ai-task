# syntax=docker/dockerfile:1
FROM python:3.10-slim

# System deps
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
RUN pip install "poetry==$POETRY_VERSION"

# Set workdir
WORKDIR /app

# Copy pyproject and poetry.lock first for better cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy app code
COPY rag_microservice ./rag_microservice
COPY initdb ./initdb

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["uvicorn", "rag_microservice.api:app", "--host", "0.0.0.0", "--port", "8000"] 