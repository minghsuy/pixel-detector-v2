# Healthcare Pixel Scanning Workflow Guide

## Overview
This guide documents how to scan healthcare institutions for HIPAA-violating tracking pixels using the Pixel Detector tool.

## Step-by-Step Workflow

### 1. Prepare Institution List

Create a text file with domains (one per line):
```bash
# Create the list file
cat > healthcare_sites.txt << EOF
hospital1.org
hospital2.com
medicalcenter.edu/health
clinicnetwork.org
EOF
```

**Tips:**
- Use main domain only (tool adds https:// automatically)
- Include path for subdomains (e.g., `university.edu/medical-center`)
- Verify domains exist before scanning

### 2. Run the Batch Scan

```bash
# Basic scan
poetry run pixel-detector batch healthcare_sites.txt -o results/

# With specific options
poetry run pixel-detector batch healthcare_sites.txt \
  -o results/state_name/ \
  --timeout 60000 \
  --screenshot \
  --max-concurrent 10
```

**Timing:**
- ~2-3 seconds per site
- 10 sites = ~30 seconds total
- DNS pre-check skips dead domains

### 3. Handle Common Issues

**Bot Protection:**
- Sites like Mount Sinai use anti-bot measures
- Tool automatically retries with enhanced stealth
- May see "protection detected" messages (normal)

**Failed Scans:**
- Check domain spelling
- Try with/without www
- Some sites block all automated access

### 4. Analyze Results

The tool generates:
- `summary.json` - Overview of all scans
- `[domain].json` - Detailed results per site
- Console output with summary table

### 5. Generate Reports

Use the analysis script:
```bash
cd results/your_scan/
chmod +x run_analysis.sh
./run_analysis.sh
```

Or manually analyze:
```bash
# Count sites with tracking
jq '[.[] | select(.pixels_found > 0)] | length' summary.json

# List clean sites
jq -r '.[] | select(.success and .pixels_found == 0) | .domain' summary.json

# Show tracking types
jq -r '.[] | select(.pixels_found > 0) | .domain + ": " + (.pixel_types | join(", "))' summary.json
```

## Best Practices

### Domain Selection
1. **Start with main domains** - Homepage tracking indicates organization-wide practices
2. **Include diverse types** - Academic centers, public hospitals, private systems
3. **Verify current domains** - Healthcare mergers change domains frequently

### Scan Timing
- **Avoid peak hours** - Scan during off-peak for faster results
- **Batch appropriately** - 10-20 sites per batch optimal
- **Allow retries** - Some sites need multiple attempts

### Result Interpretation
- **Google Analytics = HIPAA violation** without BAA
- **No pixels on homepage ≠ fully compliant** (check patient portals)
- **Failed scans** may indicate strict security (good) or errors (retry)

## Sample Analysis Workflow

```bash
# 1. Setup
mkdir -p results/state_analysis
cd results/state_analysis

# 2. Create target list
echo "Researching top medical institutions..."
cat > targets.txt << EOF
majorhospital.org
university.edu/medical
regionalhealth.com
publichealth.gov
EOF

# 3. Run scan
echo "Starting privacy compliance scan..."
poetry run pixel-detector batch targets.txt -o .

# 4. Quick analysis
echo "=== RESULTS ==="
echo "Total scanned: $(jq length summary.json)"
echo "With tracking: $(jq '[.[] | select(.pixels_found > 0)] | length' summary.json)"
echo "Clean sites: $(jq '[.[] | select(.success and .pixels_found == 0)] | length' summary.json)"

# 5. Generate report
echo "=== VIOLATIONS ==="
jq -r '.[] | select(.pixels_found > 0) | "❌ " + .domain + ": " + (.pixel_types | join(", "))' summary.json
echo ""
echo "=== COMPLIANT ==="
jq -r '.[] | select(.success and .pixels_found == 0) | "✅ " + .domain' summary.json
```

## Automation Tips

### Scheduled Scans
```bash
# Add to crontab for monthly scans
0 2 1 * * cd /path/to/pixel-detector && poetry run pixel-detector batch /path/to/hospitals.txt -o /path/to/results/$(date +\%Y\%m)/
```

### CI/CD Integration
```yaml
# GitHub Action example
- name: Scan healthcare sites
  run: |
    poetry install
    poetry run playwright install chromium
    poetry run pixel-detector batch hospitals.txt -o results/
    
- name: Check compliance
  run: |
    violations=$(jq '[.[] | select(.pixels_found > 0)] | length' results/summary.json)
    if [ $violations -gt 0 ]; then
      echo "Found $violations HIPAA violations!"
      exit 1
    fi
```

## Performance Metrics

Based on NY healthcare scan:
- **Scan rate**: 2.3 seconds/site average
- **Success rate**: 80% (8/10 sites)
- **Detection rate**: 87.5% have violations
- **Data size**: ~4KB per site result
- **Total time**: 23 seconds for 10 sites

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "DNS lookup failed" | Verify domain exists, check spelling |
| "Bot protection detected" | Normal - tool handles automatically |
| Slow scans | Reduce concurrent limit, increase timeout |
| No results file | Check output directory permissions |
| Import errors | Run `poetry install` and `poetry run playwright install chromium` |

## Next Steps

1. **Regular monitoring** - Set up monthly scans
2. **Expand scope** - Include patient portals, appointment systems
3. **Share results** - Notify institutions of violations
4. **Track improvements** - Document compliance changes over time

---

*For more details, see the [Pixel Detector documentation](https://github.com/minghsuy/pixel-detector)*