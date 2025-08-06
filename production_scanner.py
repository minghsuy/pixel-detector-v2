#!/usr/bin/env python3
"""
Production Scanner for Pixel Detection
Combines all the best features from our development:
- Smart URL variations (tries www/non-www, http/https)
- Strict validation (rejects garbage immediately)
- CSV/TXT input support (portfolio and on-demand modes)
- Fast timeouts (30s default, 60s max)
- Checkpoint/resume capability
- Clean output for data integration
"""

import asyncio
import csv
import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from urllib.parse import urlparse
import tldextract
import idna

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Import models
try:
    from pixel_detector.models import ScanResult, ScanMetadata
    from pixel_detector.detectors import DETECTOR_REGISTRY
except ImportError:
    sys.path.insert(0, '/app/src')
    from pixel_detector.models import ScanResult, ScanMetadata
    from pixel_detector.detectors import DETECTOR_REGISTRY


class ProductionScanner:
    """
    Production-ready scanner with all enterprise features.
    """
    
    # Constants
    MAX_TIMEOUT_MS = 60000  # 60 seconds absolute max
    DEFAULT_TIMEOUT_MS = 30000  # 30 seconds default
    DEFAULT_CONCURRENT = 5  # Good for most systems
    
    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        mode: str = "auto",
        max_concurrent: int = DEFAULT_CONCURRENT,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        try_variations: bool = True
    ):
        """
        Initialize the production scanner.
        
        Args:
            input_file: CSV (portfolio) or TXT (on-demand) file
            output_dir: Directory for results
            mode: "portfolio", "ondemand", or "auto" (detect from extension)
            max_concurrent: Number of concurrent scans
            timeout_ms: Timeout per URL attempt in milliseconds
            try_variations: Whether to try www/non-www and http/https variations
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect mode
        if mode == "auto":
            self.mode = "portfolio" if input_file.suffix.lower() == ".csv" else "ondemand"
        else:
            self.mode = mode.lower()
        
        # Settings
        self.max_concurrent = max_concurrent
        self.timeout_ms = min(timeout_ms, self.MAX_TIMEOUT_MS)
        self.try_variations = try_variations
        
        # Initialize tldextract for domain validation
        self.extractor = tldextract.TLDExtract(include_psl_private_domains=False)
        
        # Output paths
        self.scan_results_dir = self.output_dir / "scan_results"
        self.scan_results_dir.mkdir(exist_ok=True)
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        
        # Portfolio mode specific
        if self.mode == "portfolio":
            self.final_output_csv = self.output_dir / "portfolio_results.csv"
            self.mapping_file = self.output_dir / "id_domain_mapping.json"
            self.original_data: List[Dict] = []
            self.id_to_domain: Dict[str, str] = {}
            self.domain_to_ids: Dict[str, List[str]] = {}
        else:
            self.final_output_csv = self.output_dir / "scan_results.csv"
        
        # Tracking
        self.domains_to_scan: List[str] = []
        self.completed_domains: Set[str] = set()
        self.stats = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "duplicates": 0,
            "completed": 0,
            "failed": 0,
            "with_pixels": 0,
            "clean": 0
        }
    
    def validate_domain(self, url: str) -> Tuple[bool, str, str]:
        """
        Validate and clean a domain.
        Returns: (is_valid, cleaned_domain, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "", "Empty input"
        
        url = url.strip()
        
        # Reject obvious garbage
        if url.lower() in ['none', 'null', 'undefined', 'n/a', 'na', '-', '', '0']:
            return False, "", f"Invalid: {url}"
        
        # Reject email
        if '@' in url:
            return False, "", "Email address"
        
        # Reject phone numbers
        if re.match(r'^[\d\s\-\(\)\+]+$', url):
            return False, "", "Phone number"
        
        # Clean up common issues
        url = re.sub(r'^https?://', '', url.lower())
        url = re.sub(r'^www\.', '', url)
        url = url.rstrip('/')
        
        # Extract domain parts
        try:
            extracted = self.extractor(f"https://{url}")
            if not extracted.suffix:
                return False, "", "No valid TLD"
            if not extracted.domain:
                return False, "", "No domain found"
            
            # Return registered domain (SLD + TLD)
            clean_domain = f"{extracted.domain}.{extracted.suffix}"
            return True, clean_domain, ""
            
        except Exception as e:
            return False, "", str(e)[:50]
    
    def load_checkpoint(self) -> None:
        """Load checkpoint if it exists."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file) as f:
                    data = json.load(f)
                    self.completed_domains = set(data.get("completed", []))
                    self.stats.update(data.get("stats", {}))
                    print(f"✅ Resumed from checkpoint: {len(self.completed_domains)} already completed")
            except:
                pass
    
    def save_checkpoint(self) -> None:
        """Save checkpoint for resume capability."""
        checkpoint = {
            "completed": list(self.completed_domains),
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint, f, indent=2)
    
    def preprocess_input(self) -> None:
        """
        Preprocess the input file (CSV or TXT).
        """
        print(f"\n📋 Processing {self.mode.upper()} input")
        print("=" * 60)
        
        if self.mode == "portfolio":
            self._preprocess_csv()
        else:
            self._preprocess_txt()
        
        print(f"\n📊 Input Statistics:")
        print(f"  Total entries: {self.stats['total']}")
        print(f"  Valid domains: {self.stats['valid']}")
        print(f"  Invalid entries: {self.stats['invalid']}")
        print(f"  Duplicates removed: {self.stats['duplicates']}")
        print(f"  Unique domains to scan: {len(self.domains_to_scan)}")
    
    def _preprocess_csv(self) -> None:
        """Preprocess CSV for portfolio mode."""
        with open(self.input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            if 'custom_id' not in reader.fieldnames or 'url' not in reader.fieldnames:
                raise ValueError("CSV must have 'custom_id' and 'url' columns")
            
            seen_domains = set()
            
            for row in reader:
                self.stats["total"] += 1
                self.original_data.append(row)
                
                custom_id = str(row['custom_id']).strip()
                url = str(row['url']).strip()
                
                # Validate
                is_valid, clean_domain, error = self.validate_domain(url)
                
                if is_valid:
                    self.stats["valid"] += 1
                    self.id_to_domain[custom_id] = clean_domain
                    
                    # Handle duplicates
                    if clean_domain not in seen_domains:
                        self.domains_to_scan.append(clean_domain)
                        seen_domains.add(clean_domain)
                        self.domain_to_ids[clean_domain] = []
                    else:
                        self.stats["duplicates"] += 1
                    
                    self.domain_to_ids[clean_domain].append(custom_id)
                else:
                    self.stats["invalid"] += 1
                    self.id_to_domain[custom_id] = f"INVALID:{error}"
        
        # Save mapping
        with open(self.mapping_file, 'w') as f:
            json.dump({
                "id_to_domain": self.id_to_domain,
                "domain_to_ids": self.domain_to_ids
            }, f, indent=2)
    
    def _preprocess_txt(self) -> None:
        """Preprocess TXT for on-demand mode."""
        seen_domains = set()
        
        with open(self.input_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                self.stats["total"] += 1
                
                # Validate
                is_valid, clean_domain, error = self.validate_domain(line)
                
                if is_valid:
                    if clean_domain not in seen_domains:
                        self.stats["valid"] += 1
                        self.domains_to_scan.append(clean_domain)
                        seen_domains.add(clean_domain)
                    else:
                        self.stats["duplicates"] += 1
                else:
                    self.stats["invalid"] += 1
    
    def generate_url_variations(self, domain: str) -> List[str]:
        """
        Generate URL variations to try.
        Returns URLs in order of likelihood.
        """
        if not self.try_variations:
            return [f"https://{domain}"]
        
        # For most domains, try without www first (it's more common)
        return [
            f"https://{domain}",        # Most common
            f"https://www.{domain}",    # With www
            f"http://{domain}",         # HTTP fallback
            f"http://www.{domain}",     # HTTP with www
        ]
    
    async def scan_domain(self, domain: str, browser) -> ScanResult:
        """
        Scan a single domain with smart URL variations.
        """
        start_time = time.time()
        urls_to_try = self.generate_url_variations(domain)
        
        print(f"🔍 Scanning {domain}...")
        
        last_error = None
        successful_url = None
        
        for i, url in enumerate(urls_to_try):
            try:
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,
                )
                page = await context.new_page()
                
                # Track requests
                network_requests = []
                page.on("request", lambda req: network_requests.append(req.url))
                
                # Navigate with timeout
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms
                )
                
                if response and response.status < 500:
                    successful_url = page.url
                    
                    # Detect pixels
                    pixels_detected = []
                    tracking_requests = 0
                    
                    for detector_class in DETECTOR_REGISTRY.values():
                        detector = detector_class()
                        
                        for req_url in network_requests:
                            if detector.check_network_request(req_url):
                                detector.network_requests.append(req_url)
                                tracking_requests += 1
                        
                        try:
                            content = await asyncio.wait_for(page.content(), timeout=5.0)
                            detector.check_dom_elements(content)
                        except:
                            pass
                        
                        evidence = detector.build_evidence()
                        if evidence.has_pixel:
                            pixels_detected.append({
                                "type": detector.pixel_type.value,
                                "evidence": evidence.model_dump()
                            })
                    
                    await context.close()
                    
                    return ScanResult(
                        domain=domain,
                        url_scanned=successful_url,
                        timestamp=datetime.now(),
                        pixels_detected=pixels_detected,
                        scan_metadata=ScanMetadata(
                            page_load_time=time.time() - start_time,
                            total_requests=len(network_requests),
                            tracking_requests=tracking_requests,
                            scan_duration=time.time() - start_time,
                            browser_used="chromium",
                            stealth_mode=False
                        ),
                        success=True,
                        error_message=None
                    )
                
                await context.close()
                
            except (PlaywrightTimeoutError, asyncio.TimeoutError):
                last_error = f"Timeout ({self.timeout_ms}ms)"
            except Exception as e:
                last_error = str(e)[:100]
        
        # All variations failed
        return ScanResult(
            domain=domain,
            url_scanned=urls_to_try[0],
            timestamp=datetime.now(),
            pixels_detected=[],
            scan_metadata=ScanMetadata(
                page_load_time=0,
                total_requests=0,
                tracking_requests=0,
                scan_duration=time.time() - start_time,
                browser_used="chromium",
                stealth_mode=False,
                errors=[f"All variations failed: {last_error}"]
            ),
            success=False,
            error_message=last_error
        )
    
    async def run_scanner(self) -> None:
        """
        Run the scanner on all domains.
        """
        # Load checkpoint
        self.load_checkpoint()
        
        # Filter already completed
        remaining = [d for d in self.domains_to_scan if d not in self.completed_domains]
        
        if not remaining:
            print("\n✨ All domains already scanned!")
            return
        
        print(f"\n🚀 Starting scan")
        print(f"  Domains to scan: {len(remaining)}")
        print(f"  Concurrent: {self.max_concurrent}")
        print(f"  Timeout: {self.timeout_ms}ms")
        print(f"  URL variations: {'Enabled' if self.try_variations else 'Disabled'}")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_domain(domain):
                async with semaphore:
                    if domain in self.completed_domains:
                        return
                    
                    result = await self.scan_domain(domain, browser)
                    
                    # Save result
                    safe_name = domain.replace('.', '_').replace('/', '_')
                    output_file = self.scan_results_dir / f"{safe_name}.json"
                    with open(output_file, 'w') as f:
                        json.dump(result.model_dump(), f, indent=2, default=str)
                    
                    # Update stats
                    self.completed_domains.add(domain)
                    self.stats["completed"] += 1
                    
                    if result.success:
                        if result.pixels_detected:
                            self.stats["with_pixels"] += 1
                            print(f"🎯 {domain}: {len(result.pixels_detected)} pixels")
                        else:
                            self.stats["clean"] += 1
                            print(f"✓ {domain}: Clean")
                    else:
                        self.stats["failed"] += 1
                        print(f"✗ {domain}: Failed")
                    
                    # Progress
                    pct = len(self.completed_domains) * 100 / len(self.domains_to_scan)
                    print(f"📊 Progress: {len(self.completed_domains)}/{len(self.domains_to_scan)} ({pct:.1f}%)")
                    
                    # Save checkpoint every 10 domains
                    if len(self.completed_domains) % 10 == 0:
                        self.save_checkpoint()
            
            # Process all domains
            tasks = [process_domain(domain) for domain in remaining]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            await browser.close()
        
        # Final checkpoint
        self.save_checkpoint()
    
    def generate_output(self) -> None:
        """
        Generate the final output CSV.
        """
        print(f"\n📊 Generating {self.mode.upper()} output")
        print("=" * 60)
        
        # Load scan results
        scan_results = {}
        for json_file in self.scan_results_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    domain = data.get("domain", "").lower()
                    if domain:
                        scan_results[domain] = data
            except:
                pass
        
        if self.mode == "portfolio":
            self._generate_portfolio_output(scan_results)
        else:
            self._generate_ondemand_output(scan_results)
        
        print(f"✅ Results saved to: {self.final_output_csv}")
    
    def _generate_portfolio_output(self, scan_results: Dict) -> None:
        """Generate portfolio output with join-back."""
        with open(self.final_output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'custom_id', 'url', 'domain', 'scan_status',
                'has_pixel', 'pixel_count', 'pixel_names',
                'error', 'scan_duration', 'timestamp'
            ])
            
            for row in self.original_data:
                custom_id = str(row['custom_id']).strip()
                original_url = str(row['url']).strip()
                
                domain_info = self.id_to_domain.get(custom_id, "")
                
                if domain_info.startswith("INVALID:"):
                    # Invalid domain
                    error = domain_info.replace("INVALID:", "")
                    writer.writerow([
                        custom_id, original_url, '', 'rejected',
                        0, 0, '', error, 0, ''
                    ])
                else:
                    # Valid domain - get scan result
                    result = scan_results.get(domain_info)
                    if result:
                        self._write_result_row(writer, custom_id, original_url, domain_info, result)
                    else:
                        writer.writerow([
                            custom_id, original_url, domain_info, 'not_scanned',
                            0, 0, '', 'Not found in results', 0, ''
                        ])
    
    def _generate_ondemand_output(self, scan_results: Dict) -> None:
        """Generate simple on-demand output."""
        with open(self.final_output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'domain', 'scan_status', 'has_pixel', 'pixel_count',
                'pixel_names', 'error', 'scan_duration'
            ])
            
            for domain in self.domains_to_scan:
                result = scan_results.get(domain)
                if result:
                    pixels = result.get('pixels_detected', [])
                    writer.writerow([
                        domain,
                        'success' if result.get('success') else 'failed',
                        1 if pixels else 0,
                        len(pixels),
                        ', '.join([p.get('type', '') for p in pixels]),
                        result.get('error_message', ''),
                        f"{result.get('scan_metadata', {}).get('scan_duration', 0):.2f}"
                    ])
                else:
                    writer.writerow([
                        domain, 'not_scanned', 0, 0, '',
                        'Not found in results', 0
                    ])
    
    def _write_result_row(self, writer, custom_id, original_url, domain, result):
        """Helper to write a result row."""
        pixels = result.get('pixels_detected', [])
        metadata = result.get('scan_metadata', {})
        
        writer.writerow([
            custom_id,
            original_url,
            domain,
            'success' if result.get('success') else 'failed',
            1 if pixels else 0,
            len(pixels),
            ', '.join([p.get('type', '') for p in pixels]),
            result.get('error_message', ''),
            f"{metadata.get('scan_duration', 0):.2f}",
            result.get('timestamp', '')
        ])


async def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Production Scanner for Pixel Detection")
        print("\nUsage: python production_scanner.py <input_file> <output_dir> [options]")
        print("\nInput formats:")
        print("  CSV: Portfolio mode (requires custom_id, url columns)")
        print("  TXT: On-demand mode (one domain per line)")
        print("\nOptions:")
        print("  --mode MODE         Force mode: portfolio or ondemand (default: auto)")
        print("  --concurrent N      Max concurrent scans (default: 5)")
        print("  --timeout N         Timeout in ms (default: 30000, max: 60000)")
        print("  --no-variations     Disable URL variations (only try https://domain)")
        print("\nExamples:")
        print("  python production_scanner.py portfolio.csv results/")
        print("  python production_scanner.py domains.txt quick_scan/ --concurrent 10")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    # Parse options
    mode = "auto"
    concurrent = 5
    timeout = 30000
    try_variations = True
    
    for i in range(3, len(sys.argv), 2):
        if sys.argv[i] == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1]
        elif sys.argv[i] == "--concurrent" and i + 1 < len(sys.argv):
            concurrent = int(sys.argv[i + 1])
        elif sys.argv[i] == "--timeout" and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])
        elif sys.argv[i] == "--no-variations":
            try_variations = False
            i -= 1  # This flag has no value
    
    # Initialize scanner
    scanner = ProductionScanner(
        input_file=input_file,
        output_dir=output_dir,
        mode=mode,
        max_concurrent=concurrent,
        timeout_ms=timeout,
        try_variations=try_variations
    )
    
    # Run pipeline
    scanner.preprocess_input()
    await scanner.run_scanner()
    scanner.generate_output()
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ SCAN COMPLETE")
    print(f"  Total processed: {scanner.stats['completed']}")
    print(f"  Clean sites: {scanner.stats['clean']}")
    print(f"  Sites with pixels: {scanner.stats['with_pixels']}")
    print(f"  Failed: {scanner.stats['failed']}")
    print(f"  Output: {scanner.final_output_csv}")


if __name__ == "__main__":
    asyncio.run(main())