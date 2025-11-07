# Simplified Dockerfile for Pixel Detector using uv
# Uses the working CLI tool that correctly detects pixels

FROM python:3.11-slim

# Corporate proxy support (optional)
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

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies and the project
RUN uv sync --frozen --no-dev

# Pre-cache tldextract public suffix list
RUN uv run python -c "import tldextract; tldextract.extract('example.com')" && \
    echo "Successfully cached public suffix list" || \
    echo "Warning: Could not pre-cache public suffix list, will try at runtime"

# Install Playwright browsers
RUN uv run playwright install chromium || \
    (echo "Warning: Playwright install failed, trying without SSL verification" && \
     NODE_TLS_REJECT_UNAUTHORIZED=0 uv run playwright install chromium)

# Create directories for input/output
RUN mkdir -p /app/input /app/output

# Set Python path
ENV PYTHONPATH=/app:/app/src

# Use uv run as entrypoint
ENTRYPOINT ["uv", "run", "pixel-detector"]

# Default command shows help
CMD ["--help"]
