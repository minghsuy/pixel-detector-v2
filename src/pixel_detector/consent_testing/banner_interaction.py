"""Banner interaction testing module.

This module performs the actual consent banner tests: baseline, reject, and accept.
"""

import time
from datetime import datetime

from playwright.async_api import Page

from ..detectors.base import BasePixelDetector
from ..models.consent_test import (
    ConsentAction,
    ConsentCompliance,
    ConsentTestEvidence,
    ConsentTestResult,
    TimelineEvent,
    ViolationSeverity,
)
from .button_selectors import BannerSelector
from .compliance_checker import ComplianceChecker


class BannerInteractionTester:
    """Performs consent banner interaction tests."""

    def __init__(self, page: Page, detectors: list[BasePixelDetector]):
        """Initialize the tester.

        Args:
            page: Playwright Page object
            detectors: List of pixel detectors to use for tracking detection
        """
        self.page = page
        self.detectors = detectors
        self.selector = BannerSelector(page)
        self.checker = ComplianceChecker()
        self.test_start_time = 0.0
        self.timeline: list[TimelineEvent] = []

    def _record_event(self, event_type: str, details: str, pixel_type: str | None = None) -> None:
        """Record an event in the timeline.

        Args:
            event_type: Type of event (page_load, tracker_fired, button_clicked, etc.)
            details: Human-readable details
            pixel_type: Pixel type if this is a tracker event
        """
        elapsed = time.time() - self.test_start_time
        self.timeline.append(
            TimelineEvent(
                timestamp_seconds=round(elapsed, 2),
                event_type=event_type,
                details=details,
                pixel_type=pixel_type,
            )
        )

    def _get_detected_pixels(self) -> list[str]:
        """Get list of currently detected pixel types.

        Returns:
            List of pixel type names that have been detected
        """
        detected = []
        for detector in self.detectors:
            if detector.is_detected():
                detected.append(detector.pixel_type.value)
        return detected

    def _get_tracking_cookies(self) -> list[str]:
        """Get list of tracking cookies currently set.

        Returns:
            List of tracking cookie names
        """
        # This would need to check cookies from detectors
        # For now, simplified implementation
        cookies: list[str] = []
        for detector in self.detectors:
            if hasattr(detector, "cookies_found") and detector.cookies_found:
                cookies.extend(detector.cookies_found)
        return list(set(cookies))

    def _count_tracking_requests(self) -> int:
        """Count number of tracking requests made.

        Returns:
            Total count of tracking requests
        """
        count = 0
        for detector in self.detectors:
            if hasattr(detector, "network_requests"):
                count += len(detector.network_requests)
        return count

    async def baseline_test(self) -> ConsentTestResult:
        """Perform baseline test: load page, don't interact, see what tracks.

        This detects dark patterns where tracking fires before user consent.

        Returns:
            ConsentTestResult for the baseline test
        """
        self.test_start_time = time.time()
        self.timeline = []
        self._record_event("test_start", "Baseline test started (no interaction)")

        try:
            # Wait for banner to appear (don't interact with it)
            banner_found, platform = await self.selector.wait_for_banner(timeout_ms=5000)

            if banner_found:
                self._record_event("banner_detected", f"Consent banner detected: {platform}")
            else:
                self._record_event("no_banner", "No consent banner detected within 5 seconds")

            # Wait a bit longer to catch any delayed tracking
            await self.page.wait_for_timeout(3000)
            self._record_event("wait_complete", "Waited 3 seconds for tracking to fire")

            # Capture what has fired
            pixels_detected = self._get_detected_pixels()
            cookies = self._get_tracking_cookies()
            request_count = self._count_tracking_requests()

            # Record each detected pixel
            for pixel in pixels_detected:
                if pixel not in ["onetrust", "cookiebot", "osano", "trustarc", "usercentrics", "termly"]:
                    self._record_event("tracker_fired", f"{pixel} detected before consent", pixel_type=pixel)

            # Build evidence
            evidence = ConsentTestEvidence(
                action_taken=ConsentAction.BASELINE,
                banner_detected=banner_found,
                banner_platform=platform,
                button_clicked=False,
                button_selector_used=None,
                pixels_before_interaction=pixels_detected,
                pixels_after_interaction=[],
                cookies_before=cookies,
                cookies_after=[],
                tracking_requests_before=request_count,
                tracking_requests_after=0,
                timeline=self.timeline,
                test_duration_seconds=round(time.time() - self.test_start_time, 2),
                banner_wait_timeout=not banner_found,
            )

            # Calculate compliance
            score, compliance, severity = self.checker.calculate_test_score(evidence, ConsentAction.BASELINE)
            violations = self.checker.determine_violations(pixels_detected, [], ConsentAction.BASELINE)
            recommendation = self.checker.generate_recommendations(violations, platform)

            return ConsentTestResult(
                test_type=ConsentAction.BASELINE,
                compliance_status=compliance,
                violation_severity=severity,
                evidence=evidence,
                compliance_score=score,
                violations_detected=violations,
                recommendation=recommendation,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            # Test failed - return inconclusive result
            error_evidence = ConsentTestEvidence(
                action_taken=ConsentAction.BASELINE,
                banner_detected=False,
                button_clicked=False,
                test_duration_seconds=round(time.time() - self.test_start_time, 2),
                error_message=str(e),
            )

            return ConsentTestResult(
                test_type=ConsentAction.BASELINE,
                compliance_status=ConsentCompliance.INCONCLUSIVE,
                violation_severity=ViolationSeverity.MEDIUM,
                evidence=error_evidence,
                compliance_score=50,
                violations_detected=[f"Test error: {str(e)}"],
                recommendation="Manual verification required",
            )

    async def reject_all_test(self) -> ConsentTestResult:
        """Perform reject all test: click reject button, verify no tracking.

        This is the critical test for GDPR/CCPA compliance.

        Returns:
            ConsentTestResult for the reject test
        """
        self.test_start_time = time.time()
        self.timeline = []
        self._record_event("test_start", "Reject All test started")

        try:
            # Wait for banner
            banner_found, platform = await self.selector.wait_for_banner(timeout_ms=5000)

            if not banner_found:
                self._record_event("no_banner", "No consent banner detected")
                error_evidence = ConsentTestEvidence(
                    action_taken=ConsentAction.REJECT_ALL,
                    banner_detected=False,
                    button_clicked=False,
                    test_duration_seconds=round(time.time() - self.test_start_time, 2),
                    banner_wait_timeout=True,
                )

                return ConsentTestResult(
                    test_type=ConsentAction.REJECT_ALL,
                    compliance_status=ConsentCompliance.MISSING,
                    violation_severity=ViolationSeverity.HIGH,
                    evidence=error_evidence,
                    compliance_score=0,
                    violations_detected=["No consent banner detected"],
                    recommendation="Implement consent management platform",
                )

            self._record_event("banner_detected", f"Consent banner detected: {platform}")

            # Type guard: platform must be str if banner was found
            assert platform is not None, "Platform should not be None when banner is found"

            # Capture state before interaction
            pixels_before = self._get_detected_pixels()
            cookies_before = self._get_tracking_cookies()
            requests_before = self._count_tracking_requests()

            # Find and click reject button
            button_found, selector = await self.selector.find_button(platform, "reject_all")

            if not button_found:
                self._record_event("button_not_found", f"Reject button not found for {platform}")
                error_evidence = ConsentTestEvidence(
                    action_taken=ConsentAction.REJECT_ALL,
                    banner_detected=True,
                    banner_platform=platform,
                    button_clicked=False,
                    pixels_before_interaction=pixels_before,
                    cookies_before=cookies_before,
                    tracking_requests_before=requests_before,
                    test_duration_seconds=round(time.time() - self.test_start_time, 2),
                    click_failed=True,
                )

                return ConsentTestResult(
                    test_type=ConsentAction.REJECT_ALL,
                    compliance_status=ConsentCompliance.INCONCLUSIVE,
                    violation_severity=ViolationSeverity.MEDIUM,
                    evidence=error_evidence,
                    compliance_score=50,
                    violations_detected=[f"Could not find reject button for {platform}"],
                    recommendation="Manual testing required - button selectors may need updating",
                )

            # Type guard: selector must be str if button was found
            assert selector is not None, "Selector should not be None when button is found"

            # Click the button
            click_success = await self.selector.click_button_with_retry(selector)

            if not click_success:
                self._record_event("click_failed", f"Failed to click button: {selector}")
                error_evidence = ConsentTestEvidence(
                    action_taken=ConsentAction.REJECT_ALL,
                    banner_detected=True,
                    banner_platform=platform,
                    button_clicked=False,
                    button_selector_used=selector,
                    pixels_before_interaction=pixels_before,
                    cookies_before=cookies_before,
                    tracking_requests_before=requests_before,
                    test_duration_seconds=round(time.time() - self.test_start_time, 2),
                    click_failed=True,
                )

                return ConsentTestResult(
                    test_type=ConsentAction.REJECT_ALL,
                    compliance_status=ConsentCompliance.INCONCLUSIVE,
                    violation_severity=ViolationSeverity.MEDIUM,
                    evidence=error_evidence,
                    compliance_score=50,
                    violations_detected=["Button click failed"],
                    recommendation="Manual testing required",
                )

            self._record_event("button_clicked", f"Clicked reject button: {selector}")

            # Wait for rejection to take effect
            await self.page.wait_for_timeout(2000)
            self._record_event("wait_after_click", "Waited 2 seconds after rejection")

            # Capture state after rejection
            pixels_after = self._get_detected_pixels()
            cookies_after = self._get_tracking_cookies()
            requests_after = self._count_tracking_requests()

            # Record any new tracking
            new_pixels = [p for p in pixels_after if p not in pixels_before]
            for pixel in new_pixels:
                if pixel not in ["onetrust", "cookiebot", "osano", "trustarc", "usercentrics", "termly"]:
                    self._record_event("tracker_after_reject", f"{pixel} fired AFTER rejection", pixel_type=pixel)

            evidence = ConsentTestEvidence(
                action_taken=ConsentAction.REJECT_ALL,
                banner_detected=True,
                banner_platform=platform,
                button_clicked=True,
                button_selector_used=selector,
                pixels_before_interaction=pixels_before,
                pixels_after_interaction=new_pixels,
                cookies_before=cookies_before,
                cookies_after=[c for c in cookies_after if c not in cookies_before],
                tracking_requests_before=requests_before,
                tracking_requests_after=requests_after - requests_before,
                timeline=self.timeline,
                test_duration_seconds=round(time.time() - self.test_start_time, 2),
            )

            # Calculate compliance
            score, compliance, severity = self.checker.calculate_test_score(evidence, ConsentAction.REJECT_ALL)
            violations = self.checker.determine_violations(pixels_before, new_pixels, ConsentAction.REJECT_ALL)
            recommendation = self.checker.generate_recommendations(violations, platform)

            return ConsentTestResult(
                test_type=ConsentAction.REJECT_ALL,
                compliance_status=compliance,
                violation_severity=severity,
                evidence=evidence,
                compliance_score=score,
                violations_detected=violations,
                recommendation=recommendation,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            self._record_event("test_error", f"Test failed: {str(e)}")
            error_evidence = ConsentTestEvidence(
                action_taken=ConsentAction.REJECT_ALL,
                banner_detected=False,
                button_clicked=False,
                test_duration_seconds=round(time.time() - self.test_start_time, 2),
                error_message=str(e),
                timeline=self.timeline,
            )

            return ConsentTestResult(
                test_type=ConsentAction.REJECT_ALL,
                compliance_status=ConsentCompliance.INCONCLUSIVE,
                violation_severity=ViolationSeverity.MEDIUM,
                evidence=error_evidence,
                compliance_score=50,
                violations_detected=[f"Test error: {str(e)}"],
                recommendation="Manual verification required",
            )

    async def accept_all_test(self) -> ConsentTestResult:
        """Perform accept all test: click accept, verify tracking works.

        This validates our detection is working correctly.

        Returns:
            ConsentTestResult for the accept test
        """
        self.test_start_time = time.time()
        self.timeline = []
        self._record_event("test_start", "Accept All test started")

        try:
            # Wait for banner
            banner_found, platform = await self.selector.wait_for_banner(timeout_ms=5000)

            if not banner_found:
                self._record_event("no_banner", "No consent banner detected")
                # For accept test, no banner just means we skip this test
                evidence = ConsentTestEvidence(
                    action_taken=ConsentAction.ACCEPT_ALL,
                    banner_detected=False,
                    button_clicked=False,
                    test_duration_seconds=round(time.time() - self.test_start_time, 2),
                    banner_wait_timeout=True,
                )

                return ConsentTestResult(
                    test_type=ConsentAction.ACCEPT_ALL,
                    compliance_status=ConsentCompliance.INCONCLUSIVE,
                    violation_severity=ViolationSeverity.NONE,
                    evidence=evidence,
                    compliance_score=100,  # Not a violation
                    violations_detected=[],
                    recommendation="No consent banner detected - test skipped",
                )

            self._record_event("banner_detected", f"Consent banner detected: {platform}")

            # Type guard: platform must be str if banner was found
            assert platform is not None, "Platform should not be None when banner is found"

            # Find and click accept button
            button_found, selector = await self.selector.find_button(platform, "accept_all")

            if button_found:
                assert selector is not None, "Selector should not be None when button is found"
                await self.selector.click_button_with_retry(selector)
                self._record_event("button_clicked", f"Clicked accept button: {selector}")

                # Wait for acceptance to take effect
                await self.page.wait_for_timeout(2000)
                self._record_event("wait_after_click", "Waited 2 seconds after acceptance")

            pixels_after = self._get_detected_pixels()
            cookies_after = self._get_tracking_cookies()
            requests_after = self._count_tracking_requests()

            evidence = ConsentTestEvidence(
                action_taken=ConsentAction.ACCEPT_ALL,
                banner_detected=True,
                banner_platform=platform,
                button_clicked=button_found,
                button_selector_used=selector if button_found else None,
                pixels_after_interaction=pixels_after,
                cookies_after=cookies_after,
                tracking_requests_after=requests_after,
                timeline=self.timeline,
                test_duration_seconds=round(time.time() - self.test_start_time, 2),
            )

            # Accept test is always compliant (validates detection)
            return ConsentTestResult(
                test_type=ConsentAction.ACCEPT_ALL,
                compliance_status=ConsentCompliance.COMPLIANT,
                violation_severity=ViolationSeverity.NONE,
                evidence=evidence,
                compliance_score=100,
                violations_detected=[],
                recommendation="Tracking functions correctly after consent",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            self._record_event("test_error", f"Test failed: {str(e)}")
            error_evidence = ConsentTestEvidence(
                action_taken=ConsentAction.ACCEPT_ALL,
                banner_detected=False,
                button_clicked=False,
                test_duration_seconds=round(time.time() - self.test_start_time, 2),
                error_message=str(e),
                timeline=self.timeline,
            )

            return ConsentTestResult(
                test_type=ConsentAction.ACCEPT_ALL,
                compliance_status=ConsentCompliance.INCONCLUSIVE,
                violation_severity=ViolationSeverity.NONE,
                evidence=error_evidence,
                compliance_score=100,  # Accept test failure is not a violation
                violations_detected=[],
                recommendation="Test error (not a compliance issue)",
            )
