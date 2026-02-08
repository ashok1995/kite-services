FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV POETRY_CACHE_DIR=/opt/poetry-cache
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry: Don't create virtual env, install to system
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi && \
    rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY src/ ./src/

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chmod -R 777 /app/logs /app/data

# Set Python path
ENV PYTHONPATH=/app/src

# Default to dev port (overridden by compose/env)
ENV SERVICE_PORT=8079

# Expose both dev and prod ports
EXPOSE 8079 8179

# Health check (uses SERVICE_PORT env var)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${SERVICE_PORT}/health || exit 1

# Copy and set entrypoint
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "src/main.py"]
