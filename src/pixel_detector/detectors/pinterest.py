import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class PinterestTagDetector(BasePixelDetector):
    """Detector for Pinterest Tag"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.PINTEREST_TAG

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "ct.pinterest.com",
            "s.pinimg.com/ct",
            "analytics.pinterest.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"ct\.pinterest\.com", re.IGNORECASE),
            re.compile(r"s\.pinimg\.com/ct/core\.js", re.IGNORECASE),
            re.compile(r"pintrk\s*\(\s*['\"]load['\"]\s*,", re.IGNORECASE),
            re.compile(r"pintrk\s*\(\s*['\"]track['\"]\s*,", re.IGNORECASE),
            re.compile(r"pintrk\s*\(\s*['\"]page['\"]\s*\)", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return [
            "_pinterest_ct",
            "_pinterest_ct_rt",
            "_epik",
            "_derived_epik",
            "_pin_unauth",
            "_pinterest_ct_ua",
        ]


    async def check_global_variables(self, page: Page) -> None:
        """Check for Pinterest-specific global variables"""
        pinterest_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof pintrk !== 'undefined') vars.push('pintrk');
            if (typeof window.pintrk !== 'undefined') vars.push('window.pintrk');
            if (window.pintrk && Array.isArray(window.pintrk.queue)) vars.push('window.pintrk.queue');
            return vars;
        }"""
        )
        self.global_variables.extend(pinterest_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Pinterest Tag noscript images"""
        noscript_pixels = await page.evaluate(
            """() => {
            const noscripts = document.querySelectorAll('noscript');
            const pixels = [];
            noscripts.forEach(ns => {
                if (ns.innerHTML.includes('ct.pinterest.com')) {
                    pixels.push(ns.innerHTML.substring(0, 200));
                }
            });
            // Also check for img tags directly
            const imgs = document.querySelectorAll('img[src*="ct.pinterest.com"]');
            imgs.forEach(img => {
                pixels.push(img.outerHTML);
            });
            return pixels;
        }"""
        )
        self.dom_elements.extend(noscript_pixels)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for Pinterest-specific meta tags"""
        pinterest_meta = await page.evaluate(
            """() => {
            const metas = document.querySelectorAll('meta[name="p:domain_verify"], meta[property^="pinterest:"]');
            return Array.from(metas).map(m => m.outerHTML);
        }"""
        )
        self.meta_tags.extend(pinterest_meta)

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Pinterest Tag ID from URL"""
        # Check for tid parameter
        match = re.search(r"[?&]tid=([^&]+)", url)
        if match:
            return match.group(1)
        # Check for tag ID in path
        match = re.search(r"/v3/tid/(\d+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Pinterest Tag ID from script content"""
        # Look for pintrk('load', 'TAG_ID')
        match = re.search(r"pintrk\s*\(\s*['\"]load['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*[,)]", script)
        if match:
            return match.group(1)
        return None

