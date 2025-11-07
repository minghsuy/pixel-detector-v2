import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType, RiskLevel
from .base import BasePixelDetector


class UsercentricsDetector(BasePixelDetector):
    """Detector for Usercentrics consent management platform (5% market share)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.USERCENTRICS

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "app.usercentrics.eu",
            "privacy-proxy.usercentrics.eu",
            "aggregator.service.usercentrics.eu",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"app\.usercentrics\.eu", re.IGNORECASE),
            re.compile(r"UC_UI", re.IGNORECASE),
            re.compile(r"usercentrics", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["uc_user_interaction", "uc_settings"]

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def hipaa_concern(self) -> bool:
        return False

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Usercentrics settings ID from URL"""
        match = re.search(r"settingsId=([a-zA-Z0-9_-]+)", url)
        return match.group(1) if match else None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Usercentrics settings ID from script content"""
        match = re.search(r"data-settings-id['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_-]+)", script)
        return match.group(1) if match else None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Usercentrics-specific global variables"""
        usercentrics_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof UC_UI !== 'undefined') vars.push('UC_UI');
            if (typeof usercentrics !== 'undefined') vars.push('usercentrics');
            if (typeof __ucCmp !== 'undefined') vars.push('__ucCmp');
            return vars;
        }"""
        )
        self.global_variables.extend(usercentrics_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Usercentrics consent layer elements"""
        elements = await page.evaluate(
            """() => {
            const elems = [];
            if (document.querySelector('#usercentrics-root')) elems.push('#usercentrics-root');
            if (document.querySelector('[data-usercentrics]')) elems.push('[data-usercentrics]');
            if (document.querySelector('.uc-embedding')) elems.push('.uc-embedding');
            return elems;
        }"""
        )
        self.dom_elements.extend(elements)

    async def check_meta_tags(self, page: Page) -> None:
        """Usercentrics doesn't use meta tags"""
        pass
