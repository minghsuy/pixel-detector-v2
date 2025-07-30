import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class TikTokPixelDetector(BasePixelDetector):
    """Detector for TikTok Pixel"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.TIKTOK_PIXEL

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "analytics.tiktok.com",
            "business-api.tiktok.com",
            "partners.tiktok.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"analytics\.tiktok\.com", re.IGNORECASE),
            re.compile(r"business-api\.tiktok\.com", re.IGNORECASE),
            re.compile(r"partners\.tiktok\.com", re.IGNORECASE),
            re.compile(r"ttq\s*\(\s*['\"]init['\"]\s*,", re.IGNORECASE),
            re.compile(r"ttq\s*\(\s*['\"]track['\"]\s*,", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["_ttp", "ttwid", "ttclid"]


    async def check_global_variables(self, page: Page) -> None:
        """Check for TikTok-specific global variables"""
        tiktok_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof ttq !== 'undefined') vars.push('ttq');
            if (typeof window.ttq !== 'undefined') vars.push('window.ttq');
            if (window.partners && window.partners.tiktok) vars.push('window.partners.tiktok');
            return vars;
        }"""
        )
        self.global_variables.extend(tiktok_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for TikTok pixel noscript images"""
        noscript_pixels = await page.evaluate(
            """() => {
            const noscripts = document.querySelectorAll('noscript');
            const pixels = [];
            noscripts.forEach(ns => {
                if (ns.innerHTML.includes('analytics.tiktok.com') || 
                    ns.innerHTML.includes('business-api.tiktok.com')) {
                    pixels.push(ns.innerHTML.substring(0, 200));
                }
            });
            return pixels;
        }"""
        )
        self.dom_elements.extend(noscript_pixels)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for TikTok-specific meta tags"""
        # TikTok doesn't typically use meta tags for tracking
        pass

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract TikTok pixel ID from URL"""
        # Look for pixel_code parameter in tracking URL
        match = re.search(r"[?&]pixel_code=([^&]+)", url)
        if match:
            return match.group(1)
        # Also check for ttclid
        match = re.search(r"ttclid=([^&]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract TikTok pixel ID from script content"""
        # Look for ttq('init', 'PIXEL_ID')
        match = re.search(r"ttq\s*\(\s*['\"]init['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*[,)]", script)
        if match:
            return match.group(1)
        return None

