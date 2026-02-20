# SalesEcho AI - Backend Dockerfile
# Optimized for Railway and Google Cloud Run deployment

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser

# Copy wheels from builder
COPY --from=builder /wheels /wheels

# Install dependencies from wheels
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY app/ ./app/
COPY main.py .
COPY schema.prisma .

# Generate Prisma client
RUN prisma generate

# Create directories for temp files
RUN mkdir -p /app/recordings /app/temp \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables (defaults - override in deployment)
ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run the application
CMD ["sh", "-c", "uvicorn main:app --host ${HOST} --port ${PORT}"]
