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

# Default command: run scheduler
CMD ["python", "main.py", "--schedule"]
