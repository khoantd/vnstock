# Use Python 3.11 slim as base image
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies only when needed
FROM base AS deps
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production image
FROM base AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user with home directory
RUN groupadd --system --gid 1001 vnstock && \
    useradd --system --uid 1001 --gid vnstock --create-home --home-dir /home/vnstock vnstock

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=vnstock:vnstock . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/uploads /home/vnstock/.vnstock /home/vnstock/.config/matplotlib && \
    chown -R vnstock:vnstock /app /home/vnstock

USER vnstock

# Set environment variables for writable directories
ENV MPLCONFIGDIR=/home/vnstock/.config/matplotlib

# JWT Configuration
# Set JWT_SECRET_KEY at runtime via docker run -e or docker-compose
# Example: docker run -e JWT_SECRET_KEY=your-secret-key ...
# If not set, will use default from rest_api.py (not recommended for production)
# Note: Set this environment variable when running the container

EXPOSE 8002

ENV PORT=8002
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/docs || exit 1

# Start the application
CMD ["uvicorn", "vnstock.api.rest_api:app", "--host", "0.0.0.0", "--port", "8002"]
