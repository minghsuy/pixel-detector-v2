"""Button selectors for 6 major consent management platforms.

This module defines CSS selectors for finding "Reject All" and "Accept All"
buttons across different CMP implementations.
"""

from dataclasses import dataclass

from playwright.async_api import Page


@dataclass
class ButtonConfig:
    """Configuration for finding consent buttons on a specific CMP platform."""

    reject_all: list[str]  # CSS selectors for "Reject All" button
    accept_all: list[str]  # CSS selectors for "Accept All" button
    banner_container: list[str]  # CSS selectors for banner element
    requires_two_step: bool = False  # Some CMPs need confirmation clicks
    second_step_confirm: list[str] | None = None  # Confirmation button selectors


# Selector configurations for 6 major CMPs
PLATFORM_SELECTORS: dict[str, ButtonConfig] = {
    "onetrust": ButtonConfig(
        reject_all=[
            "button#onetrust-reject-all-handler",
            "button.onetrust-close-btn-handler[aria-label*='reject' i]",
            "button.ot-sdk-btn[data-reject='true']",
            "button.ot-pc-refuse-all-handler",
        ],
        accept_all=[
            "button#onetrust-accept-btn-handler",
            "button.onetrust-close-btn-handler[aria-label*='accept' i]",
            "button#accept-recommended-btn-handler",
        ],
        banner_container=[
            "#onetrust-consent-sdk",
            "#onetrust-banner-sdk",
            ".ot-sdk-container",
        ],
    ),
    "cookiebot": ButtonConfig(
        reject_all=[
            "a#CybotCookiebotDialogBodyButtonDecline",
            "a#CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll",
            "a.CybotCookiebotDialogBodyButton:has-text('Decline')",
        ],
        accept_all=[
            "a#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            "a#CybotCookiebotDialogBodyButtonAccept",
            "a.CybotCookiebotDialogBodyButton:has-text('Accept')",
        ],
        banner_container=[
            "#CybotCookiebotDialog",
            "#CookiebotWidget",
            "[id^='Cookiebot']",
        ],
    ),
    "trustarc": ButtonConfig(
        reject_all=[
            "button.truste-button2",  # Typically the "Reject" button
            "a.rejectAll",
            "button[onclick*='reject']",
            "#truste-consent-button[value='reject']",
        ],
        accept_all=[
            "button.truste-button1",  # Typically the "Accept" button
            "a.acceptAll",
            "#truste-consent-button[value='accept']",
        ],
        banner_container=[
            "#truste-consent-track",
            "#teconsent",
            ".truste_box_overlay",
            "#consent-tracker",
        ],
    ),
    "osano": ButtonConfig(
        reject_all=[
            "button.osano-cm-dialog__close",
            "button.osano-cm-reject",
            "button[data-action='reject']",
            ".osano-cm-buttons button:has-text('Deny')",
        ],
        accept_all=[
            "button.osano-cm-accept-all",
            "button.osano-cm-accept",
            "button[data-action='accept']",
            ".osano-cm-buttons button:has-text('Allow')",
        ],
        banner_container=[
            ".osano-cm-dialog",
            ".osano-cm-widget",
            "[class*='osano-cm']",
        ],
    ),
    "usercentrics": ButtonConfig(
        reject_all=[
            "button[data-testid='uc-deny-all-button']",
            "button.uc-btn-deny-all",
            "button[aria-label*='Deny' i]",
        ],
        accept_all=[
            "button[data-testid='uc-accept-all-button']",
            "button.uc-btn-accept-all",
            "button[aria-label*='Accept' i]",
        ],
        banner_container=[
            "#usercentrics-root",
            "[data-usercentrics]",
            "[id^='usercentrics']",
        ],
    ),
    "termly": ButtonConfig(
        reject_all=[
            "button#t-declined-btn",
            "button.t-decline-button",
            "button[aria-label*='decline' i]",
        ],
        accept_all=[
            "button#t-accept-btn",
            "button.t-accept-button",
            "button[aria-label*='accept' i]",
        ],
        banner_container=[
            "#termly-code-snippet-support",
            "[data-termly-banner]",
            "[id*='termly']",
        ],
    ),
}


class BannerSelector:
    """Helper class for detecting and interacting with consent banners."""

    def __init__(self, page: Page):
        self.page = page

    async def detect_banner(self, timeout_ms: int = 5000) -> str | None:
        """Detect which CMP banner is present on the page.

        Args:
            timeout_ms: Maximum time to wait for banner to appear

        Returns:
            Platform name (e.g., "onetrust") or None if no banner detected
        """
        # Check each platform's banner container
        for platform_name, config in PLATFORM_SELECTORS.items():
            for selector in config.banner_container:
                try:
                    element = await self.page.wait_for_selector(
                        selector, timeout=timeout_ms, state="visible"
                    )
                    if element:
                        return platform_name
                except Exception:
                    # Selector not found, try next one
                    continue

        return None

    async def find_button(
        self, platform: str, action: str, timeout_ms: int = 2000
    ) -> tuple[bool, str | None]:
        """Find the button for the specified action on the detected platform.

        Args:
            platform: Platform name (e.g., "onetrust")
            action: Either "reject_all" or "accept_all"
            timeout_ms: Time to wait for button

        Returns:
            Tuple of (button_found: bool, selector_that_worked: str | None)
        """
        if platform not in PLATFORM_SELECTORS:
            return False, None

        config = PLATFORM_SELECTORS[platform]
        selectors = config.reject_all if action == "reject_all" else config.accept_all

        # Try each selector until one works
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(
                    selector, timeout=timeout_ms, state="visible"
                )
                if element and await element.is_visible():
                    return True, selector
            except Exception:
                # Selector didn't work, try next one
                continue

        return False, None

    async def click_button_with_retry(
        self, selector: str, max_attempts: int = 3
    ) -> bool:
        """Click a button with retry logic.

        Args:
            selector: CSS selector for the button
            max_attempts: Maximum number of click attempts

        Returns:
            True if click succeeded, False otherwise
        """
        for attempt in range(max_attempts):
            try:
                await self.page.click(selector, timeout=2000)
                # Wait a moment for any animations/confirmation
                await self.page.wait_for_timeout(500)
                return True
            except Exception:
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    return False
                # Try again with force click
                try:
                    await self.page.click(selector, force=True, timeout=1000)
                    await self.page.wait_for_timeout(500)
                    return True
                except Exception:
                    # Force click also failed, continue to next attempt
                    continue

        return False

    async def wait_for_banner(self, timeout_ms: int = 5000) -> tuple[bool, str | None]:
        """Wait for any consent banner to appear.

        Args:
            timeout_ms: Maximum time to wait

        Returns:
            Tuple of (banner_found: bool, platform_name: str | None)
        """
        platform = await self.detect_banner(timeout_ms=timeout_ms)
        if platform:
            return True, platform
        return False, None
