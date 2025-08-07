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
    
    # Option 2: Build with SSL verification disabled
    echo "Option 2: Building with relaxed SSL (for testing only)..."
    docker build \
      --build-arg HTTP_PROXY="${HTTP_PROXY}" \
      --build-arg HTTPS_PROXY="${HTTPS_PROXY}" \
      --build-arg NO_PROXY="${NO_PROXY}" \
      --build-arg NODE_TLS_REJECT_UNAUTHORIZED=0 \
      --build-arg PYTHONHTTPSVERIFY=0 \
      --build-arg REQUESTS_CA_BUNDLE="" \
      --build-arg CURL_CA_BUNDLE="" \
      -t pixel-scanner:corporate-nossl \
      -f Dockerfile.corporate \
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
echo "To run the scanner:"
echo "  docker run --rm pixel-scanner:corporate scan google.com"
echo ""
echo "For batch processing:"
echo "  docker run --rm -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output \\"
echo "    pixel-scanner:corporate batch /app/input/domains.txt -o /app/output"