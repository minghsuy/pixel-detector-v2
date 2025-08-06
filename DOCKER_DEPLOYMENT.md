# Docker/Rancher Deployment Guide

## Quick Start

### Build the Image
```bash
docker build -t pixel-scanner:production .
```

### Run Portfolio Scan (CSV with custom_id)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output --concurrent 10
```

### Run On-Demand Scan (TXT domain list)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  /app/input/domains.txt /app/output --concurrent 5
```

## Input File Formats

### Portfolio Mode (CSV)
Create `input/portfolio.csv`:
```csv
custom_id,url
HOSP001,stanford.edu
HOSP002,www.mayo.edu
HOSP003,https://clevelandclinic.org
HOSP004,user@email.com
HOSP005,none
```

The scanner will:
- Clean and validate each URL
- Reject invalid entries (emails, "none", etc.)
- Deduplicate domains
- Preserve custom_id for join-back

### On-Demand Mode (TXT)
Create `input/domains.txt`:
```text
google.com
stanford.edu
mayo.edu
badensports.com
```

## Docker Compose

### For Batch Processing
Use `docker-compose.batch.yml`:

```bash
# Edit docker-compose.batch.yml to set your input file
# Then run:
docker-compose -f docker-compose.batch.yml up

# Results will be in ./output/
```

### Resource Configuration
Adjust in docker-compose.batch.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '6'      # Max CPUs
      memory: 16G    # Max memory
    reservations:
      cpus: '2'      # Min CPUs
      memory: 4G     # Min memory
```

## Rancher/Kubernetes Deployment

### Create Deployment YAML
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pixel-scanner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pixel-scanner
  template:
    metadata:
      labels:
        app: pixel-scanner
    spec:
      containers:
      - name: scanner
        image: pixel-scanner:production
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "6"
        volumeMounts:
        - name: input
          mountPath: /app/input
          readOnly: true
        - name: output
          mountPath: /app/output
        command: ["/app/input/portfolio.csv", "/app/output", "--concurrent", "10"]
      volumes:
      - name: input
        persistentVolumeClaim:
          claimName: scanner-input-pvc
      - name: output
        persistentVolumeClaim:
          claimName: scanner-output-pvc
      restartPolicy: OnFailure
```

### Create Job for One-Time Scan
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pixel-scan-job
spec:
  template:
    spec:
      containers:
      - name: scanner
        image: pixel-scanner:production
        resources:
          limits:
            memory: "16Gi"
            cpu: "6"
        volumeMounts:
        - name: input
          mountPath: /app/input
        - name: output
          mountPath: /app/output
        command: ["/app/input/portfolio.csv", "/app/output", "--concurrent", "10"]
      volumes:
      - name: input
        configMap:
          name: scan-input
      - name: output
        emptyDir: {}
      restartPolicy: Never
  backoffLimit: 2
```

## Performance Tuning

### For Large Portfolios (1000+ domains)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output \
  --concurrent 10 \
  --timeout 30000
```

### For Corporate Networks (strict firewalls)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="8g" --cpus="4" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output \
  --concurrent 3 \
  --timeout 45000
```

### For Quick Scans (10-50 domains)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  pixel-scanner:production \
  /app/input/domains.txt /app/output \
  --concurrent 5 \
  --timeout 20000
```

## Output Files

### Portfolio Mode
- `output/portfolio_results.csv` - Full results with custom_id
- `output/scan_results/*.json` - Individual domain results
- `output/checkpoint.json` - Resume capability
- `output/id_domain_mapping.json` - Deduplication mapping

### On-Demand Mode
- `output/scan_results.csv` - Simple results table
- `output/scan_results/*.json` - Individual domain results
- `output/checkpoint.json` - Resume capability

## Monitoring

### View Logs
```bash
docker logs -f pixel-scanner-batch
```

### Check Progress
```bash
# Count completed scans
ls output/scan_results/*.json | wc -l

# View checkpoint
cat output/checkpoint.json | jq .
```

## Troubleshooting

### Container Exits Immediately
Check if input file exists:
```bash
docker run --rm -v $(pwd)/input:/app/input:ro pixel-scanner:production ls -la /app/input/
```

### Permission Denied
Ensure volumes are mounted correctly:
```bash
# Use absolute paths if relative paths don't work
docker run --rm \
  -v /absolute/path/to/input:/app/input:ro \
  -v /absolute/path/to/output:/app/output:rw \
  ...
```

### Timeout Issues
Increase timeout and reduce concurrency:
```bash
--concurrent 2 --timeout 60000
```

### Memory Issues
Reduce concurrency:
```bash
--concurrent 1
```

## Best Practices

1. **Always set resource limits** to prevent container from consuming all resources
2. **Use read-only mounts** for input files (`:ro`)
3. **Monitor first few domains** to ensure scanning works
4. **Save checkpoint regularly** (automatic every 10 domains)
5. **Use absolute paths** in production environments

## Example Production Run

```bash
# 1. Prepare input
mkdir -p input output
cp /path/to/portfolio.csv input/

# 2. Build image
docker build -t pixel-scanner:production .

# 3. Run scan
docker run --rm \
  --name pixel-scan-$(date +%Y%m%d-%H%M%S) \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" \
  --cpus="6" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output \
  --concurrent 10 \
  --timeout 30000

# 4. Check results
ls -la output/
cat output/portfolio_results.csv | head
```