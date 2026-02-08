# Backend Dockerfile for Financial Observability Platform
FROM python:3.12-slim

WORKDIR /app

# Copy requirements files
COPY requirements.txt ./requirements.txt
COPY apps/backend/requirements.txt ./apps/backend/requirements.txt

# Install Python dependencies (psycopg2-binary ships pre-compiled, no gcc needed)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory for ML model persistence
RUN mkdir -p models

# Expose port
EXPOSE 8000

# Health check (python-based, no curl needed in slim image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start command
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
