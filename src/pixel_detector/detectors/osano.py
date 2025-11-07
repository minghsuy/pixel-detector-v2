import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType, RiskLevel
from .base import BasePixelDetector


class OsanoDetector(BasePixelDetector):
    """Detector for Osano consent management platform (8% market share)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.OSANO

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "cmp.osano.com",
            "api.osano.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"cmp\.osano\.com", re.IGNORECASE),
            re.compile(r"Osano", re.IGNORECASE),
            re.compile(r"osano\.consentmanager", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["osano_consentmanager", "osano_consentmanager_uuid"]

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def hipaa_concern(self) -> bool:
        return False

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Osano customer ID from URL"""
        match = re.search(r"[/]([A-Z0-9]{5,})[/]", url)
        return match.group(1) if match else None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Osano customer ID from script content"""
        match = re.search(r"cmp\.osano\.com[/]([A-Z0-9]{5,})", script)
        return match.group(1) if match else None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Osano-specific global variables"""
        osano_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof Osano !== 'undefined') vars.push('Osano');
            if (typeof osano !== 'undefined') vars.push('osano');
            return vars;
        }"""
        )
        self.global_variables.extend(osano_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Osano consent dialog elements"""
        elements = await page.evaluate(
            """() => {
            const elems = [];
            if (document.querySelector('.osano-cm-dialog')) elems.push('.osano-cm-dialog');
            if (document.querySelector('.osano-cm-widget')) elems.push('.osano-cm-widget');
            if (document.querySelector('#osano-cm-dom-info-dialog-open')) {
                elems.push('#osano-cm-dom-info-dialog-open');
            }
            return elems;
        }"""
        )
        self.dom_elements.extend(elements)

    async def check_meta_tags(self, page: Page) -> None:
        """Osano doesn't use meta tags"""
        pass
