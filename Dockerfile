# Terraform Generator Service - Railway deployment
FROM python:3.12-slim

WORKDIR /app

# Install build dependencies for pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY templates/ ./templates/

# Install the package and dependencies
RUN pip install --no-cache-dir .

# Railway sets PORT; default to 8000 for local runs
ENV PORT=8000
EXPOSE 8000

# Run the FastAPI app (shell form so $PORT expands at runtime)
CMD uvicorn terraform_generator.api:app --host 0.0.0.0 --port $PORT
