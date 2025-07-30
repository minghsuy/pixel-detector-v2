# Use Microsoft's official Playwright Python image as base
FROM mcr.microsoft.com/playwright/python:v1.53.0-noble

# Install system dependencies for Lambda
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    cmake \
    unzip \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install poetry and dependencies
RUN pip install poetry==2.1.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --extras lambda

# Copy source code
COPY src/ ./src/

# Create lambda handler
RUN cat > lambda_handler.py << 'EOF'
import asyncio
import json
import os
from pixel_detector import PixelScanner


def lambda_handler(event, context):
    """AWS Lambda handler function"""
    
    # Get domain from event
    domain = event.get('domain')
    if not domain:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Domain parameter is required'})
        }
    
    # Configure scanner
    scanner = PixelScanner(
        headless=True,
        stealth_mode=True,
        screenshot=False,
        timeout=event.get('timeout', 30000)
    )
    
    # Run scan
    try:
        result = asyncio.run(scanner.scan_domain(domain))
        
        return {
            'statusCode': 200,
            'body': json.dumps(result.dict(), default=str)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'domain': domain
            })
        }
EOF

# Set environment variables
ENV HOME=/tmp
ENV PYTHONPATH=/app

# Set the CMD to your handler
CMD ["lambda_handler.lambda_handler"]