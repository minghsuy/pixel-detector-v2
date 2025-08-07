# Docker Deployment Guide

## Quick Start

### Build the Image
```bash
# Regular build
docker build -t pixel-scanner:production .

# For corporate environments with proxy/SSL inspection
./build-with-proxy.sh
```

### Run Single Domain Scan
```bash
docker run --rm pixel-scanner:production scan google.com
```

### Run Portfolio Scan (CSV with custom_id,url columns)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  batch /app/input/portfolio.csv -o /app/output --max-concurrent 10
```

### Run Batch Scan (TXT domain list)
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  batch /app/input/domains.txt -o /app/output --max-concurrent 5
```

## Pre-Flight Testing (Recommended)

Before running large portfolios (1000+ domains), test with smaller batches to verify everything works correctly.

### Quick Test (5-10 minutes)
```bash
# Create test file with 10 domains
cat > input/test_domains.txt << EOF
google.com
stanford.edu
mayo.edu
cdc.gov
badensports.com
EOF

# Run quick test
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="4g" --cpus="2" \
  pixel-scanner:production \
  batch /app/input/test_domains.txt -o /app/output --max-concurrent 3

# Verify outputs
ls -la output/    # Should see scan_results.csv and JSON files
cat output/scan_results.csv    # Check CSV output with all results
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

## Scanner Options & Configuration

### Available Command-Line Options
```bash
# production_scanner.py accepts these options:
--concurrent N      # Max concurrent scans (default: 5, recommended: 10-15)
--timeout N         # Timeout in milliseconds (default: 30000, max: 60000)
--mode MODE         # Force mode: portfolio or ondemand (default: auto-detect)
--no-variations     # Disable URL variations (only try https://domain)
```

### What the Scanner Does
- ✅ **Detects 8 pixel types**: Meta, Google Analytics, Google Ads, TikTok, LinkedIn, Twitter, Pinterest, Snapchat
- ✅ **Network monitoring**: Captures tracking requests
- ✅ **DOM inspection**: Finds tracking scripts
- ✅ **Cookie detection**: Identifies tracking cookies
- ❌ **No screenshots**: Faster scanning without visual capture
- ✅ **Smart retries**: Tries www/non-www, http/https variations
- ✅ **Checkpoint/resume**: Saves progress every 10 domains

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

### System Sleep Interrupted Scan
If your system went to sleep during a long scan:
```bash
# 1. Check how many domains were completed
cat output/checkpoint.json | jq '.completed_domains | length'

# 2. Resume from checkpoint (just run same command again)
# The scanner will automatically skip completed domains
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output --concurrent 10

# 3. IMPORTANT: Use caffeinate this time!
caffeinate -d -i -m -s docker run ... # (same command with caffeinate prefix)
```

## Checkpoint/Resume for Large Batches

The scanner automatically saves progress every 10 domains, allowing you to resume interrupted scans.

### Resume an Interrupted Scan
```bash
# If a scan was interrupted, simply run the same command again
# The scanner will automatically skip already-completed domains
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output --concurrent 10

# Check checkpoint status
cat output/checkpoint.json | jq '.completed_domains | length'
```

### Manual Checkpoint Management
```bash
# View checkpoint details
cat output/checkpoint.json | jq '.'

# Reset checkpoint to rescan all domains
rm output/checkpoint.json

# Keep checkpoint but clear results
rm -rf output/scan_results/*.json
```

## Advanced Batch Processing

### Memory Management for 15K+ Domains
```bash
# For very large batches (15,000+ domains)
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="32g" --cpus="8" \
  --shm-size="2g" \
  pixel-scanner:production \
  /app/input/mega_portfolio.csv /app/output \
  --concurrent 12 \
  --timeout 30000

# Monitor memory usage
docker stats pixel-scanner-batch
```

### Optimized Settings by Hardware

#### For 32GB Mac M3 Pro
```bash
--memory="24g" --cpus="10" --concurrent 15
```

#### For 16GB Corporate Laptop
```bash
--memory="12g" --cpus="4" --concurrent 5
```

#### For Cloud/Server (64GB+)
```bash
--memory="48g" --cpus="16" --concurrent 20
```

## Best Practices

1. **Always set resource limits** to prevent container from consuming all resources
2. **Use read-only mounts** for input files (`:ro`)
3. **Monitor first few domains** to ensure scanning works
4. **Save checkpoint regularly** (automatic every 10 domains)
5. **Use absolute paths** in production environments
6. **Test with small batches first** before running thousands of domains
7. **Keep logs for debugging** using `docker logs` command
8. **Prevent system sleep** for long scans:
   - **Mac**: Use `caffeinate -d` to prevent sleep
   - **Linux**: Use `systemd-inhibit` or `caffeine`
   - **Windows**: Use PowerToys Awake or adjust power settings

## Example Production Run

### For Large Portfolio (1700+ domains)
```bash
# 1. Prepare input
mkdir -p input output
cp /path/to/portfolio.csv input/

# 2. Build image
docker build -t pixel-scanner:production .

# 3. IMPORTANT: Prevent system sleep (for Mac)
# Run in separate terminal or use screen/tmux
caffeinate -d -i -m -s &
CAFFEINE_PID=$!

# 4. Run scan (2-3 hours for 1700 domains)
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

# 5. Stop caffeinate when done
kill $CAFFEINE_PID

# 6. Check results
ls -la output/
cat output/portfolio_results.csv | wc -l  # Count domains scanned
grep ",1," output/portfolio_results.csv | wc -l  # Count sites with pixels
```

#### Performance Notes
- **No screenshots**: production_scanner.py doesn't capture screenshots (faster)
- **2-3 hours for 1700 domains**: ~4-6 seconds per domain with concurrent=10
- **Adjust concurrency**: Increase to 15-20 if network/CPU allows
- **Timeout**: 30 seconds default is good for most sites

### Alternative: Run with caffeinate wrapper
```bash
# One-liner that prevents sleep during entire scan
caffeinate -d -i -m -s docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:production \
  /app/input/portfolio.csv /app/output \
  --concurrent 10
```