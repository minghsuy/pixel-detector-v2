import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType, RiskLevel
from .base import BasePixelDetector


class TrustArcDetector(BasePixelDetector):
    """Detector for TrustArc consent management platform (7% market share)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.TRUSTARC

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "consent.trustarc.com",
            "consent-pref.trustarc.com",
            "trustarc.mgr.consensu.org",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"consent\.trustarc\.com", re.IGNORECASE),
            re.compile(r"truste", re.IGNORECASE),
            re.compile(r"TrustArc", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["notice_preferences", "notice_gdpr_prefs", "cmapi_cookie_privacy"]

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def hipaa_concern(self) -> bool:
        return False

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract TrustArc domain ID from URL"""
        match = re.search(r"domain=([a-z0-9-]+\.[a-z]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract TrustArc domain ID from script content"""
        match = re.search(r"consent\.trustarc\.com[/]([a-z0-9-]+)", script, re.IGNORECASE)
        return match.group(1) if match else None

    async def check_global_variables(self, page: Page) -> None:
        """Check for TrustArc-specific global variables"""
        trustarc_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof truste !== 'undefined') vars.push('truste');
            if (typeof TrustArc !== 'undefined') vars.push('TrustArc');
            return vars;
        }"""
        )
        self.global_variables.extend(trustarc_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for TrustArc consent dialog elements"""
        elements = await page.evaluate(
            """() => {
            const elems = [];
            if (document.querySelector('#truste-consent-track')) elems.push('#truste-consent-track');
            if (document.querySelector('#teconsent')) elems.push('#teconsent');
            if (document.querySelector('.truste_box_overlay')) elems.push('.truste_box_overlay');
            return elems;
        }"""
        )
        self.dom_elements.extend(elements)

    async def check_meta_tags(self, page: Page) -> None:
        """TrustArc doesn't use meta tags"""
        pass
