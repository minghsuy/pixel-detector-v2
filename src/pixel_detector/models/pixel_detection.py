from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PixelType(str, Enum):
    META_PIXEL = "meta_pixel"
    GOOGLE_ANALYTICS = "google_analytics"
    GOOGLE_ADS = "google_ads"
    TIKTOK_PIXEL = "tiktok_pixel"
    LINKEDIN_INSIGHT = "linkedin_insight"
    TWITTER_PIXEL = "twitter_pixel"
    PINTEREST_TAG = "pinterest_tag"
    SNAPCHAT_PIXEL = "snapchat_pixel"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PixelEvidence(BaseModel):
    network_requests: list[str] = Field(default_factory=list, description="URLs of tracking requests")
    script_tags: list[str] = Field(default_factory=list, description="Script tags found in DOM")
    cookies_set: list[str] = Field(default_factory=list, description="Tracking cookies detected")
    global_variables: list[str] = Field(default_factory=list, description="Global JS variables created")
    dom_elements: list[str] = Field(default_factory=list, description="Tracking-related DOM elements")
    meta_tags: list[str] = Field(default_factory=list, description="Meta tags related to tracking")


class PixelDetection(BaseModel):
    type: PixelType
    evidence: PixelEvidence
    risk_level: RiskLevel
    hipaa_concern: bool = True
    description: str | None = None
    pixel_id: str | None = None


class ScanMetadata(BaseModel):
    page_load_time: float
    total_requests: int
    tracking_requests: int
    blocked_requests: int = 0
    scan_duration: float
    browser_used: str = "chromium"
    stealth_mode: bool = True
    errors: list[str] = Field(default_factory=list)


class ScanResult(BaseModel):
    model_config = ConfigDict()
    
    domain: str
    url_scanned: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pixels_detected: list[PixelDetection] = Field(default_factory=list)
    scan_metadata: ScanMetadata
    screenshot_path: str | None = None
    success: bool = True
    error_message: str | None = None
    
    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime) -> str:
        return timestamp.isoformat() + "Z"