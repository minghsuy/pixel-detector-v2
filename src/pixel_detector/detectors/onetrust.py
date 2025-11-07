import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType, RiskLevel
from .base import BasePixelDetector


class OneTrustDetector(BasePixelDetector):
    """Detector for OneTrust consent management platform (40% market share)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.ONETRUST

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "cdn.cookielaw.org",
            "optanon.blob.core.windows.net",
            "cookie-cdn.cookiepro.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"cdn\.cookielaw\.org", re.IGNORECASE),
            re.compile(r"OneTrust", re.IGNORECASE),
            re.compile(r"OptanonWrapper", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["OptanonConsent", "OptanonAlertBoxClosed"]

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW  # Consent tools are compliance, not violations

    @property
    def hipaa_concern(self) -> bool:
        return False  # CMPs don't violate HIPAA

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract OneTrust domain script ID from URL"""
        match = re.search(r"domainScript=([a-f0-9-]+)", url)
        return match.group(1) if match else None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract OneTrust domain script ID from script content"""
        match = re.search(r"data-domain-script['\"]?\s*[:=]\s*['\"]?([a-f0-9-]+)", script)
        return match.group(1) if match else None

    async def check_global_variables(self, page: Page) -> None:
        """Check for OneTrust-specific global variables"""
        onetrust_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof OneTrust !== 'undefined') vars.push('OneTrust');
            if (typeof OptanonWrapper !== 'undefined') vars.push('OptanonWrapper');
            if (typeof OnetrustActiveGroups !== 'undefined') vars.push('OnetrustActiveGroups');
            return vars;
        }"""
        )
        self.global_variables.extend(onetrust_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for OneTrust consent banner elements"""
        elements = await page.evaluate(
            """() => {
            const elems = [];
            if (document.querySelector('#onetrust-consent-sdk')) elems.push('#onetrust-consent-sdk');
            if (document.querySelector('#onetrust-banner-sdk')) elems.push('#onetrust-banner-sdk');
            if (document.querySelector('.optanon-alert-box-wrapper')) elems.push('.optanon-alert-box-wrapper');
            return elems;
        }"""
        )
        self.dom_elements.extend(elements)

    async def check_meta_tags(self, page: Page) -> None:
        """OneTrust doesn't use meta tags"""
        pass
