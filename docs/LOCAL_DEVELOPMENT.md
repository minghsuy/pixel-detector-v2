# Local Docker Development Guide

## Prerequisites

1. **Docker Desktop for Mac** (Apple Silicon/Intel)
   - Download from: https://www.docker.com/products/docker-desktop/
   - Allocate resources: Docker Desktop → Settings → Resources
     - CPUs: 4-8 cores (based on your hardware)
     - Memory: 8-16GB
     - Disk: 50GB+

2. **VSCode Extensions** (Recommended)
   - Docker (by Microsoft)
   - Dev Containers (by Microsoft)
   - Python (by Microsoft)

## Quick Start (5 Minutes)

### 1. Clone and Open in VSCode
```bash
git clone <your-repo>
cd pixel-detector-v2
code .
```

### 2. Build the Docker Image
Open VSCode terminal (``Cmd+` ``) and run:
```bash
# Build the production scanner image
docker build -t pixel-scanner:local .
```

### 3. Prepare Test Data
```bash
# Create directories
mkdir -p docker-input docker-results docker-screenshots

# Create a test file with sample domains
cat > docker-input/test_domains.txt << EOF
google.com
stanford.edu
mayo.edu
cdc.gov
badensports.com
EOF
```

### 4. Run Quick Test
```bash
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/output:rw \
  --memory="8g" --cpus="4" \
  pixel-scanner:local \
  /app/input/test_domains.txt /app/output --concurrent 5
```

## VSCode Docker Integration

### Using Docker Extension

1. **View Images**: Click Docker icon in sidebar → Images → `pixel-scanner:local`
2. **Run Container**: Right-click image → Run Interactive
3. **View Logs**: Docker sidebar → Containers → Right-click → View Logs
4. **Shell Access**: Right-click container → Attach Shell

### Using Tasks (Automated Workflow)

Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Build Docker Image",
      "type": "shell",
      "command": "docker build -t pixel-scanner:local .",
      "group": "build",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Run Quick Scan",
      "type": "shell",
      "command": "docker run --rm -v $(pwd)/docker-input:/app/input:ro -v $(pwd)/docker-results:/app/output:rw --memory='8g' --cpus='4' pixel-scanner:local /app/input/test_domains.txt /app/output --concurrent 5",
      "dependsOn": ["Build Docker Image"],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "View Results",
      "type": "shell",
      "command": "cat docker-results/scan_results.csv | head -20",
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

Now use: `Cmd+Shift+P` → "Tasks: Run Task" → Select task

## Running Large Portfolio Analysis

### 1. Prepare Your Domain List
```bash
# Copy your domains file
cp /path/to/portfolio_domains.txt docker-input/domains.txt

# Or create a test file
cat > docker-input/test_portfolio.txt << EOF
example.com
google.com
facebook.com
amazon.com
apple.com
EOF
```

### 2. Run with Progress Monitoring

Create `run_portfolio_scan.sh`:
```bash
#!/bin/bash
# Portfolio scanning script with progress monitoring

DOMAINS_FILE="docker-input/domains.txt"
OUTPUT_DIR="docker-results-$(date +%Y%m%d-%H%M%S)"

echo "Starting portfolio scan..."
echo "Domains: $(wc -l < $DOMAINS_FILE)"
echo "Output: $OUTPUT_DIR"

# Create output directory
mkdir -p $OUTPUT_DIR

# Run scan with real-time monitoring
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/$OUTPUT_DIR:/app/results:rw \
  -v $(pwd)/docker-screenshots:/app/screenshots:rw \
  --memory="16g" --cpus="6" \
  --name portfolio-scan \
  pixel-scanner:local \
  batch /app/input/domains.txt -o /app/results \
  --screenshot \
  --max-concurrent 5 \
  --timeout 30000 &

# Monitor progress in separate terminal
CONTAINER_ID=$(docker ps -q -f name=portfolio-scan)
docker logs -f $CONTAINER_ID
```

Make executable and run:
```bash
chmod +x run_portfolio_scan.sh
./run_portfolio_scan.sh
```

### 3. Monitor in VSCode

**Option 1: Split Terminal**
- `Cmd+\` to split terminal
- Left: Run scan
- Right: `watch -n 5 'ls -la docker-results/ | tail -20'`

**Option 2: Docker Extension**
- Click Docker icon → Containers → portfolio-scan → View Logs
- Real-time log streaming in VSCode

**Option 3: Results Preview**
Create `.vscode/settings.json`:
```json
{
  "files.associations": {
    "docker-results/*.json": "json"
  },
  "json.schemas": [
    {
      "fileMatch": ["docker-results/summary.json"],
      "url": "./schemas/summary-schema.json"
    }
  ]
}
```

## Performance Tips for M3 Pro

### 1. Optimize Docker Settings
```bash
# Check current limits
docker info | grep -E "CPUs|Memory"

# Run with M3 Pro optimized settings
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/results:rw \
  --memory="16g" \
  --cpus="8" \
  --platform linux/arm64 \
  pixel-scanner:local \
  batch /app/input/domains.txt -o /app/results \
  --max-concurrent 8
```

### 2. Batch Processing for Large Portfolios
```bash
# Split large files
split -l 500 docker-input/domains.txt docker-input/batch_

# Process batches
for batch in docker-input/batch_*; do
  echo "Processing $batch..."
  docker run --rm \
    -v $(pwd)/$batch:/app/input/domains.txt:ro \
    -v $(pwd)/docker-results:/app/results:rw \
    pixel-scanner:local \
    batch /app/input/domains.txt -o /app/results
done
```

## Debugging in VSCode

### 1. Interactive Container
```bash
# Start container with shell
docker run -it --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-results:/app/results:rw \
  --entrypoint /bin/bash \
  pixel-scanner:local

# Inside container, test commands
python -m pixel_detector scan example.com
```

### 2. VSCode Debugger
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Docker: Python",
      "type": "docker",
      "request": "launch",
      "preLaunchTask": "docker-build",
      "python": {
        "pathMappings": [
          {
            "localRoot": "${workspaceFolder}/src",
            "remoteRoot": "/app/src"
          }
        ],
        "projectType": "general"
      }
    }
  ]
}
```

## Expected Performance

On MacBook Pro M3 Pro:
- **10 sites**: ~2-3 minutes
- **100 sites**: ~20-30 minutes  
- **1,000 sites**: ~3-4 hours
- **Large portfolios**: ~1-2 sites/second with 5-8 concurrent

## Troubleshooting

### Common Issues

1. **"Cannot connect to Docker daemon"**
   ```bash
   # Ensure Docker Desktop is running
   open -a Docker
   ```

2. **"No space left on device"**
   ```bash
   # Clean up Docker
   docker system prune -a
   ```

3. **"Permission denied on results"**
   ```bash
   # Fix permissions
   chmod -R 755 docker-results docker-screenshots
   ```

4. **Slow performance**
   - Increase Docker Desktop resources
   - Reduce `--max-concurrent` to 3-5
   - Check Activity Monitor for CPU/Memory

## VSCode Shortcuts

- `Cmd+Shift+P` → "Docker: Build Image"
- `Cmd+J` → Toggle terminal
- `Cmd+\` → Split terminal
- `F5` → Start debugging
- `Cmd+K Cmd+0` → Collapse all folders

## Next Steps

1. Test with 10-site sample ✓
2. Run 100-site validation
3. Process full portfolio
4. Review results in `docker-results/summary.json`
5. Deploy to Fargate for production scale

Happy scanning! 🚀