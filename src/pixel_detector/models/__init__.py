from .consent_test import (
    ConsentAction,
    ConsentCompliance,
    ConsentComplianceSummary,
    ConsentTestEvidence,
    ConsentTestResult,
    TimelineEvent,
    ViolationSeverity,
)
from .pixel_detection import (
    PixelDetection,
    PixelEvidence,
    PixelType,
    RiskLevel,
    ScanMetadata,
    ScanResult,
)

# Rebuild ScanResult model after consent test models are imported
ScanResult.model_rebuild()

__all__ = [
    # Pixel detection models
    "PixelDetection",
    "PixelEvidence",
    "PixelType",
    "RiskLevel",
    "ScanMetadata",
    "ScanResult",
    # Consent testing models
    "ConsentAction",
    "ConsentCompliance",
    "ConsentComplianceSummary",
    "ConsentTestEvidence",
    "ConsentTestResult",
    "TimelineEvent",
    "ViolationSeverity",
]