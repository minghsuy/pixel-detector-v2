# Docker Batch Processing with Checkpoint/Resume

## Overview
When running large batch scans in Docker, you need to persist checkpoint data between runs to enable resume functionality.

## Quick Start with Checkpointing

### 1. Create Persistent Volumes
```bash
# Create directories that will persist between Docker runs
mkdir -p docker-input docker-checkpoints docker-results docker-logs
```

### 2. Prepare Your Domain List
```bash
# Copy your domains file
cp your_domains.txt docker-input/domains.txt
```

### 3. Run Initial Batch Scan with Checkpoint
```bash
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-checkpoints:/app/checkpoints:rw \
  -v $(pwd)/docker-results:/app/results:rw \
  --memory="16g" --cpus="6" \
  --name batch-scan \
  pixel-scanner:safe \
  python -m pixel_detector.batch_manager \
    /app/input/domains.txt \
    my_batch_name \
    --results-dir /app/checkpoints
```

### 4. If Scan Interrupts, Resume Automatically
```bash
# Run exact same command - it will auto-resume!
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-checkpoints:/app/checkpoints:rw \
  -v $(pwd)/docker-results:/app/results:rw \
  --memory="16g" --cpus="6" \
  --name batch-scan \
  pixel-scanner:safe \
  python -m pixel_detector.batch_manager \
    /app/input/domains.txt \
    my_batch_name \
    --results-dir /app/checkpoints
```

## Checkpoint Files Location

Your checkpoint data will be in:
```
docker-checkpoints/
├── my_batch_name_progress.json    # Checkpoint file
└── my_batch_name/                 # Individual scan results
    ├── domain1_com.json
    ├── domain2_com.json
    └── ...
```

## Monitor Progress (From Host)

### Option 1: Check Progress File
```bash
# View progress summary
cat docker-checkpoints/my_batch_name_progress.json | jq '.'

# See completion percentage
cat docker-checkpoints/my_batch_name_progress.json | jq '.completed | length as $done | .total as $total | "\($done)/\($total) (\($done * 100 / $total)%)"'
```

### Option 2: Run Monitor in Another Container
```bash
# In a new terminal
docker run --rm -it \
  -v $(pwd)/docker-checkpoints:/app/checkpoints:ro \
  pixel-scanner:safe \
  python /app/monitor_scan.py my_batch_name
```

## Advanced: Custom Batch Script

Create `run_batch.sh`:
```bash
#!/bin/bash
BATCH_NAME="portfolio_$(date +%Y%m%d_%H%M%S)"
DOMAINS_FILE="docker-input/domains.txt"

echo "Starting batch: $BATCH_NAME"
echo "Domains file: $DOMAINS_FILE"
echo "Total domains: $(wc -l < $DOMAINS_FILE)"

# Run with checkpoint support
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-checkpoints:/app/checkpoints:rw \
  -v $(pwd)/docker-results:/app/results:rw \
  -v $(pwd)/docker-logs:/app/logs:rw \
  --memory="16g" --cpus="6" \
  --name "batch-$BATCH_NAME" \
  pixel-scanner:safe \
  python -m pixel_detector.batch_manager \
    /app/input/domains.txt \
    "$BATCH_NAME" \
    --results-dir /app/checkpoints \
    --max-concurrent 5

# Check if completed
if [ $? -eq 0 ]; then
  echo "✅ Batch completed successfully!"
  echo "Results in: docker-checkpoints/$BATCH_NAME/"
else
  echo "⚠️  Batch interrupted. To resume, run:"
  echo "./run_batch.sh"
fi
```

## Force Fresh Start (Ignore Checkpoint)
```bash
# Add --no-resume flag
docker run --rm \
  -v $(pwd)/docker-input:/app/input:ro \
  -v $(pwd)/docker-checkpoints:/app/checkpoints:rw \
  -v $(pwd)/docker-results:/app/results:rw \
  --memory="16g" --cpus="6" \
  pixel-scanner:safe \
  python -m pixel_detector.batch_manager \
    /app/input/domains.txt \
    my_batch_name \
    --results-dir /app/checkpoints \
    --no-resume
```

## Extract Results After Completion
```bash
# Copy all JSON results to final directory
cp docker-checkpoints/my_batch_name/*.json docker-results/

# Generate summary
cat docker-checkpoints/my_batch_name_progress.json | jq '{
  total: .total,
  completed: .completed | length,
  failed: .failed | length,
  success_rate: ((.completed | length) / .total * 100),
  elapsed_hours: .elapsed_hours
}'
```

## Key Points

1. **Volume Mounts are Critical**
   - `/app/checkpoints` must be mounted to persist progress
   - Use `:rw` for write access

2. **Same Batch Name = Auto Resume**
   - Always use the same batch name to resume
   - Different name = fresh start

3. **Checkpoint Every 50 Domains**
   - Default saves progress every 50 successful scans
   - Minimal data loss if interrupted

4. **Graceful Shutdown**
   - Use `docker stop` (not `docker kill`)
   - Gives time to save final checkpoint

## Troubleshooting

### "Permission Denied" on Checkpoint Files
```bash
# Fix permissions
chmod -R 755 docker-checkpoints
```

### Check What's in Progress
```bash
# See remaining domains
cat docker-checkpoints/my_batch_name_progress.json | jq '.remaining | length'

# See failed domains
cat docker-checkpoints/my_batch_name_progress.json | jq '.failed'
```

### Resume Not Working?
1. Check batch name matches exactly
2. Verify checkpoint file exists
3. Ensure volume mount is correct (`-v` flag)