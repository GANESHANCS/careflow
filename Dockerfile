# CAREFlow FastAPI Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root application user
RUN useradd -m -u 1000 -s /bin/bash careflow \
    && mkdir -p /app/data/uploads \
    && chown -R careflow:careflow /app

# Copy Alembic configuration, migrations, and application source code
COPY alembic.ini .
COPY backend ./backend
COPY data ./data
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh

# Set executable permissions for entrypoint and assign ownership to careflow user
RUN chmod +x ./scripts/entrypoint.sh \
    && chown -R careflow:careflow /app

USER careflow

# Expose API port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["./scripts/entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
