"""Tests for consent management platform detectors."""

import pytest
from playwright.async_api import Page
from unittest.mock import AsyncMock, Mock

from pixel_detector.detectors.cookiebot import CookieBotDetector
from pixel_detector.detectors.onetrust import OneTrustDetector
from pixel_detector.detectors.osano import OsanoDetector
from pixel_detector.detectors.termly import TermlyDetector
from pixel_detector.detectors.trustarc import TrustArcDetector
from pixel_detector.detectors.usercentrics import UsercentricsDetector
from pixel_detector.models.pixel_detection import PixelType, RiskLevel


class TestOneTrustDetector:
    """Test cases for OneTrust consent platform detector."""

    def test_properties(self):
        """Test OneTrust detector properties."""
        detector = OneTrustDetector()
        assert detector.pixel_type == PixelType.ONETRUST
        assert "cdn.cookielaw.org" in detector.tracking_domains
        assert "optanon.blob.core.windows.net" in detector.tracking_domains
        assert "OptanonConsent" in detector.cookie_names
        assert "OptanonAlertBoxClosed" in detector.cookie_names
        assert len(detector.script_patterns) > 0
        assert detector.risk_level == RiskLevel.LOW
        assert detector.hipaa_concern is False

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test OneTrust network request detection."""
        detector = OneTrustDetector()

        # Create mock request
        request = Mock()
        request.url = "https://cdn.cookielaw.org/scripttemplates/otSDKStub.js?domainScript=abc123"

        # Should detect
        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

        # Non-matching request
        request.url = "https://www.google.com/analytics.js"
        result = await detector.check_request(request)
        assert result is False

    def test_extract_pixel_id(self):
        """Test OneTrust ID extraction from URL."""
        detector = OneTrustDetector()

        pixel_id = detector.extract_pixel_id(
            "https://cdn.cookielaw.org/scripttemplates/otSDKStub.js?domainScript=abc-123-def"
        )
        assert pixel_id == "abc-123-def"

        pixel_id = detector.extract_pixel_id("https://cdn.cookielaw.org/consent/abc123/otBannerSdk.js")
        assert pixel_id is None

    def test_extract_pixel_id_from_script(self):
        """Test OneTrust ID extraction from script."""
        detector = OneTrustDetector()

        script = '<script src="..." data-domain-script="abc-123-def"></script>'
        pixel_id = detector.extract_pixel_id_from_script(script)
        assert pixel_id == "abc-123-def"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test OneTrust global variable detection."""
        detector = OneTrustDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["OneTrust", "OptanonWrapper"]

        await detector.check_global_variables(page)

        assert "OneTrust" in detector.global_variables
        assert "OptanonWrapper" in detector.global_variables

    @pytest.mark.asyncio
    async def test_check_dom_elements(self):
        """Test OneTrust DOM element detection."""
        detector = OneTrustDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["#onetrust-consent-sdk", "#onetrust-banner-sdk"]

        await detector.check_dom_elements(page)

        assert len(detector.dom_elements) == 2
        assert "#onetrust-consent-sdk" in detector.dom_elements


class TestCookieBotDetector:
    """Test cases for Cookiebot consent platform detector."""

    def test_properties(self):
        """Test Cookiebot detector properties."""
        detector = CookieBotDetector()
        assert detector.pixel_type == PixelType.COOKIEBOT
        assert "consent.cookiebot.com" in detector.tracking_domains
        assert "CookieConsent" in detector.cookie_names
        assert detector.risk_level == RiskLevel.LOW
        assert detector.hipaa_concern is False

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Cookiebot network request detection."""
        detector = CookieBotDetector()

        request = Mock()
        request.url = "https://consent.cookiebot.com/uc.js?cbid=abc-123"

        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

    def test_extract_pixel_id(self):
        """Test Cookiebot ID extraction from URL."""
        detector = CookieBotDetector()

        pixel_id = detector.extract_pixel_id("https://consent.cookiebot.com/uc.js?cbid=abc-123-def")
        assert pixel_id == "abc-123-def"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test Cookiebot global variable detection."""
        detector = CookieBotDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["Cookiebot", "CookieConsent"]

        await detector.check_global_variables(page)

        assert "Cookiebot" in detector.global_variables
        assert "CookieConsent" in detector.global_variables


class TestOsanoDetector:
    """Test cases for Osano consent platform detector."""

    def test_properties(self):
        """Test Osano detector properties."""
        detector = OsanoDetector()
        assert detector.pixel_type == PixelType.OSANO
        assert "cmp.osano.com" in detector.tracking_domains
        assert "osano_consentmanager" in detector.cookie_names
        assert detector.risk_level == RiskLevel.LOW
        assert detector.hipaa_concern is False

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Osano network request detection."""
        detector = OsanoDetector()

        request = Mock()
        request.url = "https://cmp.osano.com/ABC12345/config.json"

        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

    def test_extract_pixel_id(self):
        """Test Osano ID extraction from URL."""
        detector = OsanoDetector()

        pixel_id = detector.extract_pixel_id("https://cmp.osano.com/ABC12345/config.json")
        assert pixel_id == "ABC12345"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test Osano global variable detection."""
        detector = OsanoDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["Osano", "osano"]

        await detector.check_global_variables(page)

        assert "Osano" in detector.global_variables
        assert "osano" in detector.global_variables


class TestTrustArcDetector:
    """Test cases for TrustArc consent platform detector."""

    def test_properties(self):
        """Test TrustArc detector properties."""
        detector = TrustArcDetector()
        assert detector.pixel_type == PixelType.TRUSTARC
        assert "consent.trustarc.com" in detector.tracking_domains
        assert "notice_preferences" in detector.cookie_names
        assert detector.risk_level == RiskLevel.LOW
        assert detector.hipaa_concern is False

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test TrustArc network request detection."""
        detector = TrustArcDetector()

        request = Mock()
        request.url = "https://consent.trustarc.com/notice?domain=example.com"

        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

    def test_extract_pixel_id(self):
        """Test TrustArc domain extraction from URL."""
        detector = TrustArcDetector()

        pixel_id = detector.extract_pixel_id("https://consent.trustarc.com/notice?domain=example.com")
        assert pixel_id == "example.com"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test TrustArc global variable detection."""
        detector = TrustArcDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["truste", "TrustArc"]

        await detector.check_global_variables(page)

        assert "truste" in detector.global_variables
        assert "TrustArc" in detector.global_variables


class TestUsercentricsDetector:
    """Test cases for Usercentrics consent platform detector."""

    def test_properties(self):
        """Test Usercentrics detector properties."""
        detector = UsercentricsDetector()
        assert detector.pixel_type == PixelType.USERCENTRICS
        assert "app.usercentrics.eu" in detector.tracking_domains
        assert "uc_user_interaction" in detector.cookie_names
        assert detector.risk_level == RiskLevel.LOW
        assert detector.hipaa_concern is False

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Usercentrics network request detection."""
        detector = UsercentricsDetector()

        request = Mock()
        request.url = "https://app.usercentrics.eu/browser-ui/latest/loader.js?settingsId=abc123"

        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

    def test_extract_pixel_id(self):
        """Test Usercentrics ID extraction from URL."""
        detector = UsercentricsDetector()

        pixel_id = detector.extract_pixel_id(
            "https://app.usercentrics.eu/browser-ui/latest/loader.js?settingsId=abc_123"
        )
        assert pixel_id == "abc_123"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test Usercentrics global variable detection."""
        detector = UsercentricsDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["UC_UI", "usercentrics"]

        await detector.check_global_variables(page)

        assert "UC_UI" in detector.global_variables
        assert "usercentrics" in detector.global_variables


class TestTermlyDetector:
    """Test cases for Termly consent platform detector."""

    def test_properties(self):
        """Test Termly detector properties."""
        detector = TermlyDetector()
        assert detector.pixel_type == PixelType.TERMLY
        assert "app.termly.io" in detector.tracking_domains
        assert "t_consent_status" in detector.cookie_names
        assert detector.risk_level == RiskLevel.LOW
        assert detector.hipaa_concern is False

    @pytest.mark.asyncio
    async def test_check_request(self):
        """Test Termly network request detection."""
        detector = TermlyDetector()

        request = Mock()
        request.url = "https://app.termly.io/embed.min.js?uuid=12345678-1234-1234-1234-123456789abc"

        result = await detector.check_request(request)
        assert result is True
        assert len(detector.network_requests) == 1

    def test_extract_pixel_id(self):
        """Test Termly UUID extraction from URL."""
        detector = TermlyDetector()

        pixel_id = detector.extract_pixel_id(
            "https://app.termly.io/embed.min.js?uuid=12345678-1234-1234-1234-123456789abc"
        )
        assert pixel_id == "12345678-1234-1234-1234-123456789abc"

    @pytest.mark.asyncio
    async def test_check_global_variables(self):
        """Test Termly global variable detection."""
        detector = TermlyDetector()

        page = AsyncMock(spec=Page)
        page.evaluate.return_value = ["TermlyConsent", "termly"]

        await detector.check_global_variables(page)

        assert "TermlyConsent" in detector.global_variables
        assert "termly" in detector.global_variables


class TestConsentDetectorRegistry:
    """Test that all consent detectors are properly registered."""

    def test_all_consent_detectors_registered(self):
        """Verify all 6 consent detectors are in registry."""
        from pixel_detector.detectors.registry import register_all_detectors, DETECTOR_REGISTRY

        # Register all detectors
        register_all_detectors()

        # Check consent platforms are registered
        assert "onetrust" in DETECTOR_REGISTRY
        assert "cookiebot" in DETECTOR_REGISTRY
        assert "osano" in DETECTOR_REGISTRY
        assert "trustarc" in DETECTOR_REGISTRY
        assert "usercentrics" in DETECTOR_REGISTRY
        assert "termly" in DETECTOR_REGISTRY

    def test_consent_detectors_have_low_risk(self):
        """Verify all consent detectors have LOW risk level."""
        from pixel_detector.detectors.registry import register_all_detectors, DETECTOR_REGISTRY

        register_all_detectors()

        consent_platforms = ["onetrust", "cookiebot", "osano", "trustarc", "usercentrics", "termly"]

        for platform in consent_platforms:
            detector_class = DETECTOR_REGISTRY[platform]
            detector = detector_class()
            assert detector.risk_level == RiskLevel.LOW
            assert detector.hipaa_concern is False
