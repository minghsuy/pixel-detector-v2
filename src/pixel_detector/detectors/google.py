import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class GoogleAnalyticsDetector(BasePixelDetector):
    """Detector for Google Analytics (GA4 and Universal Analytics)"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.GOOGLE_ANALYTICS

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "google-analytics.com/analytics.js",
            "google-analytics.com/ga.js",
            "google-analytics.com/collect",
            "google-analytics.com/g/collect",
            "googletagmanager.com/gtag/js",
            "google-analytics.com/gtag/js",
            "google-analytics.com/j/collect",
            "stats.g.doubleclick.net",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"google-analytics\.com/(analytics|ga|gtag)", re.IGNORECASE),
            re.compile(r"gtag\s*\(\s*['\"]config['\"]", re.IGNORECASE),
            re.compile(r"gtag\s*\(\s*['\"]event['\"]", re.IGNORECASE),
            re.compile(r"ga\s*\(\s*['\"]create['\"]", re.IGNORECASE),
            re.compile(r"ga\s*\(\s*['\"]send['\"]", re.IGNORECASE),
            re.compile(r"_gaq\.push", re.IGNORECASE),
            re.compile(r"UA-\d+-\d+", re.IGNORECASE),  # Universal Analytics ID
            re.compile(r"G-[A-Z0-9]+", re.IGNORECASE),  # GA4 ID
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["_ga", "_gid", "_gat", "_ga_", "__utma", "__utmb", "__utmc", "__utmz", "_gac_"]

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Google Analytics ID from URL"""
        # Look for tid parameter (UA-XXXXX-X or G-XXXXXXX)
        match = re.search(r"[?&]tid=(UA-\d+-\d+|G-[A-Z0-9]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Google Analytics ID from script content"""
        # Look for UA-XXXXX-X or G-XXXXXXX
        match = re.search(r"(UA-\d+-\d+|G-[A-Z0-9]+)", script)
        if match:
            return match.group(1)
        return None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Google Analytics global variables"""
        ga_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof ga !== 'undefined') vars.push('ga');
            if (typeof gtag !== 'undefined') vars.push('gtag');
            if (typeof _gaq !== 'undefined') vars.push('_gaq');
            if (window.dataLayer) vars.push('dataLayer');
            if (window.google_tag_manager) vars.push('google_tag_manager');
            return vars;
        }"""
        )
        self.global_variables.extend(ga_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for tracker-specific DOM elements"""
        pass

    async def check_meta_tags(self, page: Page) -> None:
        """Check for tracker-specific meta tags"""
        pass


class GoogleAdsDetector(BasePixelDetector):
    """Detector for Google Ads (formerly AdWords) conversion tracking"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.GOOGLE_ADS

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "googleadservices.com/pagead/conversion",
            "google.com/pagead/conversion",
            "googleads.g.doubleclick.net",
            "googleadservices.com/pagead/conversion.js",
            "google.com/ads/ga-audiences",
            "googletagmanager.com/gtag/js",  # When used for ads
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"googleadservices\.com/pagead/conversion", re.IGNORECASE),
            re.compile(r"gtag\s*\(\s*['\"]event['\"]\s*,\s*['\"]conversion['\"]", re.IGNORECASE),
            re.compile(r"google_conversion_id", re.IGNORECASE),
            re.compile(r"google_remarketing_only", re.IGNORECASE),
            re.compile(r"AW-\d+", re.IGNORECASE),  # Google Ads ID format
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["_gcl_aw", "_gcl_dc", "_gcl_au", "IDE", "test_cookie", "NID"]

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract Google Ads ID from URL"""
        # Look for AW-XXXXXXXXX format
        match = re.search(r"AW-\d+", url)
        if match:
            return match.group(0)
        # Also check for conversion ID
        match = re.search(r"[?&]id=(\d+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract Google Ads ID from script content"""
        # Look for AW-XXXXXXXXX
        match = re.search(r"AW-\d+", script)
        if match:
            return match.group(0)
        # Look for google_conversion_id
        match = re.search(r"google_conversion_id['\"]?\s*[:=]\s*['\"]?(\d+)", script)
        if match:
            return match.group(1)
        return None

    async def check_global_variables(self, page: Page) -> None:
        """Check for Google Ads global variables"""
        ads_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof google_trackConversion !== 'undefined') vars.push('google_trackConversion');
            if (window.google_conversion_id) vars.push('google_conversion_id');
            if (window.google_remarketing_only) vars.push('google_remarketing_only');
            return vars;
        }"""
        )
        self.global_variables.extend(ads_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for Google Ads conversion tracking images"""
        conversion_imgs = await page.evaluate(
            """() => {
            const imgs = document.querySelectorAll('img[src*="googleadservices.com/pagead/conversion"]');
            return Array.from(imgs).map(img => img.outerHTML);
        }"""
        )
        self.dom_elements.extend(conversion_imgs)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for tracker-specific meta tags"""
        pass