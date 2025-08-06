#!/usr/bin/env python3
"""
Production-grade batch scanner with enterprise reliability features.
Addresses real-world issues encountered in corporate deployments:
- Memory-efficient streaming saves
- Proper redirect handling
- DNS retry logic with user-agent rotation
- Working checkpoint/resume system
- Real-time progress monitoring
"""

import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Optional, Set
from datetime import datetime
from urllib.parse import urlparse, urlunparse
import aiofiles

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from pixel_detector.models import ScanResult
from pixel_detector.detectors import DETECTOR_REGISTRY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProductionBatchScanner:
    """Production-ready batch scanner with enterprise features."""
    
    def __init__(
        self,
        output_dir: Path,
        checkpoint_file: Optional[Path] = None,
        max_concurrent: int = 3,
        timeout_ms: int = 45000,
        max_retries: int = 2,
        save_every: int = 1,  # Save immediately after each scan
        dns_retry_delay: int = 5,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Checkpoint management
        self.checkpoint_file = checkpoint_file or self.output_dir / "checkpoint.json"
        self.completed_domains: Set[str] = set()
        self.failed_domains: dict[str, int] = {}  # domain -> retry count
        
        # Scan settings
        self.max_concurrent = max_concurrent
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        self.save_every = save_every
        self.dns_retry_delay = dns_retry_delay
        
        # Statistics
        self.stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "pixels_found": 0,
            "clean": 0,
            "start_time": None,
            "domains_with_pixels": []
        }
        
        # User agents for rotation (to avoid bot detection)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Progress file for real-time monitoring
        self.progress_file = self.output_dir / "progress.json"
        
    def normalize_domain(self, domain: str) -> list[str]:
        """
        Generate domain variations to try.
        Handles www prefix, protocol, and common variations.
        """
        domain = domain.strip().lower()
        
        # Remove any protocol if present
        if "://" in domain:
            domain = domain.split("://", 1)[1]
        
        # Remove trailing slash
        domain = domain.rstrip("/")
        
        # Generate variations to try
        variations = []
        
        # If it starts with www, also try without
        if domain.startswith("www."):
            base = domain[4:]
            variations = [
                f"https://{domain}",
                f"https://{base}",
                f"http://{domain}",
                f"http://{base}"
            ]
        # If it doesn't start with www, also try with
        else:
            variations = [
                f"https://{domain}",
                f"https://www.{domain}",
                f"http://{domain}",
                f"http://www.{domain}"
            ]
        
        return variations
    
    async def load_checkpoint(self) -> None:
        """Load checkpoint data if it exists."""
        if self.checkpoint_file.exists():
            try:
                async with aiofiles.open(self.checkpoint_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.completed_domains = set(data.get("completed", []))
                    self.failed_domains = data.get("failed", {})
                    self.stats.update(data.get("stats", {}))
                    logger.info(f"✅ Loaded checkpoint: {len(self.completed_domains)} completed, {len(self.failed_domains)} failed")
            except Exception as e:
                logger.warning(f"⚠️ Could not load checkpoint: {e}")
    
    async def save_checkpoint(self) -> None:
        """Save checkpoint data for resume capability."""
        checkpoint_data = {
            "completed": list(self.completed_domains),
            "failed": self.failed_domains,
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with aiofiles.open(self.checkpoint_file, 'w') as f:
                await f.write(json.dumps(checkpoint_data, indent=2, default=str))
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")
    
    async def update_progress(self) -> None:
        """Update real-time progress file for monitoring."""
        progress_data = {
            "current_stats": self.stats,
            "completed_domains": len(self.completed_domains),
            "failed_domains": len(self.failed_domains),
            "elapsed_time": str(datetime.now() - datetime.fromisoformat(self.stats["start_time"])) if self.stats["start_time"] else "0:00:00",
            "rate": f"{self.stats['completed'] / max(1, (time.time() - self.stats.get('start_timestamp', time.time())) / 3600):.1f} domains/hour",
            "eta": self.calculate_eta(),
            "last_update": datetime.now().isoformat()
        }
        
        try:
            async with aiofiles.open(self.progress_file, 'w') as f:
                await f.write(json.dumps(progress_data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
    
    def calculate_eta(self) -> str:
        """Calculate estimated time to completion."""
        if not self.stats.get("start_timestamp") or self.stats["completed"] == 0:
            return "Unknown"
        
        elapsed = time.time() - self.stats["start_timestamp"]
        rate = self.stats["completed"] / elapsed
        remaining = self.stats["total"] - self.stats["completed"]
        
        if rate > 0:
            eta_seconds = remaining / rate
            hours = int(eta_seconds // 3600)
            minutes = int((eta_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "Unknown"
    
    async def scan_with_redirect(self, domain: str, browser) -> Optional[ScanResult]:
        """
        Scan a domain with proper redirect handling.
        Tries multiple URL variations to handle www/non-www issues.
        """
        variations = self.normalize_domain(domain)
        last_error = None
        
        for url_variant in variations:
            try:
                logger.debug(f"🔍 Trying: {url_variant}")
                
                # Create context with random user agent
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,
                    java_script_enabled=True
                )
                
                page = await context.new_page()
                
                # Set up request interception
                network_requests = []
                async def handle_request(request):
                    network_requests.append(request.url)
                
                page.on("request", handle_request)
                
                # Navigate with redirect following
                response = await page.goto(
                    url_variant,
                    wait_until="networkidle",
                    timeout=self.timeout_ms
                )
                
                if response and response.ok:
                    # Success! Scan for pixels
                    final_url = page.url
                    logger.info(f"✓ Successfully loaded: {domain} → {final_url}")
                    
                    # Run all detectors
                    pixels_detected = []
                    for detector_class in DETECTOR_REGISTRY.values():
                        detector = detector_class()
                        
                        # Check network requests
                        for req_url in network_requests:
                            if detector.check_network_request(req_url):
                                detector.network_requests.append(req_url)
                        
                        # Check page content
                        try:
                            content = await page.content()
                            detector.check_dom_elements(content)
                            
                            # Check JavaScript variables
                            for var in detector.js_variables:
                                try:
                                    exists = await page.evaluate(f"typeof {var} !== 'undefined'")
                                    if exists:
                                        detector.js_detections.append(var)
                                except:
                                    pass
                        except:
                            pass
                        
                        # Build evidence
                        evidence = detector.build_evidence()
                        if evidence.has_pixel:
                            pixels_detected.append({
                                "type": detector.pixel_type.value,
                                "evidence": evidence.model_dump()
                            })
                    
                    await context.close()
                    
                    return ScanResult(
                        domain=domain,
                        url_scanned=final_url,
                        timestamp=datetime.now(),
                        pixels_detected=pixels_detected,
                        success=True,
                        error_message=None,
                        scan_duration_ms=int((time.time() * 1000) - (self.stats.get("scan_start", time.time() * 1000)))
                    )
                
                await context.close()
                
            except PlaywrightTimeoutError:
                last_error = f"Timeout on {url_variant}"
                logger.debug(f"⏱️ Timeout: {url_variant}")
            except Exception as e:
                last_error = str(e)
                logger.debug(f"❌ Error on {url_variant}: {e}")
        
        # All variations failed
        return ScanResult(
            domain=domain,
            url_scanned=variations[0],
            timestamp=datetime.now(),
            pixels_detected=[],
            success=False,
            error_message=last_error or "All URL variations failed"
        )
    
    async def save_result(self, result: ScanResult) -> None:
        """Save a single result to disk immediately."""
        output_file = self.output_dir / f"{result.domain.replace('.', '_').replace('/', '_')}.json"
        
        try:
            async with aiofiles.open(output_file, 'w') as f:
                await f.write(json.dumps(result.model_dump(), indent=2, default=str))
            
            # Update stats
            if result.success:
                if result.pixels_detected:
                    self.stats["pixels_found"] += 1
                    self.stats["domains_with_pixels"].append({
                        "domain": result.domain,
                        "pixels": [p["type"] for p in result.pixels_detected]
                    })
                    logger.info(f"🎯 {result.domain}: {len(result.pixels_detected)} pixels detected")
                else:
                    self.stats["clean"] += 1
                    logger.info(f"✅ {result.domain}: Clean (no pixels)")
            else:
                logger.warning(f"⚠️ {result.domain}: Scan failed - {result.error_message}")
                
        except Exception as e:
            logger.error(f"❌ Failed to save result for {result.domain}: {e}")
    
    async def process_domain(self, domain: str, browser, semaphore) -> None:
        """Process a single domain with retry logic."""
        async with semaphore:
            # Skip if already completed
            if domain in self.completed_domains:
                logger.debug(f"⏭️ Skipping completed: {domain}")
                return
            
            # Check retry count
            retry_count = self.failed_domains.get(domain, 0)
            if retry_count >= self.max_retries:
                logger.warning(f"⏭️ Skipping max-failed domain: {domain}")
                return
            
            self.stats["scan_start"] = time.time() * 1000
            
            # Scan with redirect handling
            result = await self.scan_with_redirect(domain, browser)
            
            # Save result immediately (streaming save)
            await self.save_result(result)
            
            # Update tracking
            if result.success:
                self.completed_domains.add(domain)
                self.stats["completed"] += 1
                if domain in self.failed_domains:
                    del self.failed_domains[domain]
            else:
                self.failed_domains[domain] = retry_count + 1
                self.stats["failed"] += 1
                
                # DNS retry with delay
                if "DNS" in result.error_message or "ERR_NAME" in result.error_message:
                    logger.info(f"🔄 DNS issue for {domain}, waiting {self.dns_retry_delay}s before retry...")
                    await asyncio.sleep(self.dns_retry_delay)
            
            # Save checkpoint and progress every domain
            await self.save_checkpoint()
            await self.update_progress()
            
            # Log progress
            progress_pct = (self.stats["completed"] / self.stats["total"]) * 100
            logger.info(f"📊 Progress: {self.stats['completed']}/{self.stats['total']} ({progress_pct:.1f}%) | Clean: {self.stats['clean']} | Pixels: {self.stats['pixels_found']} | Failed: {self.stats['failed']}")
    
    async def run(self, domains_file: Path) -> None:
        """Run the batch scan with all production features."""
        # Load domains
        with open(domains_file) as f:
            all_domains = [line.strip() for line in f if line.strip()]
        
        # Load checkpoint
        await self.load_checkpoint()
        
        # Filter out already completed domains
        domains_to_scan = [d for d in all_domains if d not in self.completed_domains]
        
        # Initialize stats
        self.stats["total"] = len(all_domains)
        self.stats["start_time"] = datetime.now().isoformat()
        self.stats["start_timestamp"] = time.time()
        
        logger.info(f"🚀 Starting batch scan")
        logger.info(f"📋 Total domains: {len(all_domains)}")
        logger.info(f"✅ Already completed: {len(self.completed_domains)}")
        logger.info(f"📝 To scan: {len(domains_to_scan)}")
        logger.info(f"⚙️ Settings: {self.max_concurrent} concurrent, {self.timeout_ms}ms timeout, {self.max_retries} retries")
        
        if not domains_to_scan:
            logger.info("✨ All domains already completed!")
            return
        
        # Create playwright instance
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-dev-tools",
                ]
            )
            
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Process all domains
            tasks = [
                self.process_domain(domain, browser, semaphore)
                for domain in domains_to_scan
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            await browser.close()
        
        # Final statistics
        logger.info("=" * 60)
        logger.info("🎉 BATCH SCAN COMPLETE!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"  Total: {self.stats['total']}")
        logger.info(f"  Completed: {self.stats['completed']}")
        logger.info(f"  Failed: {self.stats['failed']}")
        logger.info(f"  Clean sites: {self.stats['clean']}")
        logger.info(f"  Sites with pixels: {self.stats['pixels_found']}")
        
        if self.stats["domains_with_pixels"]:
            logger.info(f"\n🎯 Domains with tracking pixels:")
            for item in self.stats["domains_with_pixels"]:
                logger.info(f"  - {item['domain']}: {', '.join(item['pixels'])}")
        
        # Save final summary
        summary_file = self.output_dir / "scan_summary.json"
        async with aiofiles.open(summary_file, 'w') as f:
            await f.write(json.dumps(self.stats, indent=2, default=str))
        
        logger.info(f"\n📁 Results saved to: {self.output_dir}")
        logger.info(f"📊 Summary saved to: {summary_file}")


async def main():
    """Main entry point for production batch scanner."""
    if len(sys.argv) < 3:
        print("Usage: python production_batch_scanner.py <domains_file> <output_dir> [options]")
        print("\nOptions:")
        print("  --concurrent N    Max concurrent scans (default: 3)")
        print("  --timeout N       Timeout in ms (default: 45000)")
        print("  --retries N       Max retries per domain (default: 2)")
        print("\nExample:")
        print("  python production_batch_scanner.py domains.txt results/ --concurrent 5")
        sys.exit(1)
    
    domains_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    # Parse optional arguments
    max_concurrent = 3
    timeout = 45000
    retries = 2
    
    for i in range(3, len(sys.argv), 2):
        if sys.argv[i] == "--concurrent" and i + 1 < len(sys.argv):
            max_concurrent = int(sys.argv[i + 1])
        elif sys.argv[i] == "--timeout" and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])
        elif sys.argv[i] == "--retries" and i + 1 < len(sys.argv):
            retries = int(sys.argv[i + 1])
    
    # Create scanner
    scanner = ProductionBatchScanner(
        output_dir=output_dir,
        max_concurrent=max_concurrent,
        timeout_ms=timeout,
        max_retries=retries
    )
    
    # Run the scan
    await scanner.run(domains_file)


if __name__ == "__main__":
    asyncio.run(main())