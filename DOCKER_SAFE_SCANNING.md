# Docker Safe Scanning Guide for 15K Domains

Run pixel-detector safely in Docker while preserving all outputs (JSONs, screenshots, summaries).

## Pre-Flight Testing (Recommended)

Before running 15K domains, test with smaller batches to verify everything works correctly.

### Generate Test Healthcare Sites
```bash
# Create test files with top healthcare websites
python scripts/get_top_healthcare_sites.py

# This creates:
# - healthcare_quick_test.txt (10 sites for 5-minute test)
# - healthcare_test_100.txt (100 sites for 30-60 minute test)
```

### Run Quick Test (10 sites, ~5 minutes)
```bash
# Prepare test input
mkdir -p docker-input docker-results docker-screenshots
cp healthcare_quick_test.txt docker-input/

# Run quick test
docker run --rm -it \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results-test:/app/results:rw \
  -v $(pwd)/docker-screenshots-test:/app/screenshots:rw \
  --memory="8g" --cpus="4" \
  --name pixel-test-quick \
  pixel-scanner:safe \
  batch /app/input/healthcare_quick_test.txt -o /app/results --screenshot

# Verify outputs
ls -la docker-results-test/    # Should see 10 JSON files + summary.json
ls -la docker-screenshots-test/ # Should see screenshots for sites with pixels
```

### Run Full Test (100 sites, ~30-60 minutes)
```bash
# Copy larger test file
cp healthcare_test_100.txt docker-input/

# Run full test with production settings
docker run --rm -it \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results-test100:/app/results:rw \
  -v $(pwd)/docker-screenshots-test100:/app/screenshots:rw \
  --memory="16g" --cpus="6" \
  --name pixel-test-100 \
  pixel-scanner:safe \
  batch /app/input/healthcare_test_100.txt -o /app/results --screenshot --max-concurrent 5

# Check performance metrics
echo "Results count: $(ls docker-results-test100/*.json | wc -l)"
echo "Screenshots: $(ls docker-screenshots-test100/*.png 2>/dev/null | wc -l)"
```

### What to Verify Before 15K Run:
- ✅ All domains produce JSON output files
- ✅ Screenshots are captured when pixels detected
- ✅ Summary.json is generated correctly
- ✅ Memory usage stays within limits (check with `docker stats`)
- ✅ Scan rate is acceptable (domains/minute)
- ✅ No permission errors on output directories

## Quick Start (TL;DR) - After Testing

```bash
# 1. Create directories
mkdir -p docker-input docker-results docker-screenshots

# 2. Copy your domains file
cp your_15k_domains.txt docker-input/domains.txt

# 3. Run the scan
docker run --rm -it \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/results:rw \
  -v $(pwd)/docker-screenshots:/app/screenshots:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:safe \
  pixel-detector batch /app/input/domains.txt -o /app/results --screenshot -s /app/screenshots --max-concurrent 5
```

## Detailed Setup

### Step 1: Create Secure Dockerfile

Create `Dockerfile.safe`:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.53.0-noble

# Create non-root user for security
RUN groupadd -r scanner && useradd -r -g scanner -m scanner

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry==2.1.3 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy application
COPY src/ ./src/

# Create output directories
RUN mkdir -p /app/results /app/screenshots /app/logs /app/input && \
    chown -R scanner:scanner /app

# Switch to non-root user
USER scanner

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "pixel_detector"]
```

### Step 2: Build the Image

```bash
docker build -f Dockerfile.safe -t pixel-scanner:safe .
```

### Step 3: Prepare Directory Structure

```bash
# Create local directories that will receive the output
mkdir -p docker-input docker-results docker-screenshots docker-logs

# Copy your domains file
cp your_15k_domains.txt docker-input/domains.txt
```

### Step 4: Run the Full Batch Scan

```bash
docker run --rm -it \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/results:rw \
  -v $(pwd)/docker-screenshots:/app/screenshots:rw \
  -v $(pwd)/docker-logs:/app/logs:rw \
  --memory="16g" \
  --cpus="6" \
  --name pixel-scan-15k \
  pixel-scanner:safe \
  batch /app/input/domains.txt \
    --output-dir /app/results \
    --screenshot \
    --max-concurrent 5 \
    --timeout 30000
```

## What Gets Saved Where

Your local directories will contain:

```
docker-results/
├── example_com.json          # Individual scan result with pixel details
├── another_site_org.json     # Another domain's results
├── summary.json              # Summary of all domains scanned
└── ... (one JSON per domain)

docker-screenshots/
├── example_com_1737744123.png    # Screenshot if pixel detected
├── another_site_1737744156.png   # Another screenshot
└── ... (only for sites with pixels)

docker-logs/
└── pixel_detector.log        # Detailed scan logs
```

## Monitoring Progress

### Option 1: Watch Container Logs
```bash
# In another terminal
docker logs -f pixel-scan-15k
```

### Option 2: Monitor Output Directory
```bash
# Watch results being created
watch -n 5 'ls -la docker-results/ | tail -20'

# Check current summary
watch -n 10 'cat docker-results/summary.json | jq ".[-5:]"'
```

### Option 3: VSCode Docker Extension
1. Open Docker extension sidebar
2. Find `pixel-scan-15k` container
3. Right-click → "View Logs"

## Extract Final Results to CSV

Create `extract_to_csv.py`:

```python
#!/usr/bin/env python3
import json
import csv
from pathlib import Path

def extract_results(results_dir="docker-results", output_csv="scan_results.csv"):
    """Extract all scan results to CSV with pixel details"""
    
    results_path = Path(results_dir)
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'domain', 'timestamp', 'scan_status', 'error_message',
            'pixels_detected_count', 'pixel_types', 'pixel_ids', 
            'risk_levels', 'hipaa_concerns', 'screenshot_path',
            'page_load_time', 'total_requests', 'tracking_requests'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each domain's JSON
        for json_file in results_path.glob("*.json"):
            if json_file.name == "summary.json":
                continue
                
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Extract pixel information
                pixel_types = []
                pixel_ids = []
                risk_levels = []
                hipaa_concerns = []
                
                for pixel in data.get('pixels_detected', []):
                    pixel_types.append(pixel.get('type', 'unknown'))
                    pixel_ids.append(pixel.get('pixel_id', 'N/A'))
                    risk_levels.append(pixel.get('risk_level', 'unknown'))
                    hipaa_concerns.append(str(pixel.get('hipaa_concern', False)))
                
                # Write row
                writer.writerow({
                    'domain': data.get('domain'),
                    'timestamp': data.get('timestamp'),
                    'scan_status': 'success' if data.get('success', False) else 'failed',
                    'error_message': data.get('error_message', ''),
                    'pixels_detected_count': len(data.get('pixels_detected', [])),
                    'pixel_types': '|'.join(pixel_types) if pixel_types else 'none',
                    'pixel_ids': '|'.join(pixel_ids) if pixel_ids else 'none',
                    'risk_levels': '|'.join(risk_levels) if risk_levels else 'none',
                    'hipaa_concerns': '|'.join(hipaa_concerns) if hipaa_concerns else 'none',
                    'screenshot_path': data.get('screenshot_path', ''),
                    'page_load_time': data.get('scan_metadata', {}).get('page_load_time', 0),
                    'total_requests': data.get('scan_metadata', {}).get('total_requests', 0),
                    'tracking_requests': data.get('scan_metadata', {}).get('tracking_requests', 0)
                })
                
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
    
    print(f"✅ Extracted {len(list(results_path.glob('*.json')) - 1)} results to {output_csv}")

if __name__ == "__main__":
    extract_results()
```

Run it after scan:
```bash
python extract_to_csv.py
```

## Handling 15K Domains Efficiently

### With Checkpointing (Recommended)

If you need resume capability, use the batch_manager approach:

```bash
# First, add batch_manager.py to the Docker image
docker run --rm -it \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/results:rw \
  -v $(pwd)/batch_manager.py:/app/batch_manager.py:ro \
  --memory="16g" --cpus="6" \
  pixel-scanner:safe \
  python /app/batch_manager.py /app/input/domains.txt client_15k
```

### Memory Management

For 15K domains, process in chunks to avoid memory issues:

```bash
# Split your input file
split -l 1000 docker-input/domains.txt docker-input/chunk_

# Run each chunk
for chunk in docker-input/chunk_*; do
  docker run --rm -it \
    -v $(pwd)/$chunk:/app/input/domains.txt:ro \
    -v $(pwd)/docker-results:/app/results:rw \
    -v $(pwd)/docker-screenshots:/app/screenshots:rw \
    --memory="16g" --cpus="6" \
    pixel-scanner:safe \
    batch /app/input/domains.txt -o /app/results --screenshot
done
```

## Performance Tips for 32GB Mac

1. **Optimal Settings**:
   - `--max-concurrent 5` (5 parallel scans)
   - `--memory="16g"` (leave 16GB for system)
   - `--cpus="6"` (use 6 of your cores)

2. **Expected Timeline**:
   - Quick test: 10 domains × 20 sec ÷ 5 concurrent = ~1 minute
   - Full test: 100 domains × 20 sec ÷ 5 concurrent = ~7 minutes
   - Production: 15K domains × 20 sec ÷ 5 concurrent = ~17 hours

3. **Prevent Sleep**:
   ```bash
   caffeinate -d docker run ... (your full command)
   ```

## Troubleshooting

### If Quick Test Fails:
1. **Check Docker resources**: Docker Desktop → Settings → Resources
2. **Verify file permissions**: `ls -la docker-*` 
3. **Check Docker logs**: `docker logs pixel-test-quick`
4. **Ensure Playwright installed**: Rebuild with `docker build --no-cache`

### Common Issues:
- **"Permission denied"**: Run `chmod -R 755 docker-results docker-screenshots`
- **"No space left"**: Check Docker disk usage: `docker system df`
- **"Out of memory"**: Reduce `--max-concurrent` or `--memory` settings
- **"Timeout errors"**: Increase timeout: `--timeout 60000`

## Quick Reference

```bash
# Build
docker build -f Dockerfile.safe -t pixel-scanner:safe .

# Run full scan with screenshots
docker run --rm -it \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/results:rw \
  -v $(pwd)/docker-screenshots:/app/screenshots:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:safe \
  batch /app/input/domains.txt -o /app/results --screenshot --max-concurrent 5

# Extract to CSV
python extract_to_csv.py

# Check results
ls -la docker-results/ | wc -l  # Count of domains scanned
ls -la docker-screenshots/       # Screenshots taken
cat docker-results/summary.json  # View summary
```

All your outputs (JSON files, screenshots, summary) will be safely stored in your local `docker-results/` and `docker-screenshots/` directories!