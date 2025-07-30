"""Tests for the pixel scanner module."""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Request

from pixel_detector.detectors.base import BasePixelDetector
from pixel_detector.detectors.registry import get_all_detectors
from pixel_detector.models.pixel_detection import PixelType, ScanResult, ScanMetadata
from pixel_detector.scanner import PixelScanner


class TestPixelScanner:
    """Test cases for PixelScanner class."""

    def test_init(self):
        """Test PixelScanner initialization."""
        scanner = PixelScanner(headless=True, timeout=10000)
        assert scanner.headless is True
        assert scanner.timeout == 10000
        assert scanner.stealth_mode is True
        assert scanner.screenshot is False

    def test_init_defaults(self):
        """Test PixelScanner initialization with defaults."""
        scanner = PixelScanner()
        assert scanner.headless is True
        assert scanner.timeout == 30000
        assert scanner.stealth_mode is True
        assert scanner.screenshot is False
        assert scanner.user_agent is not None

    @pytest.mark.asyncio
    async def test_scan_domain_success(self, mock_scanner: PixelScanner, meta_pixel_html: str):
        """Test successful domain scanning with Meta pixel."""
        # Test the scanner with the mock setup
        result = await mock_scanner.scan_domain("https://example.com")
        
        assert result.domain == "example.com"
        assert result.success is True
        assert isinstance(result.timestamp, datetime)
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_scan_domain_with_network_requests(
        self, 
        mock_browser: AsyncMock, 
        mock_browser_context: AsyncMock,
        mock_page: AsyncMock,
        mock_request: Mock
    ):
        """Test domain scanning with network request tracking."""
        scanner = PixelScanner()
        
        # Track if Meta pixel requests are captured
        meta_requests_captured = 0
        route_handler = None
        
        def capture_route_handler(handler):
            nonlocal route_handler
            route_handler = handler
        
        # Mock the page.route method to capture the handler
        mock_page.route = capture_route_handler
        
        # Configure mock request
        mock_request.url = "https://www.facebook.com/tr?id=123456"
        
        with patch.object(scanner, '_launch_browser', return_value=mock_browser), \
             patch.object(scanner, '_create_context', return_value=mock_browser_context):
            # Start the scan
            scan_task = asyncio.create_task(scanner.scan_domain("https://example.com"))
            
            # Give the scan a moment to start
            await asyncio.sleep(0.1)
            
            # Simulate network request
            if route_handler:
                await route_handler(mock_request)
            
            # Complete the scan
            result = await scan_task
            
            assert result.success is True
            assert result.domain == "example.com"

    @pytest.mark.asyncio
    async def test_scan_domain_error_handling(self, mock_scanner: PixelScanner):
        """Test error handling during domain scanning."""
        # Mock page to raise an error
        mock_page = AsyncMock(spec=Page)
        mock_page.goto.side_effect = Exception("Network error")
        
        mock_browser = AsyncMock(spec=Browser)
        mock_context = AsyncMock(spec=BrowserContext)
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        with patch.object(mock_scanner, '_launch_browser', return_value=mock_browser), \
             patch.object(mock_scanner, '_create_context', return_value=mock_context):
            result = await mock_scanner.scan_domain("https://error.com")
            
            assert result.success is False
            assert "Network error" in str(result.error_message) or "await" in str(result.error_message)
            assert result.domain == "error.com"
            assert result.pixels_detected == []

    @pytest.mark.asyncio
    async def test_scan_multiple_domains(self, mock_scanner: PixelScanner):
        """Test scanning multiple domains."""
        domains = ["https://example1.com", "https://example2.com", "https://example3.com"]
        
        # Mock scan_domain to return successful results
        async def mock_scan(domain: str) -> ScanResult:
            from pixel_detector.models import ScanMetadata
            return ScanResult(
                domain=domain.replace("https://", ""),
                url_scanned=domain,
                timestamp=datetime.now(),
                pixels_detected=[],
                success=True,
                error_message=None,
                scan_metadata=ScanMetadata(
                    page_load_time=1.0,
                    total_requests=10,
                    tracking_requests=0,
                    scan_duration=2.0
                )
            )
        
        with patch.object(mock_scanner, 'scan_domain', side_effect=mock_scan):
            results = await mock_scanner.scan_multiple(domains)
            
            assert len(results) == 3
            assert all(r.success for r in results)
            assert [r.domain for r in results] == ["example1.com", "example2.com", "example3.com"]

    @pytest.mark.asyncio
    async def test_launch_browser(self):
        """Test browser launch."""
        scanner = PixelScanner(headless=False, timeout=5000)
        
        with patch('pixel_detector.scanner.async_playwright') as mock_playwright:
            # Mock the playwright context manager
            mock_pw = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value = mock_pw
            
            # Mock browser launch
            mock_browser = AsyncMock(spec=Browser)
            mock_context = AsyncMock(spec=BrowserContext)
            mock_pw.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            
            browser = await scanner._launch_browser(mock_pw)
            context = await scanner._create_context(browser)
            
            # Verify browser was launched with correct options
            mock_pw.chromium.launch.assert_called_once()
            call_args = mock_pw.chromium.launch.call_args[1]
            assert call_args['headless'] is False
            
            # Verify context was created
            mock_browser.new_context.assert_called_once()