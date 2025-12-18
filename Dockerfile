FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY .env.example .env

# Create output directories
RUN mkdir -p output/data output/maps output/charts

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Martinique

# Copy static files
COPY static/ ./static/

# Expose port
EXPOSE 8000

# Run the API server (PORT provided by Render)
CMD gunicorn api:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
