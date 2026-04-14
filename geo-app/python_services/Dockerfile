# ================================================================
# DOCKERFILE — FastAPI + ML Model (Multi-Stage, Production)
# ================================================================
# Stage 1: builder  — install dependencies & compile wheels
# Stage 2: production — minimal runtime image with non-root user
# ================================================================

# ================================================================
# STAGE 1 — Builder
# ================================================================
FROM python:3.11.8-slim AS builder

WORKDIR /build

# Install build-time system dependencies (compiled wheels for psycopg2, numpy, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a virtual env
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ================================================================
# STAGE 2 — Production
# ================================================================
FROM python:3.11.8-slim AS production

LABEL maintainer="Samael Hernandez"
LABEL description="Backend API para Análisis Inmobiliario con ML"
LABEL version="2.0.0"

# Install only the runtime libraries we need (no compilers)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copy the pre-built virtual env from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/false --create-home appuser

WORKDIR /app

# Create necessary directories and set ownership
RUN mkdir -p /app/data /app/logs /app/ml_model/models \
    && chown -R appuser:appuser /app

# Copy application code (in a single layer for efficiency)
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser ml_model/ ./ml_model/
COPY --chown=appuser:appuser integrations/ ./integrations/
COPY --chown=appuser:appuser scrapers/ ./scrapers/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser tasks/ ./tasks/
COPY --chown=appuser:appuser middleware/ ./middleware/
COPY --chown=appuser:appuser config.py .
COPY --chown=appuser:appuser *.py ./

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Health check — verify the API responds
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

EXPOSE 8000

# Switch to non-root user
USER appuser

# Start the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--timeout-graceful-shutdown", "30"]
