FROM python:3.14-slim AS base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Graceful shutdown: uvicorn handles SIGTERM by default
CMD ["uvicorn", "server.api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "30"]
