import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class SnapchatPixelDetector(BasePixelDetector):
    """Detector for Snapchat Pixel"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.SNAPCHAT_PIXEL

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "sc-static.net",
            "tr.snapchat.com",
            "app.snapchat.com",
            "snap.licdn.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"sc-static\.net/scevent\.min\.js", re.IGNORECASE),
            re.compile(r"tr\.snapchat\.com", re.IGNORECASE),
            re.compile(r"snaptr\s*\(\s*['\"]init['\"]\s*,", re.IGNORECASE),
            re.compile(r"snaptr\s*\(\s*['\"]track['\"]\s*,", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["_scid", "_sctr", "sc_at"]


    async def check_global_variables(self, page: Page) -> None:
        """Check for Snapchat-specific global variables"""
        snapchat_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof snaptr !== 'undefined') vars.push('snaptr');
            if (typeof window.snaptr !== 'undefined') vars.push('window.snaptr');
            return vars;
        }"""
        )
        self.global_variables.extend(snapchat_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Snapchat Pixel noscript images"""
        noscript_pixels = await page.evaluate(
            """() => {
            const noscripts = document.querySelectorAll('noscript');
            const pixels = [];
            noscripts.forEach(ns => {
                if (ns.innerHTML.includes('tr.snapchat.com')) {
                    pixels.push(ns.innerHTML.substring(0, 200));
                }
            });
            // Also check for img tags directly
            const imgs = document.querySelectorAll('img[src*="tr.snapchat.com"]');
            imgs.forEach(img => {
                pixels.push(img.outerHTML);
            });
            return pixels;
        }"""
        )
        self.dom_elements.extend(noscript_pixels)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for Snapchat-specific meta tags"""
        # Snapchat doesn't typically use meta tags for tracking
        pass

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Snapchat Pixel ID from URL"""
        # Check for pixel ID in URL
        match = re.search(r"[?&]p=([^&]+)", url)
        if match:
            return match.group(1)
        # Check for account ID
        match = re.search(r"[?&]account_id=([^&]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Snapchat Pixel ID from script content"""
        # Look for snaptr('init', 'PIXEL_ID')
        match = re.search(r"snaptr\s*\(\s*['\"]init['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*[,)]", script)
        if match:
            return match.group(1)
        return None

