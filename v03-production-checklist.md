# v0.3 Lambda Production Checklist

## Must Have (Week 1)

### 1. Error Handling
```python
# Add to lambda_handler.py
class LambdaError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

# Specific error cases
try:
    # ... scanning code ...
except TimeoutError:
    return {'statusCode': 504, 'body': json.dumps({'error': 'Scan timeout'})}
except Exception as e:
    logger.error(f"Unhandled error: {str(e)}", exc_info=True)
    return {'statusCode': 500, 'body': json.dumps({'error': 'Internal error'})}
```

### 2. Resource Cleanup
```python
# Critical for Lambda - clean up /tmp after each invocation
import shutil
import atexit

def cleanup_tmp():
    for item in ['/tmp/.cache', '/tmp/playwright-*', '/tmp/core*']:
        try:
            if os.path.exists(item):
                shutil.rmtree(item) if os.path.isdir(item) else os.remove(item)
        except:
            pass

atexit.register(cleanup_tmp)
```

### 3. Basic Monitoring
```python
# Simple CloudWatch metrics without Lambda Powertools
import time
import json

def lambda_handler(event, context):
    start_time = time.time()
    
    # Your scanning logic
    
    # Log structured data for CloudWatch Insights
    print(json.dumps({
        'metric': 'scan_complete',
        'domain': domain,
        'duration': time.time() - start_time,
        'pixels_found': len(result.pixels_detected),
        'memory_used': context.memory_limit_in_mb,
        'request_id': context.request_id
    }))
```

### 4. Timeout Handling
```python
# Lambda timeout buffer (set Lambda timeout to 300s, internal timeout to 270s)
LAMBDA_TIMEOUT = 300
SCAN_TIMEOUT = 270

async def scan_with_timeout(domain: str):
    try:
        return await asyncio.wait_for(
            scanner.scan_domain(domain),
            timeout=SCAN_TIMEOUT
        )
    except asyncio.TimeoutError:
        return ScanResult(
            domain=domain,
            error=True,
            error_message="Scan timeout after 270 seconds"
        )
```

### 5. Cold Start Optimization
```python
# Initialize expensive objects outside handler
import os
scanner = None

def get_scanner():
    global scanner
    if scanner is None:
        scanner = PixelScanner()
    return scanner

def lambda_handler(event, context):
    scanner = get_scanner()  # Reuse across warm invocations
```

## Nice to Have (Week 2)

### 6. API Key Authentication
```python
# Simple API key check
API_KEY = os.environ.get('API_KEY')

def lambda_handler(event, context):
    if API_KEY:
        provided_key = event.get('headers', {}).get('x-api-key')
        if provided_key != API_KEY:
            return {'statusCode': 401, 'body': json.dumps({'error': 'Unauthorized'})}
```

### 7. Request Validation
```python
from urllib.parse import urlparse

def validate_domain(domain: str) -> bool:
    # Basic validation
    if not domain or len(domain) > 255:
        return False
    
    # Block internal/private IPs
    private_patterns = ['localhost', '127.0.0.1', '192.168.', '10.', '172.']
    if any(p in domain for p in private_patterns):
        return False
    
    return True
```

### 8. Response Caching
```python
# Simple in-memory cache for warm containers
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_cached_result(domain: str, cache_key: str):
    # Returns cached result if less than 1 hour old
    pass
```

## Testing Strategy

### Local Lambda Testing
```bash
# Test with Docker locally before deploying
docker run -p 9000:8080 \
  -e HOME=/tmp \
  pixel-detector:v0.3.0

# In another terminal
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"body": "{\"domain\": \"example.com\"}"}'
```

### Load Testing
```bash
# Simple load test with curl
for i in {1..10}; do
  curl -X POST $API_ENDPOINT \
    -H "Content-Type: application/json" \
    -d '{"domain": "example'$i'.com"}' &
done
wait
```

## Rollback Plan

```bash
# Tag previous version before deploying
docker tag $ECR_URI/pixel-detector:latest $ECR_URI/pixel-detector:v0.2.1-backup

# Quick rollback if needed
aws lambda update-function-code \
  --function-name pixel-detector-v03 \
  --image-uri $ECR_URI/pixel-detector:v0.2.1-backup
```

## Success Metrics for v0.3

- [ ] Successfully deployed to Lambda
- [ ] Can scan real healthcare sites via API
- [ ] <10s response time for single domain
- [ ] Handles errors gracefully (no 500s)
- [ ] Stays within Lambda free tier
- [ ] No memory leaks across invocations
- [ ] Cold start <15 seconds
- [ ] Warm invocation <10 seconds

## Post-Launch Monitoring

```bash
# Watch for errors
aws logs tail /aws/lambda/pixel-detector-v03 --follow --filter-pattern ERROR

# Check performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=pixel-detector-v03 \
  --statistics Average,Maximum \
  --start-time 2025-08-03T00:00:00Z \
  --end-time 2025-08-03T23:59:59Z \
  --period 3600
```