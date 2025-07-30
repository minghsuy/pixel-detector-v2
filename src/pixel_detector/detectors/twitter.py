import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class TwitterPixelDetector(BasePixelDetector):
    """Detector for Twitter/X Pixel"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.TWITTER_PIXEL

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "analytics.twitter.com",
            "ads-twitter.com",
            "t.co/i/adsct",
            "static.ads-twitter.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"analytics\.twitter\.com", re.IGNORECASE),
            re.compile(r"static\.ads-twitter\.com/uwt\.js", re.IGNORECASE),
            re.compile(r"platform\.twitter\.com/oct\.js", re.IGNORECASE),
            re.compile(r"t\.co/i/adsct", re.IGNORECASE),
            re.compile(r"twttr\.conversion\.trackPid", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["personalization_id", "guest_id", "ct0", "auth_token"]


    async def check_global_variables(self, page: Page) -> None:
        """Check for Twitter-specific global variables"""
        twitter_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof twttr !== 'undefined') vars.push('twttr');
            if (typeof window.twttr !== 'undefined') vars.push('window.twttr');
            if (window.twttr && window.twttr.conversion) vars.push('window.twttr.conversion');
            if (typeof twq !== 'undefined') vars.push('twq');
            return vars;
        }"""
        )
        self.global_variables.extend(twitter_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Twitter pixel noscript images"""
        noscript_pixels = await page.evaluate(
            """() => {
            const noscripts = document.querySelectorAll('noscript');
            const pixels = [];
            noscripts.forEach(ns => {
                if (ns.innerHTML.includes('analytics.twitter.com') || 
                    ns.innerHTML.includes('t.co/i/adsct') ||
                    ns.innerHTML.includes('ads-twitter.com')) {
                    pixels.push(ns.innerHTML.substring(0, 200));
                }
            });
            // Also check for img tags directly
            const imgs = document.querySelectorAll('img[src*="analytics.twitter.com"], img[src*="t.co/i/adsct"]');
            imgs.forEach(img => {
                pixels.push(img.outerHTML);
            });
            return pixels;
        }"""
        )
        self.dom_elements.extend(noscript_pixels)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for Twitter-specific meta tags"""
        twitter_meta = await page.evaluate(
            """() => {
            const metas = document.querySelectorAll('meta[name^="twitter:"]');
            return Array.from(metas).map(m => m.outerHTML);
        }"""
        )
        self.meta_tags.extend(twitter_meta)

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Twitter pixel ID from URL"""
        # Twitter uses txn_id parameter
        match = re.search(r"txn_id=([^&]+)", url)
        if match:
            return match.group(1)
        # Also check for p_id parameter
        match = re.search(r"[?&]p_id=([^&]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Twitter pixel ID from script content"""
        # Look for twq('init', 'PIXEL_ID')
        match = re.search(r"twq\s*\(\s*['\"]init['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", script)
        if match:
            return match.group(1)
        return None

