#!/usr/bin/env python3
"""
Example: Analyze consent management platform usage across a portfolio.

This demonstrates how to:
1. Detect which consent platforms are in use
2. Identify sites with tracking but no consent management
3. Generate compliance risk scores based on consent implementation

Usage:
    uv run python examples/consent_gap_analysis.py portfolio.txt
    uv run python examples/consent_gap_analysis.py santa_clara_healthcare.txt

Output:
    - Console summary with risk breakdown
    - CSV report: {input_file}_consent_report.csv
"""

import asyncio
import csv
import sys
from pathlib import Path

from pixel_detector.scanner import PixelScanner
from pixel_detector.models.pixel_detection import PixelType


# Consent platform types
CONSENT_PLATFORMS = {
    PixelType.ONETRUST,
    PixelType.COOKIEBOT,
    PixelType.OSANO,
    PixelType.TRUSTARC,
    PixelType.USERCENTRICS,
    PixelType.TERMLY,
}

# Tracking pixel types that require consent
TRACKING_PIXELS = {
    PixelType.META_PIXEL,
    PixelType.GOOGLE_ANALYTICS,
    PixelType.GOOGLE_ADS,
    PixelType.TIKTOK_PIXEL,
    PixelType.LINKEDIN_INSIGHT,
    PixelType.TWITTER_PIXEL,
    PixelType.PINTEREST_TAG,
    PixelType.SNAPCHAT_PIXEL,
}


def analyze_consent_compliance(scan_result):
    """Analyze consent management compliance for a scan result"""

    # Extract detected platform types
    detected_types = {p.type for p in scan_result.pixels_detected}

    # Check for consent platforms
    consent_platforms = detected_types & CONSENT_PLATFORMS
    tracking_pixels = detected_types & TRACKING_PIXELS

    # Risk assessment
    has_consent = bool(consent_platforms)
    has_tracking = bool(tracking_pixels)

    if has_tracking and not has_consent:
        risk = "CRITICAL"
        message = f"Tracking without consent management: {len(tracking_pixels)} trackers"
    elif has_tracking and has_consent:
        risk = "REVIEW"
        message = f"Consent platform detected: {', '.join(p.value for p in consent_platforms)}"
    elif has_consent:
        risk = "LOW"
        message = f"Consent platform present: {', '.join(p.value for p in consent_platforms)}"
    else:
        risk = "LOW"
        message = "No tracking or consent detected"

    return {
        "domain": scan_result.domain,
        "risk_level": risk,
        "has_consent_platform": has_consent,
        "consent_platforms": [p.value for p in consent_platforms],
        "tracking_pixels": [p.value for p in tracking_pixels],
        "tracking_count": len(tracking_pixels),
        "message": message,
    }


async def main(domains_file: str):
    """Analyze consent compliance for a portfolio of domains"""

    # Read domains
    domains_path = Path(domains_file)
    if not domains_path.exists():
        print(f"Error: File not found: {domains_file}")
        sys.exit(1)

    with open(domains_path) as f:
        domains = [line.strip() for line in f if line.strip()]

    print(f"Analyzing {len(domains)} domains for consent compliance...")
    print("=" * 80)

    # Scan all domains
    scanner = PixelScanner(headless=True, timeout=30000)
    results = await scanner.scan_multiple(domains)

    # Analyze each result
    analyses = []
    for result in results:
        if result.success:
            analysis = analyze_consent_compliance(result)
            analyses.append(analysis)
            print(f"✓ {result.domain}: {analysis['risk_level']} - {analysis['message']}")
        else:
            print(f"✗ {result.domain}: Scan failed - {result.error_message}")

    # Generate summary
    print("\n" + "=" * 80)
    print("CONSENT COMPLIANCE SUMMARY")
    print("=" * 80)

    critical = [a for a in analyses if a["risk_level"] == "CRITICAL"]
    review = [a for a in analyses if a["risk_level"] == "REVIEW"]
    low = [a for a in analyses if a["risk_level"] == "LOW"]

    print(f"\nTotal domains scanned: {len(analyses)}")
    print(f"CRITICAL (tracking without consent): {len(critical)}")
    print(f"REVIEW (has consent, verify config): {len(review)}")
    print(f"LOW (no tracking or compliant): {len(low)}")

    # Platform usage statistics
    platform_counts = {}
    for analysis in analyses:
        for platform in analysis["consent_platforms"]:
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

    if platform_counts:
        print("\nConsent Platform Usage:")
        for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(analyses)) * 100
            print(f"  {platform}: {count} ({pct:.1f}%)")

    # High-risk sites detail
    if critical:
        print(f"\n⚠️  CRITICAL RISK SITES ({len(critical)}):")
        for analysis in critical[:10]:  # Show top 10
            print(f"  - {analysis['domain']}: {analysis['tracking_count']} trackers, no consent")

    # Save detailed report
    output_file = domains_path.stem + "_consent_report.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "domain",
                "risk_level",
                "has_consent_platform",
                "consent_platforms",
                "tracking_count",
                "tracking_pixels",
                "message",
            ],
        )
        writer.writeheader()
        for analysis in analyses:
            # Convert lists to strings for CSV
            row = analysis.copy()
            row["consent_platforms"] = "|".join(row["consent_platforms"])
            row["tracking_pixels"] = "|".join(row["tracking_pixels"])
            writer.writerow(row)

    print(f"\n✅ Detailed report saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python consent_gap_analysis.py <domains_file>")
        print("\nExample:")
        print("  python consent_gap_analysis.py santa_clara_healthcare.txt")
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
