# NAYA SUPREME V19 — Multi-stage Docker Build
# Production-optimized image: ~200MB

FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Build wheels (cache layer)
RUN pip install --user --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir -r requirements.txt

# ============================================================================
# Production stage
# ============================================================================

FROM python:3.11-slim

LABEL maintainer="NAYA SUPREME V19" \
      version="19.0.0" \
      description="Autonomous AI Revenue Generation System"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    groupadd -r naya && useradd -r -g naya naya

# Copy Python packages from builder
COPY --from=builder /root/.local /home/naya/.local

# Copy application code
COPY --chown=naya:naya . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/exports && \
    chown -R naya:naya /app

# Set Python path
ENV PATH=/home/naya/.local/bin:$PATH \
    PYTHONPATH=/app:$PYTHONPATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Non-root user
USER naya

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose ports
EXPOSE 8000 8001 8080

# Default command: API server
CMD ["uvicorn", "NAYA_CORE.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]

# Alternative commands:
# For daemon: python main.py daemon
# For dashboard: python main.py dashboard --host 0.0.0.0 --port 8080
