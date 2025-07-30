# Testing Guide for Pixel Detector

## Overview

This guide covers the testing infrastructure, patterns, and best practices for the Pixel Detector project. The test suite uses pytest with async support, mock fixtures for Playwright, and achieves 91% code coverage.

## Table of Contents
1. [Test Setup](#test-setup)
2. [Running Tests](#running-tests)
3. [Test Organization](#test-organization)
4. [Testing Patterns](#testing-patterns)
5. [Mock Fixtures](#mock-fixtures)
6. [Common Issues & Solutions](#common-issues--solutions)
7. [Coverage Goals](#coverage-goals)

## Test Setup

### Prerequisites
```bash
# Install development dependencies
poetry install --with dev

# Install Playwright browsers (for integration tests)
poetry run playwright install chromium
```

### Key Testing Dependencies
- **pytest**: Core testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Enhanced mocking utilities

## Running Tests

### Basic Commands
```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_cli.py

# Run specific test
poetry run pytest tests/test_cli.py::TestCLI::test_scan_command_basic -v -s
```

### Useful Pytest Options
- `-v`: Verbose output
- `-s`: Show print statements
- `-x`: Stop on first failure
- `-k "pattern"`: Run tests matching pattern
- `--lf`: Run last failed tests
- `--ff`: Run failed tests first

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_models.py           # Model tests (100% coverage)
├── test_detectors_base.py   # Base detector class tests
├── test_detectors_all.py    # All 8 detector implementations
├── test_cli.py             # CLI command tests
├── test_scanner.py         # Scanner integration tests
└── test_scanner_simple.py  # Simplified scanner unit tests
```

### Test Naming Conventions
- Test files: `test_*.py`
- Test classes: `TestClassName`
- Test methods: `test_method_name_describes_behavior`

## Testing Patterns

### 1. Detector Testing Pattern

```python
class TestMetaPixelDetector:
    def test_properties(self):
        """Test detector properties."""
        detector = MetaPixelDetector()
        assert detector.pixel_type == PixelType.META_PIXEL
        assert "facebook.com" in detector.tracking_domains
        assert "_fbp" in detector.cookie_names
    
    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test network request detection."""
        detector = MetaPixelDetector()
        request = Mock()
        request.url = "https://www.facebook.com/tr?id=123"
        
        result = await detector.check_request(request)
        assert result is True
        assert "123" in detector.pixel_ids
```

### 2. CLI Testing Pattern

```python
def test_scan_command(runner, mock_scan_result):
    """Test scan command."""
    with runner.isolated_filesystem():
        # Use isolated filesystem for file operations
        result = runner.invoke(app, ["scan", "example.com"])
        assert result.exit_code == 0
        assert "Scan Results" in result.stdout
```

### 3. Async Testing Pattern

```python
@pytest.mark.asyncio
async def test_async_method():
    """Test async functionality."""
    scanner = PixelScanner()
    mock_page = AsyncMock(spec=Page)
    mock_page.goto.return_value = None
    
    # Test async method
    await scanner.some_async_method(mock_page)
```

### 4. Mock Testing Pattern

```python
@patch('pixel_detector.scanner.async_playwright')
async def test_browser_setup(mock_playwright):
    """Test browser setup with mocks."""
    mock_pw = AsyncMock()
    mock_playwright.return_value.__aenter__.return_value = mock_pw
    
    scanner = PixelScanner()
    browser, context = await scanner._setup_browser()
```

## Mock Fixtures

### Key Fixtures in conftest.py

#### 1. Mock Playwright Objects
```python
@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mock Playwright Page object."""
    page = create_autospec(Page, spec_set=True)
    page.url = "https://example.com"
    page.goto = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value={})
    return page
```

#### 2. Sample HTML Content
```python
@pytest.fixture
def meta_pixel_html() -> str:
    """HTML content with Meta Pixel tracking."""
    return """
    <script>
        fbq('init', '1234567890');
        fbq('track', 'PageView');
    </script>
    """
```

#### 3. Sample Data Models
```python
@pytest.fixture
def mock_scan_result():
    """Create a mock scan result."""
    return ScanResult(
        domain="https://example.com",
        url_scanned="https://example.com",
        timestamp=datetime.utcnow(),
        pixels_detected=[...],
        scan_metadata=ScanMetadata(...),
        success=True
    )
```

## Common Issues & Solutions

### 1. Import Errors
**Problem**: `ImportError: cannot import name 'Model' from 'pixel_detector.models'`
**Solution**: Models are in submodules:
```python
# Wrong
from pixel_detector.models import PixelType

# Correct
from pixel_detector.models.pixel_detection import PixelType
```

### 2. Async Test Failures
**Problem**: `RuntimeError: This event loop is already running`
**Solution**: Use `pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_async_function():
    # test code
```

### 3. Mock Attribute Errors
**Problem**: `AttributeError: 'Mock' object has no attribute 'goto'`
**Solution**: Use `AsyncMock` for async methods:
```python
mock_page = AsyncMock(spec=Page)
mock_page.goto = AsyncMock(return_value=None)
```

### 4. Typer CLI Test Issues
**Problem**: File paths don't work in typer test runner
**Solution**: Use `runner.isolated_filesystem()`:
```python
def test_batch_command(runner):
    with runner.isolated_filesystem():
        with open("input.txt", "w") as f:
            f.write("example.com")
        result = runner.invoke(app, ["batch", "input.txt"])
```

### 5. Model Field Mismatches
**Problem**: Tests fail with `unexpected keyword argument 'error'`
**Solution**: Check actual model field names:
```python
# Wrong
ScanResult(..., error="message")

# Correct  
ScanResult(..., error_message="message")
```

## Coverage Goals

### Current Coverage (91%) ✅
- **Models**: 100% ✅
- **CLI**: 96% ✅
- **Detectors**: 78-100% ✅
- **Scanner**: 86% ✅
- **Base classes**: 89-91% ✅
- **Registry**: 95-100% ✅

### Target Coverage (80%+) - EXCEEDED!
We've successfully exceeded our target coverage of 80%, achieving 91% overall coverage.

Remaining areas for potential improvement:
1. End-to-end tests with real site simulation
2. Performance benchmarks
3. Edge cases in detectors (LinkedIn, Pinterest, Twitter)
4. Scanner screenshot functionality testing

### Coverage Commands
```bash
# View coverage report
poetry run pytest --cov=src --cov-report=term-missing

# Generate HTML report
poetry run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Check specific module coverage
poetry run pytest --cov=src.pixel_detector.scanner --cov-report=term
```

## Best Practices

### 1. Test Independence
- Each test should be independent
- Use fixtures for shared setup
- Clean up resources in teardown

### 2. Mock External Dependencies
- Mock Playwright browser operations
- Mock network requests
- Mock file system operations when possible

### 3. Test Both Success and Failure
```python
async def test_scan_success():
    # Test successful scan
    
async def test_scan_network_error():
    # Test network failure handling
    
async def test_scan_timeout():
    # Test timeout handling
```

### 4. Use Descriptive Test Names
```python
# Bad
def test_scan():
    pass

# Good
def test_scan_domain_with_meta_pixel_detection():
    pass
```

### 5. Fixture Reuse
- Define common fixtures in conftest.py
- Use fixture composition for complex scenarios
- Keep fixtures focused and simple

## Debugging Tests

### 1. Run Single Test with Output
```bash
poetry run pytest tests/test_cli.py::TestCLI::test_scan_command -v -s
```

### 2. Use pytest.set_trace()
```python
def test_something():
    # ... setup code ...
    import pytest; pytest.set_trace()  # Debugger breakpoint
    # ... test code ...
```

### 3. Check Mock Calls
```python
# Verify mock was called
mock_scanner.scan_domain.assert_called_once()

# Check call arguments
mock_scanner.scan_domain.assert_called_with("example.com")

# View all calls
print(mock_scanner.scan_domain.call_args_list)
```

### 4. Examine Coverage Gaps
```bash
# Generate detailed HTML report
poetry run pytest --cov=src --cov-report=html

# Look for red lines in htmlcov/index.html
```

## Contributing Tests

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests cover both success and error cases
3. Add appropriate fixtures to conftest.py
4. Update this documentation if adding new patterns
5. Maintain or improve overall coverage

### Test Review Checklist
- [ ] Tests are independent and repeatable
- [ ] Async tests use proper decorators
- [ ] Mocks are properly configured
- [ ] Both success and failure paths tested
- [ ] Coverage maintained or improved
- [ ] No hardcoded paths or values
- [ ] Clear test names and documentation