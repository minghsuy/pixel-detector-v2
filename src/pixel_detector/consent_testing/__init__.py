"""Consent management testing module.

This module provides banner interaction testing to detect malfunctioning
consent mechanisms (comparable to BitSight's consent management feature).
"""

from .banner_interaction import BannerInteractionTester
from .button_selectors import PLATFORM_SELECTORS, BannerSelector, ButtonConfig
from .compliance_checker import ComplianceChecker

__all__ = [
    "BannerInteractionTester",
    "BannerSelector",
    "ButtonConfig",
    "ComplianceChecker",
    "PLATFORM_SELECTORS",
]
