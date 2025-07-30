#!/usr/bin/env python3
"""
Example usage of the Pixel Detector
"""

import asyncio
import json
from pixel_detector import PixelScanner


async def main():
    # Create scanner instance
    scanner = PixelScanner(
        headless=True,      # Run in headless mode
        stealth_mode=True,  # Use anti-detection measures
        screenshot=False,   # Don't take screenshots
        timeout=30000,      # 30 second timeout
    )
    
    # Example healthcare domain (replace with actual domain)
    domain = "sutterhealth.org"
    
    print(f"Scanning {domain} for tracking pixels...")
    
    # Perform scan
    result = await scanner.scan_domain(domain)
    
    # Print summary
    print(f"\nScan completed in {result.scan_metadata.scan_duration:.2f} seconds")
    print(f"Total requests: {result.scan_metadata.total_requests}")
    print(f"Tracking requests: {result.scan_metadata.tracking_requests}")
    
    if result.pixels_detected:
        print(f"\nFound {len(result.pixels_detected)} tracking pixel(s):")
        for pixel in result.pixels_detected:
            print(f"\n- {pixel.type.value.upper()}")
            print(f"  Risk Level: {pixel.risk_level.value}")
            print(f"  HIPAA Concern: {'Yes' if pixel.hipaa_concern else 'No'}")
            if pixel.pixel_id:
                print(f"  Pixel ID: {pixel.pixel_id}")
            print(f"  Evidence:")
            if pixel.evidence.network_requests:
                print(f"    - {len(pixel.evidence.network_requests)} network requests")
            if pixel.evidence.script_tags:
                print(f"    - {len(pixel.evidence.script_tags)} script tags")
            if pixel.evidence.cookies_set:
                print(f"    - Cookies: {', '.join(pixel.evidence.cookies_set)}")
    else:
        print("\nNo tracking pixels detected!")
    
    # Save full results to JSON
    with open("scan_results.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
    print("\nFull results saved to scan_results.json")


if __name__ == "__main__":
    asyncio.run(main())