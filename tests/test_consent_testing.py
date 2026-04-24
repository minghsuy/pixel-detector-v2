"""Tests for consent banner interaction testing (Phase 2)."""

from datetime import datetime

from pixel_detector.consent_testing.compliance_checker import ComplianceChecker
from pixel_detector.models.consent_test import (
    ConsentAction,
    ConsentCompliance,
    ConsentComplianceSummary,
    ConsentTestEvidence,
    ConsentTestResult,
    TimelineEvent,
    ViolationSeverity,
)


class TestConsentTestModels:
    """Test consent testing data models."""

    def test_timeline_event_creation(self) -> None:
        """Test TimelineEvent model creation."""
        event = TimelineEvent(
            timestamp_seconds=1.23,
            event_type="tracker_fired",
            details="Google Analytics detected",
            pixel_type="google_analytics"
        )

        assert event.timestamp_seconds == 1.23
        assert event.event_type == "tracker_fired"
        assert event.details == "Google Analytics detected"
        assert event.pixel_type == "google_analytics"

    def test_consent_test_evidence_baseline(self) -> None:
        """Test ConsentTestEvidence for baseline test."""
        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.BASELINE,
            banner_detected=True,
            banner_platform="cookiebot",
            button_clicked=False,
            pixels_before_interaction=["google_analytics", "cookiebot"],
            pixels_after_interaction=[],
            cookies_before=["_ga", "_gid"],
            cookies_after=[],
            tracking_requests_before=2,
            tracking_requests_after=0,
            test_duration_seconds=5.5,
        )

        assert evidence.action_taken == ConsentAction.BASELINE
        assert evidence.banner_detected is True
        assert evidence.banner_platform == "cookiebot"
        assert len(evidence.pixels_before_interaction) == 2
        assert evidence.button_clicked is False

    def test_consent_test_evidence_reject(self) -> None:
        """Test ConsentTestEvidence for reject test."""
        timeline = [
            TimelineEvent(
                timestamp_seconds=0.5,
                event_type="banner_detected",
                details="Cookiebot banner found"
            ),
            TimelineEvent(
                timestamp_seconds=1.2,
                event_type="button_clicked",
                details="Clicked reject button"
            ),
        ]

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.REJECT_ALL,
            banner_detected=True,
            banner_platform="cookiebot",
            button_clicked=True,
            button_selector_used="#CybotCookiebotDialogBodyButtonDecline",
            pixels_before_interaction=["cookiebot"],
            pixels_after_interaction=[],
            cookies_before=[],
            cookies_after=[],
            tracking_requests_before=0,
            tracking_requests_after=0,
            timeline=timeline,
            test_duration_seconds=3.5,
        )

        assert evidence.action_taken == ConsentAction.REJECT_ALL
        assert evidence.button_clicked is True
        assert evidence.button_selector_used is not None
        assert len(evidence.timeline) == 2
        assert len(evidence.pixels_after_interaction) == 0

    def test_consent_test_result_compliant(self) -> None:
        """Test ConsentTestResult for compliant scenario."""
        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.REJECT_ALL,
            banner_detected=True,
            button_clicked=True,
            test_duration_seconds=2.0,
        )

        result = ConsentTestResult(
            test_type=ConsentAction.REJECT_ALL,
            compliance_status=ConsentCompliance.COMPLIANT,
            violation_severity=ViolationSeverity.NONE,
            evidence=evidence,
            compliance_score=100,
            violations_detected=[],
            recommendation="Site properly blocks tracking after rejection",
            timestamp=datetime.utcnow(),
        )

        assert result.test_type == ConsentAction.REJECT_ALL
        assert result.compliance_status == ConsentCompliance.COMPLIANT
        assert result.compliance_score == 100
        assert len(result.violations_detected) == 0

    def test_consent_test_result_malfunctioning(self) -> None:
        """Test ConsentTestResult for malfunctioning scenario."""
        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.BASELINE,
            banner_detected=True,
            button_clicked=False,
            pixels_before_interaction=["google_analytics"],
            test_duration_seconds=3.0,
        )

        result = ConsentTestResult(
            test_type=ConsentAction.BASELINE,
            compliance_status=ConsentCompliance.MALFUNCTIONING,
            violation_severity=ViolationSeverity.CRITICAL,
            evidence=evidence,
            compliance_score=0,
            violations_detected=["Google Analytics fired before consent given (dark pattern)"],
            recommendation="Move all tracking scripts behind consent check",
            timestamp=datetime.utcnow(),
        )

        assert result.test_type == ConsentAction.BASELINE
        assert result.compliance_status == ConsentCompliance.MALFUNCTIONING
        assert result.compliance_score == 0
        assert len(result.violations_detected) == 1
        assert result.violation_severity == ViolationSeverity.CRITICAL

    def test_consent_compliance_summary(self) -> None:
        """Test ConsentComplianceSummary model."""
        summary = ConsentComplianceSummary(
            overall_score=33,
            overall_status=ConsentCompliance.MISSING,
            banner_platform="cookiebot",
            critical_violations=2,
            primary_issue="Tracking before consent",
            recommended_action="DECLINE - Critical consent violations",
        )

        assert summary.overall_score == 33
        assert summary.overall_status == ConsentCompliance.MISSING
        assert summary.banner_platform == "cookiebot"
        assert summary.critical_violations == 2
        assert summary.primary_issue == "Tracking before consent"
        assert "DECLINE" in summary.recommended_action


class TestComplianceChecker:
    """Test compliance checking logic."""

    def test_calculate_score_average(self) -> None:
        """Test score calculation averages test scores."""
        checker = ComplianceChecker()

        # Create test results with different scores
        baseline_evidence = ConsentTestEvidence(
            action_taken=ConsentAction.BASELINE,
            banner_detected=True,
            button_clicked=False,
            test_duration_seconds=2.0,
        )
        baseline_result = ConsentTestResult(
            test_type=ConsentAction.BASELINE,
            compliance_status=ConsentCompliance.MALFUNCTIONING,
            violation_severity=ViolationSeverity.CRITICAL,
            evidence=baseline_evidence,
            compliance_score=0,
            violations_detected=["Tracking before consent"],
            recommendation="Fix tracking",
        )

        reject_evidence = ConsentTestEvidence(
            action_taken=ConsentAction.REJECT_ALL,
            banner_detected=True,
            button_clicked=True,
            test_duration_seconds=2.0,
        )
        reject_result = ConsentTestResult(
            test_type=ConsentAction.REJECT_ALL,
            compliance_status=ConsentCompliance.MISSING,
            violation_severity=ViolationSeverity.HIGH,
            evidence=reject_evidence,
            compliance_score=0,
            violations_detected=["No banner"],
            recommendation="Add banner",
        )

        accept_evidence = ConsentTestEvidence(
            action_taken=ConsentAction.ACCEPT_ALL,
            banner_detected=True,
            button_clicked=True,
            test_duration_seconds=2.0,
        )
        accept_result = ConsentTestResult(
            test_type=ConsentAction.ACCEPT_ALL,
            compliance_status=ConsentCompliance.COMPLIANT,
            violation_severity=ViolationSeverity.NONE,
            evidence=accept_evidence,
            compliance_score=100,
            violations_detected=[],
            recommendation="Good",
        )

        summary = checker.build_summary([baseline_result, reject_result, accept_result])

        # Average should be (0 + 0 + 100) / 3 = 33.33, rounded to 33
        assert summary.overall_score == 33

    def test_determine_violations_baseline(self) -> None:
        """Test violation detection for baseline test."""
        checker = ComplianceChecker()

        pixels_before = ["google_analytics", "cookiebot"]
        pixels_after = []

        violations = checker.determine_violations(pixels_before, pixels_after, ConsentAction.BASELINE)

        # Should detect google_analytics as violation (cookiebot is consent platform, not violation)
        assert len(violations) == 1
        # Violation messages have spaces and title case
        assert "google analytics" in violations[0].lower()
        assert "before consent" in violations[0].lower()

    def test_determine_violations_reject(self) -> None:
        """Test violation detection for reject test."""
        checker = ComplianceChecker()

        pixels_before = ["cookiebot"]
        pixels_after = ["google_analytics"]  # New tracking after rejection!

        violations = checker.determine_violations(pixels_before, pixels_after, ConsentAction.REJECT_ALL)

        # Should detect google_analytics firing after rejection
        assert len(violations) == 1
        # Violation messages have spaces and title case
        assert "google analytics" in violations[0].lower()
        assert "after" in violations[0].lower() or "rejection" in violations[0].lower()

    def test_generate_recommendations(self) -> None:
        """Test recommendation generation."""
        checker = ComplianceChecker()

        violations = [
            "Google Analytics fired before consent given (dark pattern)",
            "Meta Pixel detected before user interaction"
        ]

        recommendation = checker.generate_recommendations(violations, "cookiebot")

        assert recommendation is not None
        assert "tracking" in recommendation.lower() or "consent" in recommendation.lower()

    def test_calculate_test_score_baseline_clean(self) -> None:
        """Test scoring for baseline test with no pre-consent tracking."""
        checker = ComplianceChecker()

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.BASELINE,
            banner_detected=True,
            button_clicked=False,
            pixels_before_interaction=["cookiebot"],  # Only consent platform
            pixels_after_interaction=[],
            test_duration_seconds=2.0,
        )

        score, compliance, severity = checker.calculate_test_score(evidence, ConsentAction.BASELINE)

        assert score == 100
        assert compliance == ConsentCompliance.COMPLIANT
        assert severity == ViolationSeverity.NONE

    def test_calculate_test_score_baseline_dark_pattern(self) -> None:
        """Test scoring for baseline test with dark pattern."""
        checker = ComplianceChecker()

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.BASELINE,
            banner_detected=True,
            button_clicked=False,
            pixels_before_interaction=["google_analytics", "cookiebot"],  # Tracking before consent!
            pixels_after_interaction=[],
            test_duration_seconds=2.0,
        )

        score, compliance, severity = checker.calculate_test_score(evidence, ConsentAction.BASELINE)

        # Score uses gradual penalty: max(0, 100 - (1 * 30)) = 70 for 1 tracking pixel
        assert score == 70
        assert compliance == ConsentCompliance.MALFUNCTIONING
        assert severity == ViolationSeverity.HIGH

    def test_calculate_test_score_reject_compliant(self) -> None:
        """Test scoring for reject test that properly blocks tracking."""
        checker = ComplianceChecker()

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.REJECT_ALL,
            banner_detected=True,
            button_clicked=True,
            pixels_before_interaction=["cookiebot"],
            pixels_after_interaction=[],  # No new tracking after rejection
            test_duration_seconds=2.0,
        )

        score, compliance, severity = checker.calculate_test_score(evidence, ConsentAction.REJECT_ALL)

        assert score == 100
        assert compliance == ConsentCompliance.COMPLIANT
        assert severity == ViolationSeverity.NONE

    def test_calculate_test_score_reject_violation(self) -> None:
        """Test scoring for reject test that fails to block tracking."""
        checker = ComplianceChecker()

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.REJECT_ALL,
            banner_detected=True,
            button_clicked=True,
            pixels_before_interaction=["cookiebot"],
            pixels_after_interaction=["google_analytics"],  # Tracking despite rejection!
            test_duration_seconds=2.0,
        )

        score, compliance, severity = checker.calculate_test_score(evidence, ConsentAction.REJECT_ALL)

        assert score == 0
        assert compliance == ConsentCompliance.MALFUNCTIONING
        assert severity == ViolationSeverity.CRITICAL

    def test_calculate_test_score_reject_no_banner(self) -> None:
        """Test scoring for reject test when banner is missing."""
        checker = ComplianceChecker()

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.REJECT_ALL,
            banner_detected=False,  # No banner found
            button_clicked=False,
            test_duration_seconds=2.0,
        )

        score, compliance, severity = checker.calculate_test_score(evidence, ConsentAction.REJECT_ALL)

        # When button not clicked (no banner found), returns INCONCLUSIVE with score 50
        assert score == 50
        assert compliance == ConsentCompliance.INCONCLUSIVE
        assert severity == ViolationSeverity.MEDIUM

    def test_calculate_test_score_accept(self) -> None:
        """Test scoring for accept test (always passes)."""
        checker = ComplianceChecker()

        evidence = ConsentTestEvidence(
            action_taken=ConsentAction.ACCEPT_ALL,
            banner_detected=True,
            button_clicked=True,
            pixels_after_interaction=["google_analytics"],
            test_duration_seconds=2.0,
        )

        score, compliance, severity = checker.calculate_test_score(evidence, ConsentAction.ACCEPT_ALL)

        assert score == 100
        assert compliance == ConsentCompliance.COMPLIANT
        assert severity == ViolationSeverity.NONE


class TestButtonSelectors:
    """Test button selector functionality."""

    def test_platform_selectors_defined(self) -> None:
        """Test that platform selectors are properly defined."""
        from pixel_detector.consent_testing.button_selectors import PLATFORM_SELECTORS

        # Verify all 6 platforms are defined
        assert "onetrust" in PLATFORM_SELECTORS
        assert "cookiebot" in PLATFORM_SELECTORS
        assert "osano" in PLATFORM_SELECTORS
        assert "trustarc" in PLATFORM_SELECTORS
        assert "usercentrics" in PLATFORM_SELECTORS
        assert "termly" in PLATFORM_SELECTORS

    def test_selector_structure(self) -> None:
        """Test that selectors have proper structure."""
        from pixel_detector.consent_testing.button_selectors import PLATFORM_SELECTORS

        for platform, config in PLATFORM_SELECTORS.items():
            # Each platform should have reject and accept button lists
            assert hasattr(config, "reject_all")
            assert hasattr(config, "accept_all")
            assert hasattr(config, "banner_container")

            # Lists should not be empty
            assert len(config.reject_all) > 0
            assert len(config.accept_all) > 0
            assert len(config.banner_container) > 0

            # All should be strings (CSS selectors)
            assert all(isinstance(s, str) for s in config.reject_all)
            assert all(isinstance(s, str) for s in config.accept_all)
            assert all(isinstance(s, str) for s in config.banner_container)
