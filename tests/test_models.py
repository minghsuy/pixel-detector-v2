import pytest
from datetime import datetime
from pixel_detector.models import (
    PixelType,
    RiskLevel,
    PixelEvidence,
    PixelDetection,
    ScanMetadata,
    ScanResult,
)


def test_pixel_evidence_creation():
    """Test PixelEvidence model creation"""
    evidence = PixelEvidence(
        network_requests=["https://facebook.com/tr?id=123"],
        script_tags=["<script>fbq('init', '123')</script>"],
        cookies_set=["_fbp", "_fbc"],
    )
    
    assert len(evidence.network_requests) == 1
    assert len(evidence.script_tags) == 1
    assert len(evidence.cookies_set) == 2
    assert evidence.global_variables == []


def test_pixel_detection_creation():
    """Test PixelDetection model creation"""
    evidence = PixelEvidence()
    detection = PixelDetection(
        type=PixelType.META_PIXEL,
        evidence=evidence,
        risk_level=RiskLevel.HIGH,
        hipaa_concern=True,
        description="Test detection",
        pixel_id="123456789",
    )
    
    assert detection.type == PixelType.META_PIXEL
    assert detection.risk_level == RiskLevel.HIGH
    assert detection.hipaa_concern is True
    assert detection.pixel_id == "123456789"


def test_scan_result_creation():
    """Test ScanResult model creation"""
    metadata = ScanMetadata(
        page_load_time=2.5,
        total_requests=100,
        tracking_requests=5,
        scan_duration=10.0,
    )
    
    result = ScanResult(
        domain="example.com",
        url_scanned="https://example.com",
        pixels_detected=[],
        scan_metadata=metadata,
    )
    
    assert result.domain == "example.com"
    assert result.success is True
    assert result.error_message is None
    assert isinstance(result.timestamp, datetime)


def test_scan_result_json_serialization():
    """Test JSON serialization of ScanResult"""
    metadata = ScanMetadata(
        page_load_time=2.5,
        total_requests=100,
        tracking_requests=5,
        scan_duration=10.0,
    )
    
    result = ScanResult(
        domain="example.com",
        url_scanned="https://example.com",
        pixels_detected=[],
        scan_metadata=metadata,
    )
    
    # Test that it can be serialized to dict
    result_dict = result.model_dump()
    assert result_dict["domain"] == "example.com"
    assert "timestamp" in result_dict
    
    # Test JSON encoding
    import json
    json_str = json.dumps(result_dict, default=str)
    assert "example.com" in json_str