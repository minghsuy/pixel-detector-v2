# Production Dockerfile for Pixel Detector
# Optimized for Docker/Rancher deployment
# NOT for Lambda - use locally or in container orchestration

FROM python:3.11-slim

# Corporate proxy configuration
# Set these via --build-arg when building behind a proxy:
# docker build --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTPS_PROXY=$HTTPS_PROXY ...
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# Set proxy environment variables if provided
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock ./

# Install Python dependencies with proxy support
RUN if [ -n "$HTTP_PROXY" ]; then \
        pip config set global.proxy $HTTP_PROXY; \
    fi && \
    pip install --no-cache-dir poetry==1.8.5 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main

# Pre-cache tldextract public suffix list during build
# This prevents SSL certificate issues at runtime in corporate environments
# If behind proxy, this might fail - that's OK, we'll handle it at runtime
RUN python -c "import os; os.environ['REQUESTS_CA_BUNDLE'] = ''; \
    import tldextract; tldextract.extract('example.com')" && \
    echo "Successfully cached public suffix list" || \
    echo "Warning: Could not pre-cache public suffix list, will try at runtime"

# Install Playwright browsers with proxy support
# Note: Playwright respects HTTP_PROXY/HTTPS_PROXY environment variables
RUN if [ -n "$HTTPS_PROXY" ]; then \
        export PLAYWRIGHT_DOWNLOAD_HOST="$HTTPS_PROXY" || true; \
    fi && \
    playwright install chromium || \
    (echo "Warning: Playwright install failed, trying without SSL verification" && \
     NODE_TLS_REJECT_UNAUTHORIZED=0 playwright install chromium)

# Copy application code
COPY src/ ./src/
COPY production_scanner.py url_handler.py ./

# Create directories for input/output
RUN mkdir -p /app/input /app/output

# Make sure Python can find our modules
ENV PYTHONPATH=/app:/app/src

# Default entrypoint for production scanner
ENTRYPOINT ["python", "/app/production_scanner.py"]

# Default shows help if no arguments
CMD ["--help"]