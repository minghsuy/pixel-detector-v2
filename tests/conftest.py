"""Shared test fixtures and configuration for pixel-detector tests."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Request, Response

from pixel_detector.models.pixel_detection import PixelEvidence, PixelType
from pixel_detector.scanner import PixelScanner


@pytest.fixture
def mock_request() -> Mock:
    """Create a mock Playwright Request object."""
    request = Mock(spec=Request)
    request.url = "https://example.com"
    request.method = "GET"
    request.resource_type = "script"
    request.headers = {"user-agent": "Mozilla/5.0"}
    return request


@pytest.fixture
def mock_response() -> Mock:
    """Create a mock Playwright Response object."""
    response = Mock(spec=Response)
    response.status = 200
    response.headers = {"content-type": "text/html"}
    response.url = "https://example.com"
    return response


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mock Playwright Page object."""
    page = create_autospec(Page, spec_set=True)
    page.url = "https://example.com"
    page.goto = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value={})
    page.content = AsyncMock(return_value="<html><body></body></html>")
    page.query_selector_all = AsyncMock(return_value=[])
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.close = AsyncMock(return_value=None)
    
    # Mock cookies
    page.context = AsyncMock()
    page.context.cookies = AsyncMock(return_value=[])
    
    return page


@pytest.fixture
def mock_browser_context() -> AsyncMock:
    """Create a mock Playwright BrowserContext object."""
    context = create_autospec(BrowserContext, spec_set=True)
    context.new_page = AsyncMock()
    context.close = AsyncMock(return_value=None)
    context.route = AsyncMock(return_value=None)
    return context


@pytest.fixture
def mock_browser() -> AsyncMock:
    """Create a mock Playwright Browser object."""
    browser = create_autospec(Browser, spec_set=True)
    browser.new_context = AsyncMock()
    browser.close = AsyncMock(return_value=None)
    return browser


@pytest.fixture
def sample_pixel_evidence() -> PixelEvidence:
    """Create sample pixel evidence for testing."""
    return PixelEvidence(
        network_requests=["https://www.facebook.com/tr?id=123456"],
        cookies_set=["_fbp", "_fbc"],
        script_tags=['<script>fbq("init", "123456");</script>'],
        global_variables=["fbq"],
        dom_elements=["<img src='https://www.facebook.com/tr'>"],
        meta_tags=[]
    )


@pytest.fixture
def meta_pixel_html() -> str:
    """HTML content with Meta Pixel tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Meta Pixel</title>
        <!-- Meta Pixel Code -->
        <script>
        !function(f,b,e,v,n,t,s)
        {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)};
        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
        n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t,s)}(window, document,'script',
        'https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', '1234567890');
        fbq('track', 'PageView');
        </script>
        <noscript><img height="1" width="1" style="display:none"
        src="https://www.facebook.com/tr?id=1234567890&ev=PageView&noscript=1"
        /></noscript>
        <!-- End Meta Pixel Code -->
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def google_analytics_html() -> str:
    """HTML content with Google Analytics tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Google Analytics</title>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'GA_MEASUREMENT_ID');
        </script>
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def google_ads_html() -> str:
    """HTML content with Google Ads tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Google Ads</title>
        <!-- Google Ads Conversion Tracking -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=AW-123456789"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'AW-123456789');
          gtag('event', 'conversion', {
              'send_to': 'AW-123456789/AbC-D_efG-h12_34-567',
              'value': 1.0,
              'currency': 'USD'
          });
        </script>
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def tiktok_pixel_html() -> str:
    """HTML content with TikTok Pixel tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with TikTok Pixel</title>
        <script>
        !function (w, d, t) {
          w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"],ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e},ttq.load=function(e,n){var i="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{},ttq._i[e]=[],ttq._i[e]._u=i,ttq._t=ttq._t||{},ttq._t[e]=+new Date,ttq._o=ttq._o||{},ttq._o[e]=n||{};var o=document.createElement("script");o.type="text/javascript",o.async=!0,o.src=i+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)};
          ttq.load('C2ABCDEF3U4G5H6I7J8K');
          ttq.page();
        }(window, document, 'ttq');
        </script>
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def linkedin_insight_html() -> str:
    """HTML content with LinkedIn Insight Tag tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with LinkedIn Insight Tag</title>
        <script type="text/javascript">
        _linkedin_partner_id = "1234567";
        window._linkedin_data_partner_ids = window._linkedin_data_partner_ids || [];
        window._linkedin_data_partner_ids.push(_linkedin_partner_id);
        </script><script type="text/javascript">
        (function(){var s = document.getElementsByTagName("script")[0];
        var b = document.createElement("script");
        b.type = "text/javascript";b.async = true;
        b.src = "https://snap.licdn.com/li.lms-analytics/insight.min.js";
        s.parentNode.insertBefore(b, s);})();
        </script>
        <noscript>
        <img height="1" width="1" style="display:none;" alt="" src="https://px.ads.linkedin.com/collect/?pid=1234567&fmt=gif" />
        </noscript>
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def twitter_pixel_html() -> str:
    """HTML content with Twitter Pixel tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Twitter Pixel</title>
        <!-- Twitter universal website tag code -->
        <script>
        !function(e,t,n,s,u,a){e.twq||(s=e.twq=function(){s.exe?s.exe.apply(s,arguments):s.queue.push(arguments);
        },s.version='1.1',s.queue=[],u=t.createElement(n),u.async=!0,u.src='//static.ads-twitter.com/uwt.js',
        a=t.getElementsByTagName(n)[0],a.parentNode.insertBefore(u,a))}(window,document,'script');
        // Insert Twitter Pixel ID and Standard Events data below
        twq('init','o1234');
        twq('track','PageView');
        </script>
        <!-- End Twitter universal website tag code -->
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def pinterest_tag_html() -> str:
    """HTML content with Pinterest Tag tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Pinterest Tag</title>
        <!-- Pinterest Tag -->
        <script>
        !function(e){if(!window.pintrk){window.pintrk = function () {
        window.pintrk.queue.push(Array.prototype.slice.call(arguments))};var
          n=window.pintrk;n.queue=[],n.version="3.0";var
          t=document.createElement("script");t.async=!0,t.src=e;var
          r=document.getElementsByTagName("script")[0];
          r.parentNode.insertBefore(t,r)}}("https://s.pinimg.com/ct/core.js");
        pintrk('load', '2612345678901', {em: '<user_email_address>'});
        pintrk('page');
        </script>
        <noscript>
        <img height="1" width="1" style="display:none;" alt=""
          src="https://ct.pinterest.com/v3/?event=init&tid=2612345678901&pd[em]=<hashed_email_address>&noscript=1" />
        </noscript>
        <!-- end Pinterest Tag -->
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def snapchat_pixel_html() -> str:
    """HTML content with Snapchat Pixel tracking."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Snapchat Pixel</title>
        <!-- Snap Pixel Code -->
        <script type='text/javascript'>
        (function(e,t,n){if(e.snaptr)return;var a=e.snaptr=function()
        {a.handleRequest?a.handleRequest.apply(a,arguments):a.queue.push(arguments)};
        a.queue=[];var s='script';r=t.createElement(s);r.async=!0;
        r.src=n;var u=t.getElementsByTagName(s)[0];
        u.parentNode.insertBefore(r,u);})(window,document,
        'https://sc-static.net/scevent.min.js');
        snaptr('init', '12345678-1234-1234-1234-123456789012', {
        'user_email': '__INSERT_USER_EMAIL__'
        });
        snaptr('track', 'PAGE_VIEW');
        </script>
        <!-- End Snap Pixel Code -->
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """


@pytest.fixture
def clean_html() -> str:
    """HTML content with no tracking pixels."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clean Test Page</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; }
        </style>
    </head>
    <body>
        <h1>Test Page Without Tracking</h1>
        <p>This page has no tracking pixels.</p>
    </body>
    </html>
    """


@pytest.fixture
def multiple_pixels_html() -> str:
    """HTML content with multiple tracking pixels."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page with Multiple Pixels</title>
        <!-- Meta Pixel Code -->
        <script>
        fbq('init', '1234567890');
        fbq('track', 'PageView');
        </script>
        <!-- Google Analytics -->
        <script>
        gtag('config', 'GA_MEASUREMENT_ID');
        </script>
        <!-- TikTok Pixel -->
        <script>
        ttq.load('C2ABCDEF3U4G5H6I7J8K');
        </script>
    </head>
    <body>
        <h1>Test Page with Multiple Tracking Pixels</h1>
    </body>
    </html>
    """


@pytest.fixture
async def mock_scanner(mock_browser: AsyncMock, mock_browser_context: AsyncMock, mock_page: AsyncMock) -> AsyncGenerator[PixelScanner, None]:
    """Create a PixelScanner instance with mocked Playwright components."""
    scanner = PixelScanner(headless=True, timeout=5000)
    
    # Mock the browser setup
    mock_browser.new_context.return_value = mock_browser_context
    mock_browser_context.new_page.return_value = mock_page
    
    # Patch the browser launching methods
    scanner._launch_browser = AsyncMock(return_value=mock_browser)  # type: ignore
    scanner._create_context = AsyncMock(return_value=mock_browser_context)  # type: ignore
    
    yield scanner
    
    # Cleanup not needed as we're using mocks


@pytest.fixture
def sample_cookies() -> list[dict[str, Any]]:
    """Sample cookies for testing."""
    return [
        {
            "name": "_fbp",
            "value": "fb.1.1234567890.123456789",
            "domain": ".example.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax"
        },
        {
            "name": "_ga",
            "value": "GA1.2.123456789.1234567890",
            "domain": ".example.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": False,
            "sameSite": "Lax"
        },
        {
            "name": "_ttp",
            "value": "2Vt-TZtehyBxjpPiFW3cJQXXQAw",
            "domain": ".example.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }
    ]


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()