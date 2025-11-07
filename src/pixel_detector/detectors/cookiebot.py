import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType, RiskLevel
from .base import BasePixelDetector


class CookieBotDetector(BasePixelDetector):
    """Detector for Cookiebot consent management platform (15% market share)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.COOKIEBOT

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "consent.cookiebot.com",
            "cookiebot.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"consent\.cookiebot\.com", re.IGNORECASE),
            re.compile(r"Cookiebot", re.IGNORECASE),
            re.compile(r"CookieConsent", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["CookieConsent", "CookieConsentBulkSetting"]

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def hipaa_concern(self) -> bool:
        return False

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Cookiebot ID from URL"""
        match = re.search(r"cbid=([a-f0-9-]+)", url)
        return match.group(1) if match else None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Cookiebot ID from script content"""
        match = re.search(r"data-cbid['\"]?\s*[:=]\s*['\"]?([a-f0-9-]+)", script)
        return match.group(1) if match else None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Cookiebot-specific global variables"""
        cookiebot_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof Cookiebot !== 'undefined') vars.push('Cookiebot');
            if (typeof CookieConsent !== 'undefined') vars.push('CookieConsent');
            return vars;
        }"""
        )
        self.global_variables.extend(cookiebot_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Cookiebot consent banner elements"""
        elements = await page.evaluate(
            """() => {
            const elems = [];
            if (document.querySelector('#CybotCookiebotDialog')) elems.push('#CybotCookiebotDialog');
            if (document.querySelector('#CookiebotWidget')) elems.push('#CookiebotWidget');
            if (document.querySelector('.CybotCookiebotDialogBodyLevelButtonCustom')) {
                elems.push('.CybotCookiebotDialogBodyLevelButtonCustom');
            }
            return elems;
        }"""
        )
        self.dom_elements.extend(elements)

    async def check_meta_tags(self, page: Page) -> None:
        """Cookiebot doesn't use meta tags"""
        pass
