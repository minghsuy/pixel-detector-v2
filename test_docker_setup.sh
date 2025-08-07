#!/bin/bash
# Comprehensive test script for Docker setup
# Tests all functionality including corporate proxy handling

echo "========================================="
echo "Pixel Detector Docker Test Suite"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    
    echo -e "${YELLOW}Testing:${NC} $test_name"
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Command: $command"
        ((TESTS_FAILED++))
    fi
    echo ""
}

echo "1. Testing Local CLI Installation"
echo "=================================="
run_test "CLI is installed" "which pixel-detector || poetry run which pixel-detector"
run_test "CLI version check" "pixel-detector --version || poetry run pixel-detector --version"
run_test "List detectors" "pixel-detector list-detectors || poetry run pixel-detector list-detectors"

echo "2. Testing Single Domain Scanning"
echo "=================================="
run_test "Scan google.com (should find pixels)" "poetry run pixel-detector scan google.com | grep -E 'google_analytics|google_ads'"
run_test "Scan mayo.edu (should be clean)" "poetry run pixel-detector scan mayo.edu | grep -E 'No tracking pixels|0 tracking'"

echo "3. Testing Batch Processing"
echo "==========================="
# Create test files
cat > test_domains.txt << EOF
google.com
facebook.com
mayo.edu
EOF

cat > test_portfolio.csv << EOF
custom_id,url
GOOGLE,google.com
META,facebook.com
MAYO,mayo.edu
EOF

run_test "Batch TXT file" "poetry run pixel-detector batch test_domains.txt -o test_output_txt --max-concurrent 2"
run_test "Batch CSV file" "poetry run pixel-detector batch test_portfolio.csv -o test_output_csv --max-concurrent 2"
run_test "CSV output exists" "test -f test_output_csv/scan_results.csv"
run_test "CSV has correct columns" "head -1 test_output_csv/scan_results.csv | grep -q 'custom_id,url,domain,scan_status'"

echo "4. Testing Docker Build"
echo "======================="
if [ -n "$HTTP_PROXY" ]; then
    echo -e "${YELLOW}Corporate proxy detected: $HTTP_PROXY${NC}"
    run_test "Docker build with proxy" "./build-with-proxy.sh"
else
    run_test "Docker build" "docker build -t pixel-scanner:test ."
fi

echo "5. Testing Docker Commands"
echo "=========================="
if docker images | grep -q pixel-scanner; then
    run_test "Docker single domain scan" "docker run --rm pixel-scanner:test scan google.com"
    run_test "Docker help command" "docker run --rm pixel-scanner:test --help"
    
    # Test batch with volume mounts
    mkdir -p docker_test_input docker_test_output
    cp test_domains.txt docker_test_input/
    cp test_portfolio.csv docker_test_input/
    
    run_test "Docker batch TXT" "docker run --rm -v $(pwd)/docker_test_input:/input -v $(pwd)/docker_test_output:/output pixel-scanner:test batch /input/test_domains.txt -o /output"
    run_test "Docker batch CSV" "docker run --rm -v $(pwd)/docker_test_input:/input -v $(pwd)/docker_test_output:/output pixel-scanner:test batch /input/test_portfolio.csv -o /output"
else
    echo -e "${YELLOW}Skipping Docker tests - image not built${NC}"
fi

echo "6. Verifying Pixel Detection"
echo "============================"
if [ -f test_output_csv/scan_results.csv ]; then
    echo "Checking detection accuracy:"
    
    if grep -q "GOOGLE.*google_analytics\|google_ads" test_output_csv/scan_results.csv; then
        echo -e "${GREEN}✓ Google Analytics/Ads detected on google.com${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Failed to detect Google pixels${NC}"
        ((TESTS_FAILED++))
    fi
    
    if grep -q "META.*meta_pixel" test_output_csv/scan_results.csv; then
        echo -e "${GREEN}✓ Meta Pixel detected on facebook.com${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Failed to detect Meta pixel${NC}"
        ((TESTS_FAILED++))
    fi
    
    if grep -q "MAYO.*,0,0,," test_output_csv/scan_results.csv; then
        echo -e "${GREEN}✓ Mayo.edu correctly shown as clean${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Mayo.edu not correctly identified as clean${NC}"
        ((TESTS_FAILED++))
    fi
fi

echo ""
echo "========================================="
echo "Test Results"
echo "========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! The setup is working correctly.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. For single scans: pixel-detector scan domain.com"
    echo "2. For batch CSV: pixel-detector batch portfolio.csv -o results/"
    echo "3. For Docker: docker run --rm pixel-scanner scan domain.com"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please check the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. For proxy issues: export HTTP_PROXY=http://your-proxy:port"
    echo "2. For Docker issues: ./build-with-proxy.sh"
    echo "3. For CLI issues: poetry install && poetry run playwright install chromium"
    exit 1
fi