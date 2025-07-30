# Test Fixtures Reference

This document provides detailed information about the test fixtures defined in `tests/conftest.py`.

## Overview

The `conftest.py` file contains shared pytest fixtures used across the test suite. These fixtures provide:
- Mock Playwright objects (Browser, Page, Request, etc.)
- Sample HTML content for each pixel type
- Mock data models
- Utility fixtures for testing

## Mock Object Fixtures

### Browser Automation Mocks

#### `mock_request()`
```python
@pytest.fixture
def mock_request() -> Mock:
    """Create a mock Playwright Request object."""
```
**Usage**: Testing network request interception
**Returns**: Mock Request with url, method, resource_type, headers

#### `mock_response()`
```python
@pytest.fixture
def mock_response() -> Mock:
    """Create a mock Playwright Response object."""
```
**Usage**: Testing response handling
**Returns**: Mock Response with status, headers, url

#### `mock_page()`
```python
@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mock Playwright Page object."""
```
**Usage**: Testing page interactions without real browser
**Key Methods Mocked**:
- `goto()`: Page navigation
- `evaluate()`: JavaScript execution
- `content()`: HTML content retrieval
- `screenshot()`: Screenshot capture
- `query_selector_all()`: DOM queries

#### `mock_browser_context()`
```python
@pytest.fixture
def mock_browser_context() -> AsyncMock:
    """Create a mock Playwright BrowserContext object."""
```
**Usage**: Testing browser context operations
**Key Methods Mocked**:
- `new_page()`: Page creation
- `close()`: Context cleanup
- `route()`: Request interception

#### `mock_browser()`
```python
@pytest.fixture
def mock_browser() -> AsyncMock:
    """Create a mock Playwright Browser object."""
```
**Usage**: Testing browser lifecycle
**Key Methods Mocked**:
- `new_context()`: Context creation
- `close()`: Browser cleanup

## Data Model Fixtures

### `sample_pixel_evidence()`
```python
@pytest.fixture
def sample_pixel_evidence() -> PixelEvidence:
    """Create sample pixel evidence for testing."""
```
**Returns**: PixelEvidence with sample data for all evidence types

### `sample_cookies()`
```python
@pytest.fixture
def sample_cookies() -> list[dict[str, Any]]:
    """Sample cookies for testing."""
```
**Returns**: List of cookie dictionaries with various tracking cookies

## HTML Content Fixtures

Each pixel type has a corresponding HTML fixture containing realistic tracking code:

### `meta_pixel_html()`
```python
@pytest.fixture
def meta_pixel_html() -> str:
    """HTML content with Meta (Facebook) Pixel tracking."""
```
**Contains**: 
- Facebook Pixel initialization code
- fbq tracking calls
- Noscript fallback image

### `google_analytics_html()`
```python
@pytest.fixture
def google_analytics_html() -> str:
    """HTML content with Google Analytics tracking."""
```
**Contains**:
- Google Tag Manager script
- gtag configuration
- dataLayer initialization

### `google_ads_html()`
```python
@pytest.fixture
def google_ads_html() -> str:
    """HTML content with Google Ads tracking."""
```
**Contains**:
- Google Ads conversion tracking
- AW- conversion IDs
- Conversion event tracking

### `tiktok_pixel_html()`
```python
@pytest.fixture
def tiktok_pixel_html() -> str:
    """HTML content with TikTok Pixel tracking."""
```
**Contains**:
- TikTok pixel loader
- ttq.load() calls
- Pixel ID configuration

### `linkedin_insight_html()`
```python
@pytest.fixture
def linkedin_insight_html() -> str:
    """HTML content with LinkedIn Insight Tag tracking."""
```
**Contains**:
- LinkedIn partner ID setup
- Insight tag script loading
- Noscript tracking pixel

### `twitter_pixel_html()`
```python
@pytest.fixture
def twitter_pixel_html() -> str:
    """HTML content with Twitter Pixel tracking."""
```
**Contains**:
- Twitter universal website tag
- twq initialization
- PageView tracking

### `pinterest_tag_html()`
```python
@pytest.fixture
def pinterest_tag_html() -> str:
    """HTML content with Pinterest Tag tracking."""
```
**Contains**:
- Pinterest tag loader
- pintrk calls
- Email hashing setup

### `snapchat_pixel_html()`
```python
@pytest.fixture
def snapchat_pixel_html() -> str:
    """HTML content with Snapchat Pixel tracking."""
```
**Contains**:
- Snap Pixel initialization
- snaptr tracking calls
- User email configuration

### Special HTML Fixtures

#### `clean_html()`
```python
@pytest.fixture
def clean_html() -> str:
    """HTML content with no tracking pixels."""
```
**Usage**: Testing scenarios where no pixels should be detected

#### `multiple_pixels_html()`
```python
@pytest.fixture
def multiple_pixels_html() -> str:
    """HTML content with multiple tracking pixels."""
```
**Usage**: Testing detection of multiple pixel types on one page

## Scanner Fixtures

### `mock_scanner()`
```python
@pytest.fixture
async def mock_scanner(
    mock_browser: AsyncMock, 
    mock_browser_context: AsyncMock, 
    mock_page: AsyncMock
) -> AsyncGenerator[PixelScanner, None]:
    """Create a PixelScanner instance with mocked Playwright components."""
```
**Usage**: Testing scanner without real browser
**Setup**: Patches `_setup_browser` to return mocked components

## Utility Fixtures

### `event_loop()`
```python
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
```
**Usage**: Ensures proper async test execution
**Note**: May show deprecation warning - consider using pytest-asyncio's built-in handling

## Usage Examples

### Testing Pixel Detection
```python
def test_meta_pixel_detection(meta_pixel_html, mock_page):
    # Set page content to Meta pixel HTML
    mock_page.content.return_value = meta_pixel_html
    
    # Test detection logic
    detector = MetaPixelDetector()
    # ... rest of test
```

### Testing with Multiple Fixtures
```python
@pytest.mark.asyncio
async def test_full_scan(
    mock_scanner, 
    meta_pixel_html,
    sample_cookies
):
    # Use multiple fixtures together
    mock_scanner._page.content.return_value = meta_pixel_html
    mock_scanner._page.context.cookies.return_value = sample_cookies
    
    result = await mock_scanner.scan_domain("example.com")
    assert len(result.pixels_detected) > 0
```

### Testing Network Requests
```python
def test_request_handling(mock_request):
    mock_request.url = "https://www.facebook.com/tr?id=123"
    
    detector = MetaPixelDetector()
    is_tracking = detector.check_request(mock_request)
    assert is_tracking is True
```

## Best Practices

1. **Use Type Hints**: All fixtures include proper type annotations
2. **Fixture Composition**: Combine fixtures for complex test scenarios
3. **Isolation**: Each fixture is independent and reusable
4. **Realistic Data**: HTML fixtures contain actual tracking code patterns
5. **Async Support**: Use AsyncMock for async operations

## Adding New Fixtures

When adding new fixtures:
1. Place in appropriate section of conftest.py
2. Include docstring explaining purpose
3. Add type hints for return values
4. Consider if fixture should be session/function scoped
5. Update this documentation

Example:
```python
@pytest.fixture
def new_pixel_html() -> str:
    """HTML content with NewPixel tracking."""
    return """
    <html>
        <head>
            <script>
                // New pixel tracking code
            </script>
        </head>
    </html>
    """
```