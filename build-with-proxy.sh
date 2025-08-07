#!/bin/bash
# Build script for corporate environments with proxy/firewall

echo "========================================="
echo "Docker Build Script for Corporate Proxy"
echo "========================================="

# Check if proxy is set
if [ -z "$HTTP_PROXY" ] && [ -z "$HTTPS_PROXY" ]; then
    echo "Warning: No proxy detected. Set HTTP_PROXY and HTTPS_PROXY if behind a firewall."
    echo "Example: export HTTP_PROXY=http://proxy.company.com:8080"
    echo ""
fi

# Display current proxy settings
echo "Current proxy settings:"
echo "  HTTP_PROXY: ${HTTP_PROXY:-not set}"
echo "  HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
echo "  NO_PROXY: ${NO_PROXY:-not set}"
echo ""

# Option 1: Standard build with proxy
echo "Option 1: Building with standard proxy settings..."
docker build \
  --build-arg HTTP_PROXY="${HTTP_PROXY}" \
  --build-arg HTTPS_PROXY="${HTTPS_PROXY}" \
  --build-arg NO_PROXY="${NO_PROXY}" \
  -t pixel-scanner:corporate \
  . || {
    echo ""
    echo "Standard build failed. Trying alternative approach..."
    echo ""
    
    # Option 2: Build with more aggressive proxy handling
    echo "Option 2: Trying alternative build approach..."
    # Try with network host mode which sometimes helps with proxy issues
    docker build \
      --network=host \
      --build-arg HTTP_PROXY="${HTTP_PROXY}" \
      --build-arg HTTPS_PROXY="${HTTPS_PROXY}" \
      --build-arg NO_PROXY="${NO_PROXY}" \
      -t pixel-scanner:corporate \
      . || {
        echo ""
        echo "Both build attempts failed."
        echo ""
        echo "Troubleshooting steps:"
        echo "1. Verify proxy settings: curl -I https://google.com"
        echo "2. Check Docker proxy config: ~/.docker/config.json"
        echo "3. Try manual build with --network=host"
        echo "4. Contact IT for proxy authentication details"
        exit 1
      }
}

echo ""
echo "Build successful!"
echo ""
echo "Examples:"
echo ""
echo "1. Scan a single domain:"
echo "   docker run --rm pixel-scanner:corporate scan google.com"
echo ""
echo "2. Scan multiple domains from a text file:"
echo "   # First create a file with domains (one per line)"
echo "   echo 'google.com' > domains.txt"
echo "   echo 'facebook.com' >> domains.txt"
echo "   "
echo "   # Then run the batch scan"
echo "   docker run --rm -v \$(pwd):/app/work pixel-scanner:corporate batch /app/work/domains.txt -o /app/work/output"
echo ""
echo "3. Scan from CSV file (with custom_id,url columns):"
echo "   # Create CSV file"
echo "   echo 'custom_id,url' > portfolio.csv"
echo "   echo 'COMP001,healthcare.com' >> portfolio.csv"
echo "   echo 'COMP002,hospital.org' >> portfolio.csv"
echo "   "
echo "   # Run batch scan"
echo "   docker run --rm -v \$(pwd):/app/work pixel-scanner:corporate batch /app/work/portfolio.csv -o /app/work/results"
echo ""
echo "Note: Results will be saved in the output directory as scan_results.csv"
echo "      CSV output includes: custom_id, url, domain, scan_status, has_pixel,"
echo "      pixel_count, pixel_names (pipe-separated), timestamp, duration_seconds, error"