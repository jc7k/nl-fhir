# Production Dockerfile for NL-FHIR Epic 1
# Multi-stage build for optimal size and security

# Stage 1: Build stage
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY src/ ./src/

# Install uv for dependency management
RUN pip install uv

# Install dependencies
RUN uv pip install --system .

# Stage 2: Production stage
FROM python:3.10-slim

# Security: Run as non-root user
RUN useradd -m -u 1000 nlf-hir && \
    mkdir -p /app && \
    chown -R nlf-hir:nlf-hir /app

# Set working directory
WORKDIR /app

# Copy application from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=nlf-hir:nlf-hir src/ ./src/
COPY --chown=nlf-hir:nlf-hir static/ ./static/
COPY --chown=nlf-hir:nlf-hir templates/ ./templates/

# Switch to non-root user
USER nlf-hir

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:8000/health'); exit(0 if r.status_code == 200 else 1)" || exit 1

# Expose port
EXPOSE 8000

# Environment variables for production
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Production server with Gunicorn and Uvicorn workers
CMD ["gunicorn", "nl_fhir.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]