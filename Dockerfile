FROM python:3.11-slim AS base
WORKDIR /app
EXPOSE 8400

# Install system dependencies:
# - curl: health check
# - gnupg, apt-transport-https: for Microsoft package signing key
# - unixodbc-dev, g++: required by pyodbc
# - Microsoft ODBC Driver 18 for SQL Server: required by pyodbc
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        apt-transport-https \
        unixodbc-dev \
        g++ \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && apt-get purge -y --auto-remove gnupg apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

USER appuser

# Environment variables
ENV PORT=8400
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Container metadata
LABEL description="DREEF AI Backend Service"
LABEL version="1.0"
LABEL maintainer="DREEF Team"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8400/health || exit 1

ENTRYPOINT ["gunicorn", "main:app", \
            "--workers", "2", \
            "--worker-class", "uvicorn.workers.UvicornWorker", \
            "--bind", "0.0.0.0:8400", \
            "--timeout", "120", \
            "--keep-alive", "5"]
