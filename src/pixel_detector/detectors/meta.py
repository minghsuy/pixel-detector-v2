import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class MetaPixelDetector(BasePixelDetector):
    """Detector for Meta (Facebook) Pixel"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.META_PIXEL

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "facebook.com/tr",
            "www.facebook.com/tr",
            "connect.facebook.net",
            "fbcdn.net",
            "facebook.com/signals",
            "facebook.com/v2/catalog_match",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"fbq\s*\(\s*['\"]init['\"]", re.IGNORECASE),
            re.compile(r"fbq\s*\(\s*['\"]track['\"]", re.IGNORECASE),
            re.compile(r"facebook\.com/tr\?", re.IGNORECASE),
            re.compile(r"connect\.facebook\.net.*fbevents\.js", re.IGNORECASE),
            re.compile(r"_fbq\s*=", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["_fbp", "_fbc", "fbm_", "xs", "fr", "datr"]

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Facebook Pixel ID from URL"""
        # Look for id parameter in tracking URL
        match = re.search(r"[?&]id=(\d+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Facebook Pixel ID from script content"""
        # Look for fbq('init', 'PIXEL_ID')
        match = re.search(r"fbq\s*\(\s*['\"]init['\"]\s*,\s*['\"](\d+)['\"]", script)
        if match:
            return match.group(1)
        return None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Facebook-specific global variables"""
        fb_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof fbq !== 'undefined') vars.push('fbq');
            if (typeof _fbq !== 'undefined') vars.push('_fbq');
            if (typeof FB !== 'undefined') vars.push('FB');
            if (window.fbAsyncInit) vars.push('fbAsyncInit');
            return vars;
        }"""
        )
        self.global_variables.extend(fb_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Facebook pixel noscript images"""
        noscript_pixels = await page.evaluate(
            """() => {
            const noscripts = document.querySelectorAll('noscript');
            const pixels = [];
            noscripts.forEach(ns => {
                if (ns.innerHTML.includes('facebook.com/tr')) {
                    pixels.push(ns.innerHTML.substring(0, 200));
                }
            });
            return pixels;
        }"""
        )
        self.dom_elements.extend(noscript_pixels)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for Facebook-specific meta tags"""
        fb_meta = await page.evaluate(
            """() => {
            const metas = document.querySelectorAll('meta[property^="fb:"], meta[property^="og:"]');
            return Array.from(metas).map(m => m.outerHTML);
        }"""
        )
        self.meta_tags.extend(fb_meta)