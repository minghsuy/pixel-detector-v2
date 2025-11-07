"""Compliance checker for consent banner testing.

This module calculates compliance scores and generates violation reports
for consent management platform testing.
"""

from ..models.consent_test import (
    ConsentAction,
    ConsentCompliance,
    ConsentComplianceSummary,
    ConsentTestResult,
    ViolationSeverity,
)


class ComplianceChecker:
    """Analyzes consent test results and calculates compliance scores."""

    # Tracking pixel types that require consent
    TRACKING_PIXELS = {
        "meta_pixel",
        "google_analytics",
        "google_ads",
        "tiktok_pixel",
        "linkedin_insight",
        "twitter_pixel",
        "pinterest_tag",
        "snapchat_pixel",
    }

    def calculate_score(self, test_results: list[ConsentTestResult]) -> int:
        """Calculate overall compliance score from all test results.

        Args:
            test_results: List of consent test results

        Returns:
            Score from 0-100 (100 = fully compliant)
        """
        if not test_results:
            return 0

        total_score = sum(result.compliance_score for result in test_results)
        return total_score // len(test_results)

    def determine_violations(
        self,
        pixels_before: list[str],
        pixels_after: list[str],
        action: ConsentAction,
    ) -> list[str]:
        """Generate human-readable violation descriptions.

        Args:
            pixels_before: Pixel types detected before interaction
            pixels_after: Pixel types detected after interaction
            action: Type of action performed

        Returns:
            List of violation descriptions
        """
        violations = []

        # Filter to only tracking pixels (not consent platforms)
        tracking_before = [p for p in pixels_before if p in self.TRACKING_PIXELS]
        tracking_after = [p for p in pixels_after if p in self.TRACKING_PIXELS]

        if action == ConsentAction.BASELINE:
            # Dark pattern: tracking fires before user interaction
            if tracking_before:
                for pixel in tracking_before:
                    violations.append(
                        f"{pixel.replace('_', ' ').title()} fired before consent given (dark pattern)"
                    )

        elif action == ConsentAction.REJECT_ALL:
            # Critical violation: tracking continues after rejection
            if tracking_after:
                for pixel in tracking_after:
                    violations.append(
                        f"{pixel.replace('_', ' ').title()} continued tracking after rejection (critical violation)"
                    )

        elif action == ConsentAction.ACCEPT_ALL:
            # This is expected behavior - no violations
            pass

        return violations

    def generate_recommendations(
        self,
        violations: list[str],
        platform: str | None,
    ) -> str:
        """Generate actionable fix recommendations.

        Args:
            violations: List of detected violations
            platform: Detected CMP platform name

        Returns:
            Recommendation string
        """
        if not violations:
            return "Consent mechanism is functioning correctly"

        recommendations = []

        # Check violation types
        has_baseline_violations = any("before consent" in v for v in violations)
        has_rejection_violations = any("after rejection" in v for v in violations)

        if has_baseline_violations:
            recommendations.append(
                "Move all tracking scripts behind consent check - they should not load until user accepts"
            )

        if has_rejection_violations:
            if platform:
                recommendations.append(
                    f"Implement proper {platform.capitalize()} consent signal integration - "
                    f"tracking scripts must check consent status before firing"
                )
            else:
                recommendations.append(
                    "Tracking scripts must check consent status before firing - currently ignoring rejection"
                )

        if has_baseline_violations or has_rejection_violations:
            recommendations.append(
                "Test implementation with European IP address to ensure GDPR compliance"
            )

        return " | ".join(recommendations)

    def calculate_test_score(
        self, evidence, action: ConsentAction
    ) -> tuple[int, ConsentCompliance, ViolationSeverity]:
        """Calculate score for a single test.

        Args:
            evidence: ConsentTestEvidence object
            action: Type of action performed

        Returns:
            Tuple of (score, compliance_status, severity)
        """
        # Filter to tracking pixels only
        tracking_before = [p for p in evidence.pixels_before_interaction if p in self.TRACKING_PIXELS]
        tracking_after = [p for p in evidence.pixels_after_interaction if p in self.TRACKING_PIXELS]

        if action == ConsentAction.BASELINE:
            # Baseline test: should have NO tracking before interaction
            if not evidence.banner_detected:
                # No banner = missing consent mechanism
                return 0, ConsentCompliance.MISSING, ViolationSeverity.HIGH

            if tracking_before:
                # Dark pattern: immediate tracking
                score = max(0, 100 - (len(tracking_before) * 30))
                return score, ConsentCompliance.MALFUNCTIONING, ViolationSeverity.HIGH
            else:
                # Good: no tracking before consent
                return 100, ConsentCompliance.COMPLIANT, ViolationSeverity.NONE

        elif action == ConsentAction.REJECT_ALL:
            # Reject test: NO tracking should occur after rejection
            if not evidence.button_clicked:
                # Couldn't click button - test inconclusive
                return 50, ConsentCompliance.INCONCLUSIVE, ViolationSeverity.MEDIUM

            if tracking_after:
                # CRITICAL: tracking after explicit rejection
                return 0, ConsentCompliance.MALFUNCTIONING, ViolationSeverity.CRITICAL
            else:
                # Good: no tracking after rejection
                return 100, ConsentCompliance.COMPLIANT, ViolationSeverity.NONE

        elif action == ConsentAction.ACCEPT_ALL:
            # Accept test: tracking SHOULD work (this validates detection)
            if not evidence.button_clicked:
                return 50, ConsentCompliance.INCONCLUSIVE, ViolationSeverity.MEDIUM

            # For accept test, we expect tracking to work
            # Not having tracking isn't necessarily bad (could be privacy-first site)
            # But having tracking confirms our detection works
            return 100, ConsentCompliance.COMPLIANT, ViolationSeverity.NONE

        return 50, ConsentCompliance.INCONCLUSIVE, ViolationSeverity.MEDIUM

    def build_summary(
        self, test_results: list[ConsentTestResult]
    ) -> ConsentComplianceSummary:
        """Build overall consent compliance summary from test results.

        Args:
            test_results: List of all consent test results

        Returns:
            ConsentComplianceSummary object
        """
        if not test_results:
            return ConsentComplianceSummary(
                overall_score=0,
                overall_status=ConsentCompliance.INCONCLUSIVE,
                critical_violations=0,
                tests_passed=0,
                tests_failed=0,
                tests_inconclusive=0,
            )

        overall_score = self.calculate_score(test_results)

        # Count test outcomes
        tests_passed = sum(
            1 for r in test_results if r.compliance_status == ConsentCompliance.COMPLIANT
        )
        tests_failed = sum(
            1
            for r in test_results
            if r.compliance_status in [ConsentCompliance.MALFUNCTIONING, ConsentCompliance.MISSING]
        )
        tests_inconclusive = sum(
            1 for r in test_results if r.compliance_status == ConsentCompliance.INCONCLUSIVE
        )

        # Count critical violations
        critical_violations = sum(
            1
            for r in test_results
            if r.violation_severity == ViolationSeverity.CRITICAL
        )

        # Determine worst-case status
        if any(r.compliance_status == ConsentCompliance.MALFUNCTIONING for r in test_results):
            overall_status = ConsentCompliance.MALFUNCTIONING
        elif any(r.compliance_status == ConsentCompliance.MISSING for r in test_results):
            overall_status = ConsentCompliance.MISSING
        elif all(r.compliance_status == ConsentCompliance.COMPLIANT for r in test_results):
            overall_status = ConsentCompliance.COMPLIANT
        else:
            overall_status = ConsentCompliance.INCONCLUSIVE

        # Determine highest severity
        max_severity = ViolationSeverity.NONE
        for result in test_results:
            if result.violation_severity == ViolationSeverity.CRITICAL:
                max_severity = ViolationSeverity.CRITICAL
                break
            elif result.violation_severity == ViolationSeverity.HIGH and max_severity == ViolationSeverity.NONE:
                max_severity = ViolationSeverity.HIGH
            elif result.violation_severity == ViolationSeverity.MEDIUM and max_severity in [
                ViolationSeverity.NONE,
                ViolationSeverity.LOW,
            ]:
                max_severity = ViolationSeverity.MEDIUM

        # Find primary issue
        primary_issue = None
        for result in test_results:
            if result.violations_detected:
                primary_issue = result.violations_detected[0]
                break

        # Get platform name
        banner_platform = None
        for result in test_results:
            if result.evidence.banner_platform:
                banner_platform = result.evidence.banner_platform
                break

        # Determine recommended action for underwriters
        if overall_score >= 90:
            recommended_action = "ACCEPT - Consent mechanism functioning correctly"
        elif overall_score >= 70:
            recommended_action = "REVIEW - Minor consent issues detected, verify configuration"
        elif overall_score >= 40:
            recommended_action = "DECLINE or INCREASE PREMIUM - Significant consent violations detected"
        else:
            recommended_action = "DECLINE - Critical consent violations, high risk of privacy lawsuits"

        return ConsentComplianceSummary(
            overall_score=overall_score,
            overall_status=overall_status,
            critical_violations=critical_violations,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_inconclusive=tests_inconclusive,
            primary_issue=primary_issue,
            banner_platform=banner_platform,
            risk_level=max_severity,
            recommended_action=recommended_action,
        )
