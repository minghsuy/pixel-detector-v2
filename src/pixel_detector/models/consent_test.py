"""Data models for consent management testing.

This module defines models for testing consent banner interactions and
detecting malfunctioning consent mechanisms (comparable to BitSight's
consent management feature).
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ConsentAction(str, Enum):
    """Type of consent interaction performed."""

    BASELINE = "baseline"  # No interaction - detect dark patterns
    REJECT_ALL = "reject_all"  # User clicks reject - should block tracking
    ACCEPT_ALL = "accept_all"  # User clicks accept - tracking allowed


class ConsentCompliance(str, Enum):
    """Compliance status of consent mechanism."""

    COMPLIANT = "compliant"  # Respects user choice correctly
    MALFUNCTIONING = "malfunctioning"  # Consent exists but doesn't work
    MISSING = "missing"  # No consent banner detected
    INCONCLUSIVE = "inconclusive"  # Test couldn't complete


class ViolationSeverity(str, Enum):
    """Severity level of consent violations."""

    CRITICAL = "critical"  # Explicit violation (e.g., tracking after rejection)
    HIGH = "high"  # Dark pattern (e.g., tracking before consent)
    MEDIUM = "medium"  # Configuration issues
    LOW = "low"  # Minor issues
    NONE = "none"  # No violations detected


class TimelineEvent(BaseModel):
    """Single event in the consent test timeline."""

    timestamp_seconds: float = Field(description="Seconds since page load started")
    event_type: str = Field(description="Type of event (page_load, tracker_fired, button_clicked, etc.)")
    details: str = Field(description="Human-readable event details")
    pixel_type: str | None = Field(default=None, description="Pixel type if tracker event")


class ConsentTestEvidence(BaseModel):
    """Evidence collected during consent testing."""

    model_config = ConfigDict()

    action_taken: ConsentAction
    banner_detected: bool
    banner_platform: str | None = Field(default=None, description="CMP platform name (onetrust, cookiebot, etc.)")
    button_clicked: bool
    button_selector_used: str | None = Field(default=None, description="CSS selector that worked")

    # Tracking detection
    pixels_before_interaction: list[str] = Field(
        default_factory=list, description="Pixel types detected before interaction"
    )
    pixels_after_interaction: list[str] = Field(
        default_factory=list, description="Pixel types detected after interaction"
    )
    cookies_before: list[str] = Field(default_factory=list, description="Tracking cookies before interaction")
    cookies_after: list[str] = Field(default_factory=list, description="Tracking cookies after interaction")

    tracking_requests_before: int = Field(default=0, description="Number of tracking requests before interaction")
    tracking_requests_after: int = Field(default=0, description="Number of tracking requests after interaction")

    # Detailed timeline
    timeline: list[TimelineEvent] = Field(default_factory=list, description="Chronological event timeline")

    # Test execution details
    test_duration_seconds: float = Field(default=0.0, description="How long the test took")
    banner_wait_timeout: bool = Field(default=False, description="True if banner didn't appear within timeout")
    click_failed: bool = Field(default=False, description="True if button click failed")
    error_message: str | None = Field(default=None, description="Error details if test failed")


class ConsentTestResult(BaseModel):
    """Result of a single consent test (baseline, reject, or accept)."""

    model_config = ConfigDict()

    test_type: ConsentAction
    compliance_status: ConsentCompliance
    violation_severity: ViolationSeverity
    evidence: ConsentTestEvidence

    # Scoring and violations
    compliance_score: int = Field(ge=0, le=100, description="0-100 compliance score")
    violations_detected: list[str] = Field(default_factory=list, description="Human-readable violation descriptions")
    recommendation: str | None = Field(default=None, description="Actionable recommendation to fix issues")

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime) -> str:
        return timestamp.isoformat() + "Z"


class ConsentComplianceSummary(BaseModel):
    """Overall consent compliance summary across all tests."""

    model_config = ConfigDict()

    overall_score: int = Field(ge=0, le=100, description="Average score across all tests")
    overall_status: ConsentCompliance = Field(description="Worst case status from all tests")
    critical_violations: int = Field(default=0, description="Number of critical violations found")

    tests_passed: int = Field(default=0, description="Number of compliant tests")
    tests_failed: int = Field(default=0, description="Number of non-compliant tests")
    tests_inconclusive: int = Field(default=0, description="Number of inconclusive tests")

    primary_issue: str | None = Field(default=None, description="Most serious issue detected")
    banner_platform: str | None = Field(default=None, description="Detected CMP platform")

    # Risk assessment
    risk_level: ViolationSeverity = Field(
        default=ViolationSeverity.NONE, description="Overall risk level for underwriting"
    )
    recommended_action: str | None = Field(default=None, description="What underwriter should do")
