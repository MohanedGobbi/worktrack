FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    postgresql-client \
    postgresql-dev \
    gcc \
    musl-dev \
    libffi-dev \
    bash \
    poppler-utils

# Copy requirements early for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN mkdir -p staticfiles logs media && \
    python manage.py collectstatic --noinput || true

# Create non-root user
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser && \
    chown -R appuser:appgroup /app
USER appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn worktrack_pro.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"]
