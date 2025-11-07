import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType, RiskLevel
from .base import BasePixelDetector


class TermlyDetector(BasePixelDetector):
    """Detector for Termly consent management platform (3% market share)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.TERMLY

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "app.termly.io",
            "consent.termly.io",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"app\.termly\.io", re.IGNORECASE),
            re.compile(r"TermlyConsent", re.IGNORECASE),
            re.compile(r"termly", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["t_consent_status", "termly-consent-preferences"]

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def hipaa_concern(self) -> bool:
        return False

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Termly website UUID from URL"""
        match = re.search(r"uuid=([a-f0-9-]{36})", url, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Termly website UUID from script content"""
        match = re.search(r"data-website-uuid['\"]?\s*[:=]\s*['\"]?([a-f0-9-]{36})", script, re.IGNORECASE)
        return match.group(1) if match else None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Termly-specific global variables"""
        termly_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof TermlyConsent !== 'undefined') vars.push('TermlyConsent');
            if (typeof termly !== 'undefined') vars.push('termly');
            return vars;
        }"""
        )
        self.global_variables.extend(termly_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Termly consent banner elements"""
        elements = await page.evaluate(
            """() => {
            const elems = [];
            if (document.querySelector('#termly-code-snippet-support')) {
                elems.push('#termly-code-snippet-support');
            }
            if (document.querySelector('.termly-styles-module')) elems.push('.termly-styles-module');
            if (document.querySelector('[data-termly-banner]')) elems.push('[data-termly-banner]');
            return elems;
        }"""
        )
        self.dom_elements.extend(elements)

    async def check_meta_tags(self, page: Page) -> None:
        """Termly doesn't use meta tags"""
        pass
