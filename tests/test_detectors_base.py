"""Tests for the base pixel detector."""

import re
from abc import ABC
from re import Pattern
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from playwright.async_api import Page, Request

from pixel_detector.detectors.base import BasePixelDetector
from pixel_detector.models.pixel_detection import PixelDetection, PixelEvidence, PixelType, RiskLevel


class ConcreteDetector(BasePixelDetector):
    """Concrete implementation of BasePixelDetector for testing."""
    
    @property
    def pixel_type(self) -> PixelType:
        return PixelType.META_PIXEL
    
    @property
    def tracking_domains(self) -> list[str]:
        return ["facebook.com", "fbcdn.net"]
    
    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"fbq\s*\(\s*['\"]init['\"]", re.IGNORECASE),
            re.compile(r"facebook\.com/tr\?", re.IGNORECASE),
        ]
    
    @property
    def cookie_names(self) -> list[str]:
        return ["_fbp", "_fbc"]
    
    async def check_global_variables(self, page: Page) -> None:
        """Check for specific global variables."""
        fb_vars = await page.evaluate("() => typeof fbq !== 'undefined' ? ['fbq'] : []")
        self.global_variables.extend(fb_vars)
    
    async def check_dom_elements(self, page: Page) -> None:
        """Check for specific DOM elements."""
        pass
    
    async def check_meta_tags(self, page: Page) -> None:
        """Check for specific meta tags."""
        pass
    
    def extract_pixel_id(self, url: str) -> str | None:
        """Extract pixel ID from URL."""
        import re
        match = re.search(r"[?&]id=(\d+)", url)
        if match:
            return match.group(1)
        return None
    
    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract pixel ID from script content."""
        import re
        match = re.search(r"fbq\s*\(\s*['\"]init['\"]\s*,\s*['\"](\d+)['\"]", script)
        if match:
            return match.group(1)
        return None


class TestBasePixelDetector:
    """Test cases for BasePixelDetector."""

    def test_init(self):
        """Test detector initialization."""
        detector = ConcreteDetector()
        assert detector.network_requests == []
        assert detector.cookies_found == set()
        assert detector.script_tags == []
        assert detector.global_variables == []
        assert detector.dom_elements == []
        assert detector.meta_tags == []
        assert detector.pixel_ids == set()

    def test_abstract_properties(self):
        """Test that abstract properties are properly implemented."""
        detector = ConcreteDetector()
        assert detector.pixel_type == PixelType.META_PIXEL
        assert detector.tracking_domains == ["facebook.com", "fbcdn.net"]
        assert len(detector.script_patterns) == 2
        assert detector.cookie_names == ["_fbp", "_fbc"]

    def test_risk_level_property(self):
        """Test default risk level."""
        detector = ConcreteDetector()
        assert detector.risk_level == RiskLevel.HIGH

    def test_hipaa_concern_property(self):
        """Test default HIPAA concern."""
        detector = ConcreteDetector()
        assert detector.hipaa_concern is True

    def test_reset(self):
        """Test detector reset functionality."""
        detector = ConcreteDetector()
        
        # Add some data
        detector.network_requests.append("https://facebook.com/tr")
        detector.cookies_found.add("_fbp")
        detector.script_tags.append("<script>fbq</script>")
        detector.global_variables.append("fbq")
        detector.dom_elements.append("<img>")
        detector.meta_tags.append("<meta>")
        detector.pixel_ids.add("123456")
        
        # Reset
        detector.reset()
        
        # Verify everything is cleared
        assert detector.network_requests == []
        assert detector.cookies_found == set()
        assert detector.script_tags == []
        assert detector.global_variables == []
        assert detector.dom_elements == []
        assert detector.meta_tags == []
        assert detector.pixel_ids == set()

    @pytest.mark.asyncio
    async def test_check_request_match(self):
        """Test network request checking with matching domain."""
        detector = ConcreteDetector()
        
        # Create mock request
        request = Mock(spec=Request)
        request.url = "https://www.facebook.com/tr?id=123456&ev=PageView"
        
        # Test matching request
        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1
        assert "facebook.com/tr?id=123456" in detector.network_requests[0]
        assert "123456" in detector.pixel_ids

    @pytest.mark.asyncio
    async def test_check_request_no_match(self):
        """Test network request checking with non-matching domain."""
        detector = ConcreteDetector()
        
        # Create mock request
        request = Mock(spec=Request)
        request.url = "https://www.google.com/analytics.js"
        
        # Test non-matching request
        result = await detector.check_request(request)
        assert result is False
        assert len(detector.network_requests) == 0
        assert len(detector.pixel_ids) == 0

    @pytest.mark.asyncio
    async def test_check_cookies(self):
        """Test cookie checking."""
        detector = ConcreteDetector()
        
        # Create mock page
        page = AsyncMock(spec=Page)
        page.context.cookies = AsyncMock(return_value=[
            {"name": "_fbp", "value": "fb.1.123456", "domain": ".example.com"},
            {"name": "_fbc", "value": "fb.2.123456", "domain": ".example.com"},
            {"name": "_ga", "value": "GA1.2.123456", "domain": ".example.com"},  # Non-matching
        ])
        
        await detector.check_cookies(page)
        
        # Verify only matching cookies were found
        assert len(detector.cookies_found) == 2
        assert "_fbp" in detector.cookies_found
        assert "_fbc" in detector.cookies_found
        assert "_ga" not in detector.cookies_found

    @pytest.mark.asyncio
    async def test_check_dom(self):
        """Test DOM checking."""
        detector = ConcreteDetector()
        
        # Create mock page
        page = AsyncMock(spec=Page)
        
        # Mock script evaluation
        page.evaluate.side_effect = [
            # First call returns scripts
            [
                '<script>fbq("init", "123456789");</script>',
                '<script src="https://connect.facebook.com/fbevents.js"></script>',
                '<script>console.log("test");</script>',
            ],
            # Second call for global variables
            ["fbq"],
        ]
        
        await detector.check_dom(page)
        
        # Verify scripts were found
        assert len(detector.script_tags) == 1  # Only one script matches the patterns
        assert any("fbq" in script for script in detector.script_tags)
        assert "123456789" in detector.pixel_ids
        
        # Verify global variables were checked
        assert "fbq" in detector.global_variables

    def test_is_detected_true(self):
        """Test detection when evidence exists."""
        detector = ConcreteDetector()
        
        # No evidence - should not be detected
        assert detector.is_detected() is False
        
        # Add some evidence
        detector.network_requests.append("https://facebook.com/tr")
        assert detector.is_detected() is True
        
        # Reset and try with different evidence
        detector.reset()
        detector.cookies_found.add("_fbp")
        assert detector.is_detected() is True

    def test_is_detected_false(self):
        """Test detection when no evidence exists."""
        detector = ConcreteDetector()
        assert detector.is_detected() is False

    def test_build_detection_with_evidence(self):
        """Test building detection with evidence."""
        detector = ConcreteDetector()
        
        # Add evidence
        detector.network_requests = ["https://www.facebook.com/tr?id=123"]
        detector.cookies_found = {"_fbp", "_fbc"}
        detector.script_tags = ['<script>fbq("init", "123");</script>']
        detector.global_variables = ["fbq"]
        detector.pixel_ids = {"123456"}
        
        detection = detector.build_detection()
        
        assert detection is not None
        assert detection.type == PixelType.META_PIXEL
        assert detection.risk_level == RiskLevel.HIGH
        assert detection.hipaa_concern is True
        assert detection.pixel_id == "123456"
        assert len(detection.evidence.network_requests) == 1
        assert len(detection.evidence.cookies_set) == 2
        assert detection.description is not None

    def test_build_detection_no_evidence(self):
        """Test building detection with no evidence."""
        detector = ConcreteDetector()
        
        detection = detector.build_detection()
        assert detection is None

    def test_get_description(self):
        """Test description generation."""
        detector = ConcreteDetector()
        
        # Add various evidence
        detector.network_requests = ["req1", "req2"]
        detector.script_tags = ["script1"]
        detector.cookies_found = {"_fbp"}
        detector.pixel_ids = {"123456", "789012"}
        
        description = detector.get_description()
        
        assert "meta_pixel detected" in description
        assert "2 tracking requests" in description
        assert "1 tracking scripts" in description
        assert "1 tracking cookies" in description
        assert "Pixel ID: " in description

    def test_extract_pixel_id(self):
        """Test pixel ID extraction from URL."""
        detector = ConcreteDetector()
        
        # Test with ID in URL
        pixel_id = detector.extract_pixel_id("https://www.facebook.com/tr?id=123456789&ev=PageView")
        assert pixel_id == "123456789"
        
        # Test without ID
        pixel_id = detector.extract_pixel_id("https://www.facebook.com/fbevents.js")
        assert pixel_id is None

    def test_extract_pixel_id_from_script(self):
        """Test pixel ID extraction from script."""
        detector = ConcreteDetector()
        
        # Test with matching script
        pixel_id = detector.extract_pixel_id_from_script('<script>fbq("init", "123");</script>')
        assert pixel_id == "123"
        
        # Test with non-matching script
        pixel_id = detector.extract_pixel_id_from_script('<script>console.log("test");</script>')
        assert pixel_id is None

    @pytest.mark.asyncio
    async def test_check_meta_tags_abstract(self):
        """Test that check_meta_tags can be called."""
        detector = ConcreteDetector()
        mock_page = AsyncMock(spec=Page)
        
        # Should not raise an error
        await detector.check_meta_tags(mock_page)

    @pytest.mark.asyncio
    async def test_check_global_variables_implementation(self):
        """Test concrete implementation of check_global_variables."""
        detector = ConcreteDetector()
        mock_page = AsyncMock(spec=Page)
        mock_page.evaluate.return_value = ["fbq"]
        
        await detector.check_global_variables(mock_page)
        
        assert "fbq" in detector.global_variables