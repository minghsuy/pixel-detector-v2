"""Tests for all individual pixel detectors."""

import re
from re import Pattern
import pytest
from playwright.async_api import Page
from unittest.mock import AsyncMock, Mock, patch

from pixel_detector.detectors.google import GoogleAnalyticsDetector, GoogleAdsDetector
from pixel_detector.detectors.meta import MetaPixelDetector
from pixel_detector.detectors.linkedin import LinkedInInsightDetector
from pixel_detector.detectors.pinterest import PinterestTagDetector
from pixel_detector.detectors.snapchat import SnapchatPixelDetector
from pixel_detector.detectors.tiktok import TikTokPixelDetector
from pixel_detector.detectors.twitter import TwitterPixelDetector
from pixel_detector.models.pixel_detection import PixelType, RiskLevel


class TestMetaPixelDetector:
    """Test cases for Meta Pixel detector."""

    def test_properties(self):
        """Test Meta detector properties."""
        detector = MetaPixelDetector()
        assert detector.pixel_type == PixelType.META_PIXEL
        assert "facebook.com/tr" in detector.tracking_domains
        assert "connect.facebook.net" in detector.tracking_domains
        assert "_fbp" in detector.cookie_names
        assert "_fbc" in detector.cookie_names
        assert len(detector.script_patterns) > 0
        assert detector.risk_level == RiskLevel.HIGH
        assert detector.hipaa_concern is True

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Meta pixel network request detection."""
        detector = MetaPixelDetector()
        
        # Create mock request
        request = Mock()
        request.url = "https://www.facebook.com/tr?id=123456&ev=PageView"
        
        # Should detect
        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1
        assert "123456" in detector.pixel_ids
        
        # Non-matching request
        request.url = "https://www.google.com/analytics.js"
        result = await detector.check_request(request)
        assert result is False

    def test_extract_pixel_id(self):
        """Test Meta pixel ID extraction from URL."""
        detector = MetaPixelDetector()
        
        pixel_id = detector.extract_pixel_id("https://www.facebook.com/tr?id=1234567890&ev=PageView")
        assert pixel_id == "1234567890"
        
        pixel_id = detector.extract_pixel_id("https://connect.facebook.net/fbevents.js")
        assert pixel_id is None

    def test_extract_pixel_id_from_script(self):
        """Test Meta pixel ID extraction from script."""
        detector = MetaPixelDetector()
        
        script = 'fbq("init", "9876543210");'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "9876543210"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test Meta pixel global variable detection."""
        detector = MetaPixelDetector()
        
        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["fbq", "_fbq"]
        
        await detector.check_global_variables(page)
        
        assert "fbq" in detector.global_variables
        assert "_fbq" in detector.global_variables

    @pytest.mark.asyncio
    async def test_check_dom_elements(self):
        """Test Meta pixel DOM element detection."""
        detector = MetaPixelDetector()
        
        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ['<noscript><img src="https://www.facebook.com/tr?id=123" /></noscript>']
        
        await detector.check_dom_elements(page)
        
        assert len(detector.dom_elements) == 1
        assert "facebook.com/tr" in detector.dom_elements[0]


class TestGoogleAnalyticsDetector:
    """Test cases for Google Analytics detector."""

    def test_properties(self):
        """Test GA detector properties."""
        detector = GoogleAnalyticsDetector()
        assert detector.pixel_type == PixelType.GOOGLE_ANALYTICS
        # Check for specific paths, not just domains
        assert any("google-analytics.com" in domain for domain in detector.tracking_domains)
        assert any("googletagmanager.com" in domain for domain in detector.tracking_domains)
        assert "_ga" in detector.cookie_names
        assert "_gid" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test GA network request detection."""
        detector = GoogleAnalyticsDetector()
        
        request = Mock()
        request.url = "https://www.google-analytics.com/analytics.js"
        
        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

    def test_extract_pixel_id(self):
        """Test GA measurement ID extraction."""
        detector = GoogleAnalyticsDetector()
        
        # From collect URL with tid parameter
        pixel_id = detector.extract_pixel_id("https://www.google-analytics.com/collect?v=1&tid=UA-12345678-1")
        assert pixel_id == "UA-12345678-1"
        
        # From collect URL with G- format
        pixel_id = detector.extract_pixel_id("https://www.google-analytics.com/collect?v=1&tid=G-ABC123")
        assert pixel_id == "G-ABC123"

    def test_extract_pixel_id_from_script(self):
        """Test GA measurement ID extraction from script."""
        detector = GoogleAnalyticsDetector()
        
        script = 'gtag("config", "G-ABCDEF123");'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "G-ABCDEF123"


class TestGoogleAdsDetector:
    """Test cases for Google Ads detector."""

    def test_properties(self):
        """Test Google Ads detector properties."""
        detector = GoogleAdsDetector()
        assert detector.pixel_type == PixelType.GOOGLE_ADS
        # Check for specific paths, not just domains
        assert any("googleadservices.com" in domain for domain in detector.tracking_domains)
        assert any("doubleclick.net" in domain for domain in detector.tracking_domains)
        assert "_gcl_aw" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Google Ads network request detection."""
        detector = GoogleAdsDetector()
        
        request = Mock()
        request.url = "https://www.googleadservices.com/pagead/conversion.js"
        
        result = await detector.check_request(request)
        assert result is True

    def test_extract_pixel_id_from_script(self):
        """Test Google Ads conversion ID extraction."""
        detector = GoogleAdsDetector()
        
        script = 'gtag("config", "AW-123456789");'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "AW-123456789"


class TestTikTokPixelDetector:
    """Test cases for TikTok Pixel detector."""

    def test_properties(self):
        """Test TikTok detector properties."""
        detector = TikTokPixelDetector()
        assert detector.pixel_type == PixelType.TIKTOK_PIXEL
        assert "analytics.tiktok.com" in detector.tracking_domains
        assert "_ttp" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test TikTok pixel network request detection."""
        detector = TikTokPixelDetector()
        
        request = Mock()
        request.url = "https://analytics.tiktok.com/api/v1/pixel?pixel_code=C2ABCDEF3U4G5H6I7J8K"
        
        result = await detector.check_request(request)
        assert result is True
        assert "C2ABCDEF3U4G5H6I7J8K" in detector.pixel_ids

    def test_extract_pixel_id(self):
        """Test TikTok pixel ID extraction from URL."""
        detector = TikTokPixelDetector()
        
        pixel_id = detector.extract_pixel_id("https://analytics.tiktok.com/api/v1/pixel?pixel_code=C2ABCDEF3U4G5H6I7J8K")
        assert pixel_id == "C2ABCDEF3U4G5H6I7J8K"

    def test_extract_pixel_id_from_script(self):
        """Test TikTok pixel ID extraction from script."""
        detector = TikTokPixelDetector()
        
        script = 'ttq("init", "C2ABCDEF3U4G5H6I7J8K");'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "C2ABCDEF3U4G5H6I7J8K"


class TestLinkedInInsightDetector:
    """Test cases for LinkedIn Insight Tag detector."""

    def test_properties(self):
        """Test LinkedIn detector properties."""
        detector = LinkedInInsightDetector()
        assert detector.pixel_type == PixelType.LINKEDIN_INSIGHT
        assert "px.ads.linkedin.com" in detector.tracking_domains
        assert "snap.licdn.com" in detector.tracking_domains
        assert "li_fat_id" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test LinkedIn pixel network request detection."""
        detector = LinkedInInsightDetector()
        
        request = Mock()
        request.url = "https://px.ads.linkedin.com/collect/?pid=1234567&fmt=gif"
        
        result = await detector.check_request(request)
        assert result is True
        assert "1234567" in detector.pixel_ids

    def test_extract_pixel_id(self):
        """Test LinkedIn partner ID extraction."""
        detector = LinkedInInsightDetector()
        
        pixel_id = detector.extract_pixel_id("https://px.ads.linkedin.com/collect/?pid=1234567&fmt=gif")
        assert pixel_id == "1234567"


class TestTwitterPixelDetector:
    """Test cases for Twitter Pixel detector."""

    def test_properties(self):
        """Test Twitter detector properties."""
        detector = TwitterPixelDetector()
        assert detector.pixel_type == PixelType.TWITTER_PIXEL
        assert "analytics.twitter.com" in detector.tracking_domains
        assert "static.ads-twitter.com" in detector.tracking_domains
        assert "personalization_id" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Twitter pixel network request detection."""
        detector = TwitterPixelDetector()
        
        request = Mock()
        request.url = "https://analytics.twitter.com/i/adsct?txn_id=o1234"
        
        result = await detector.check_request(request)
        assert result is True

    def test_extract_pixel_id_from_script(self):
        """Test Twitter pixel ID extraction."""
        detector = TwitterPixelDetector()
        
        script = 'twq("init","o1234");'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "o1234"


class TestPinterestTagDetector:
    """Test cases for Pinterest Tag detector."""

    def test_properties(self):
        """Test Pinterest detector properties."""
        detector = PinterestTagDetector()
        assert detector.pixel_type == PixelType.PINTEREST_TAG
        # Check for specific paths, not just domains
        assert any("ct.pinterest.com" in domain for domain in detector.tracking_domains)
        assert any("s.pinimg.com" in domain for domain in detector.tracking_domains)
        assert "_pinterest_ct" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Pinterest pixel network request detection."""
        detector = PinterestTagDetector()
        
        request = Mock()
        request.url = "https://ct.pinterest.com/v3/?event=init&tid=2612345678901"
        
        result = await detector.check_request(request)
        assert result is True
        assert "2612345678901" in detector.pixel_ids

    def test_extract_pixel_id(self):
        """Test Pinterest tag ID extraction."""
        detector = PinterestTagDetector()
        
        pixel_id = detector.extract_pixel_id("https://ct.pinterest.com/v3/?event=init&tid=2612345678901")
        assert pixel_id == "2612345678901"


class TestSnapchatPixelDetector:
    """Test cases for Snapchat Pixel detector."""

    def test_properties(self):
        """Test Snapchat detector properties."""
        detector = SnapchatPixelDetector()
        assert detector.pixel_type == PixelType.SNAPCHAT_PIXEL
        assert "sc-static.net" in detector.tracking_domains
        assert "tr.snapchat.com" in detector.tracking_domains
        assert "_scid" in detector.cookie_names
        assert len(detector.script_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Snapchat pixel network request detection."""
        detector = SnapchatPixelDetector()
        
        request = Mock()
        request.url = "https://sc-static.net/scevent.min.js"
        
        result = await detector.check_request(request)
        assert result is True

    def test_extract_pixel_id_from_script(self):
        """Test Snapchat pixel ID extraction."""
        detector = SnapchatPixelDetector()
        
        script = 'snaptr("init", "12345678-1234-1234-1234-123456789012");'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "12345678-1234-1234-1234-123456789012"


class TestAllDetectorsIntegration:
    """Integration tests for all detectors."""

    @pytest.mark.parametrize("detector_class,expected_type", [
        (MetaPixelDetector, PixelType.META_PIXEL),
        (GoogleAnalyticsDetector, PixelType.GOOGLE_ANALYTICS),
        (GoogleAdsDetector, PixelType.GOOGLE_ADS),
        (TikTokPixelDetector, PixelType.TIKTOK_PIXEL),
        (LinkedInInsightDetector, PixelType.LINKEDIN_INSIGHT),
        (TwitterPixelDetector, PixelType.TWITTER_PIXEL),
        (PinterestTagDetector, PixelType.PINTEREST_TAG),
        (SnapchatPixelDetector, PixelType.SNAPCHAT_PIXEL),
    ])
    def test_detector_types(self, detector_class, expected_type):
        """Test that all detectors return correct pixel types."""
        detector = detector_class()
        assert detector.pixel_type == expected_type

    @pytest.mark.parametrize("detector_class", [
        MetaPixelDetector,
        GoogleAnalyticsDetector,
        GoogleAdsDetector,
        TikTokPixelDetector,
        LinkedInInsightDetector,
        TwitterPixelDetector,
        PinterestTagDetector,
        SnapchatPixelDetector,
    ])
    def test_detector_initialization(self, detector_class):
        """Test that all detectors can be initialized."""
        detector = detector_class()
        assert detector.network_requests == []
        assert detector.cookies_found == set()
        assert detector.script_tags == []
        assert detector.global_variables == []
        assert detector.dom_elements == []
        assert detector.meta_tags == []
        assert detector.pixel_ids == set()

    @pytest.mark.parametrize("detector_class", [
        MetaPixelDetector,
        GoogleAnalyticsDetector,
        GoogleAdsDetector,
        TikTokPixelDetector,
        LinkedInInsightDetector,
        TwitterPixelDetector,
        PinterestTagDetector,
        SnapchatPixelDetector,
    ])
    def test_detector_has_required_properties(self, detector_class):
        """Test that all detectors have required properties."""
        detector = detector_class()
        assert hasattr(detector, 'pixel_type')
        assert hasattr(detector, 'tracking_domains')
        assert hasattr(detector, 'cookie_names')
        assert hasattr(detector, 'script_patterns')
        assert len(detector.tracking_domains) > 0
        assert len(detector.cookie_names) > 0
        assert len(detector.script_patterns) > 0
        assert isinstance(detector.script_patterns[0], Pattern)

    @pytest.mark.parametrize("detector_class", [
        MetaPixelDetector,
        GoogleAnalyticsDetector,
        GoogleAdsDetector,
        TikTokPixelDetector,
        LinkedInInsightDetector,
        TwitterPixelDetector,
        PinterestTagDetector,
        SnapchatPixelDetector,
    ])
    def test_detector_build_detection(self, detector_class):
        """Test that all detectors can build detections."""
        detector = detector_class()
        
        # Add some evidence
        detector.network_requests.append("https://example.com/tracking")
        
        detection = detector.build_detection()
        assert detection is not None
        assert detection.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]
        assert detection.hipaa_concern is True