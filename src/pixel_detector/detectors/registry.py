
from .base import BasePixelDetector
from .google import GoogleAdsDetector, GoogleAnalyticsDetector
from .linkedin import LinkedInInsightDetector
from .meta import MetaPixelDetector
from .pinterest import PinterestTagDetector
from .snapchat import SnapchatPixelDetector
from .tiktok import TikTokPixelDetector
from .twitter import TwitterPixelDetector

# Global registry of pixel detectors
DETECTOR_REGISTRY: dict[str, type[BasePixelDetector]] = {}


def register_detector(name: str, detector_class: type[BasePixelDetector]) -> None:
    """Register a pixel detector"""
    DETECTOR_REGISTRY[name] = detector_class


def get_all_detectors() -> list[BasePixelDetector]:
    """Get instances of all registered detectors"""
    return [detector_class() for detector_class in DETECTOR_REGISTRY.values()]


def register_all_detectors() -> None:
    """Register all built-in detectors"""
    register_detector("meta_pixel", MetaPixelDetector)
    register_detector("google_analytics", GoogleAnalyticsDetector)
    register_detector("google_ads", GoogleAdsDetector)
    register_detector("tiktok_pixel", TikTokPixelDetector)
    register_detector("linkedin_insight", LinkedInInsightDetector)
    register_detector("twitter_pixel", TwitterPixelDetector)
    register_detector("pinterest_tag", PinterestTagDetector)
    register_detector("snapchat_pixel", SnapchatPixelDetector)