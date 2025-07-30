import re
from re import Pattern

from playwright.async_api import Page

from ..models import PixelType
from .base import BasePixelDetector


class LinkedInInsightDetector(BasePixelDetector):
    """Detector for LinkedIn Insight Tag"""

    @property
    def pixel_type(self) -> PixelType:
        return PixelType.LINKEDIN_INSIGHT

    @property
    def tracking_domains(self) -> list[str]:
        return [
            "px.ads.linkedin.com",
            "analytics.linkedin.com",
            "snap.licdn.com",
        ]

    @property
    def script_patterns(self) -> list[Pattern[str]]:
        return [
            re.compile(r"px\.ads\.linkedin\.com", re.IGNORECASE),
            re.compile(r"analytics\.linkedin\.com", re.IGNORECASE),
            re.compile(r"_linkedin_partner_id", re.IGNORECASE),
            re.compile(r"_linkedin_data_partner_ids", re.IGNORECASE),
            re.compile(r"snap\.licdn\.com/li\.lms-analytics", re.IGNORECASE),
        ]

    @property
    def cookie_names(self) -> list[str]:
        return ["li_fat_id", "lidc", "bcookie", "li_sugr", "UserMatchHistory"]


    async def check_global_variables(self, page: Page) -> None:
        """Check for LinkedIn-specific global variables"""
        linkedin_vars = await page.evaluate(
            """() => {
            const vars = [];
            if (typeof _linkedin_partner_id !== 'undefined') vars.push('_linkedin_partner_id');
            if (typeof window._linkedin_partner_id !== 'undefined') vars.push('window._linkedin_partner_id');
            if (typeof _linkedin_data_partner_ids !== 'undefined') vars.push('_linkedin_data_partner_ids');
            if (typeof window._linkedin_data_partner_ids !== 'undefined') {
                vars.push('window._linkedin_data_partner_ids');
            }
            return vars;
        }"""
        )
        self.global_variables.extend(linkedin_vars)

    async def check_dom_elements(self, page: Page) -> None:
        """Check for LinkedIn Insight Tag noscript images"""
        noscript_pixels = await page.evaluate(
            """() => {
            const noscripts = document.querySelectorAll('noscript');
            const pixels = [];
            noscripts.forEach(ns => {
                if (ns.innerHTML.includes('px.ads.linkedin.com')) {
                    pixels.push(ns.innerHTML.substring(0, 200));
                }
            });
            // Also check for img tags directly
            const imgs = document.querySelectorAll('img[src*="px.ads.linkedin.com"]');
            imgs.forEach(img => {
                pixels.push(img.outerHTML);
            });
            return pixels;
        }"""
        )
        self.dom_elements.extend(noscript_pixels)

    async def check_meta_tags(self, page: Page) -> None:
        """Check for LinkedIn-specific meta tags"""
        # LinkedIn doesn't typically use meta tags for tracking
        pass

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract LinkedIn partner ID from URL"""
        # Look for partner ID in URL
        match = re.search(r"[?&]pid=(\d+)", url)
        if match:
            return match.group(1)
        # LinkedIn uses li_fat_id parameter
        match = re.search(r"li_fat_id=([^&]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract LinkedIn partner ID from script content"""
        # Look for _linkedin_partner_id = 'ID'
        match = re.search(r"_linkedin_partner_id\s*=\s*['\"]?(\d+)['\"]?", script)
        if match:
            return match.group(1)
        return None

