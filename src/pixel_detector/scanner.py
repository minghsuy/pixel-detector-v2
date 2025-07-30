import asyncio
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Request, async_playwright
from playwright_stealth import stealth_async  # type: ignore

from .detectors import get_all_detectors, register_all_detectors
from .logging_config import get_logger
from .models import ScanMetadata, ScanResult
from .utils.health_check import WebsiteHealthChecker, batch_health_check
from .utils.retry import RetryConfig, exponential_backoff_retry
from .utils.url_normalizer import URLNormalizer


class PixelScanner:
    def __init__(
        self,
        headless: bool = True,
        stealth_mode: bool = True,
        screenshot: bool = False,
        timeout: int = 30000,
        user_agent: str | None = None,
        max_retries: int = 3,
        max_concurrent_scans: int = 5,
        pre_check_health: bool = True,
    ) -> None:
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.screenshot = screenshot
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
        self.logger = get_logger(__name__)
        self.retry_config = RetryConfig(max_retries=max_retries)
        self.max_concurrent_scans = max_concurrent_scans
        self.semaphore = asyncio.Semaphore(max_concurrent_scans)
        self.pre_check_health = pre_check_health
        self.health_checker = WebsiteHealthChecker() if pre_check_health else None
        self.url_normalizer = URLNormalizer(timeout=10)
        
        # Register all detectors
        register_all_detectors()

    async def scan_domain(self, domain: str) -> ScanResult:
        """Scan a domain for pixel tracking with retry logic"""
        try:
            # Normalize the URL first
            normalized_url, clean_domain = self.url_normalizer.normalize_url(domain)
            
            # Validate domain format
            if not self.url_normalizer.is_valid_domain(clean_domain):
                self.logger.error(f"Invalid domain format: {domain}")
                return ScanResult(
                    domain=domain,
                    url_scanned=domain,
                    error_message=f"Invalid domain format: {domain}",
                    success=False,
                    scan_metadata=ScanMetadata(
                        page_load_time=0,
                        total_requests=0,
                        tracking_requests=0,
                        scan_duration=0
                    ),
                )
            
            # Try to find accessible URL if enabled
            if self.pre_check_health:
                accessible_url = await self.url_normalizer.find_accessible_url(domain)
                if accessible_url:
                    normalized_url = accessible_url
                    self.logger.info(f"Using accessible URL: {accessible_url}")
                else:
                    # Try DNS lookup as fallback
                    try:
                        import socket
                        hostname = urlparse(normalized_url).hostname
                        if hostname:
                            socket.gethostbyname(hostname)
                            self.logger.debug(f"DNS lookup successful for {hostname}")
                    except (socket.gaierror, socket.herror) as e:
                        self.logger.warning(f"Domain not reachable and DNS lookup failed: {e}")
                        suggestions = self.url_normalizer.suggest_alternatives(domain)
                        error_msg = f"Domain not found: {str(e)}"
                        if suggestions:
                            error_msg += f"\nDid you mean one of these? {', '.join(suggestions[:3])}"
                        
                        return ScanResult(
                            domain=clean_domain,
                            url_scanned=normalized_url,
                            error_message=error_msg,
                            success=False,
                            scan_metadata=ScanMetadata(
                                page_load_time=0,
                                total_requests=0,
                                tracking_requests=0,
                                scan_duration=0
                            ),
                        )
                    except Exception as e:
                        self.logger.debug(f"DNS pre-check error for {domain}: {e}")
                        # Continue anyway if other errors occur
            
        except ValueError as e:
            # URL normalization failed
            self.logger.error(f"Failed to normalize URL {domain}: {e}")
            return ScanResult(
                domain=domain,
                url_scanned=domain,
                error_message=str(e),
                success=False,
                scan_metadata=ScanMetadata(
                    page_load_time=0,
                    total_requests=0,
                    tracking_requests=0,
                    scan_duration=0
                ),
            )
        
        # Define the actual scan function to be retried
        async def _do_scan() -> ScanResult:
            return await self._scan_domain_impl(normalized_url, clean_domain)
        
        # Determine if we should retry based on the error
        def should_retry(e: Exception) -> bool:
            error_msg = str(e).lower()
            # Retry on timeouts and network errors
            return (
                "timeout" in error_msg or
                "timed out" in error_msg or
                "network" in error_msg or
                "connection" in error_msg
            )
        
        try:
            # Use exponential backoff retry
            return await exponential_backoff_retry(
                _do_scan,  # type: ignore[arg-type]
                max_retries=self.retry_config.max_retries,
                initial_delay=self.retry_config.initial_delay,
                max_delay=self.retry_config.max_delay,
                exponential_base=self.retry_config.exponential_base,
                jitter=self.retry_config.jitter,
                retry_condition=should_retry,
            )
        except Exception as e:
            # If all retries failed, return error result
            self.logger.error(f"All retries failed for {domain}: {e}")
            return ScanResult(
                domain=clean_domain,
                url_scanned=normalized_url,
                pixels_detected=[],
                scan_metadata=ScanMetadata(
                    page_load_time=0,
                    total_requests=0,
                    tracking_requests=0,
                    scan_duration=time.time() - time.time(),
                    errors=[str(e)],
                ),
                success=False,
                error_message=str(e),
            )
    
    async def _scan_domain_impl(self, domain: str, clean_domain: str) -> ScanResult:
        """Internal implementation of domain scanning"""
        start_time = time.time()
        
        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p)
                context = await self._create_context(browser)
                
                # Get detectors
                detectors = get_all_detectors()
                
                # Set up request interception
                total_requests = 0
                tracking_requests = 0
                blocked_requests = 0
                
                async def handle_request(request: Request) -> None:
                    nonlocal total_requests, tracking_requests
                    total_requests += 1
                    
                    # Check each detector
                    for detector in detectors:
                        if await detector.check_request(request):
                            tracking_requests += 1
                            break
                
                # Create page and set up handlers
                page = await context.new_page()
                page.on("request", handle_request)
                
                # Apply stealth mode
                if self.stealth_mode:
                    await stealth_async(page)
                
                # Navigate to the page
                self.logger.info(f"Scanning {domain}...")
                load_start = time.time()
                
                try:
                    await page.goto(domain, wait_until="networkidle", timeout=self.timeout)
                except Exception as e:
                    self.logger.warning(f"Page load timeout or error: {e}")
                
                load_time = time.time() - load_start
                
                # Wait a bit for dynamic content
                await page.wait_for_timeout(2000)
                
                # Check cookies and DOM for each detector
                for detector in detectors:
                    await detector.check_cookies(page)
                    await detector.check_dom(page)
                
                # Take screenshot if requested
                screenshot_path = None
                if self.screenshot:
                    screenshot_path = f"screenshots/{clean_domain}_{int(time.time())}.png"
                    Path("screenshots").mkdir(exist_ok=True)
                    await page.screenshot(path=screenshot_path, full_page=True)
                
                # Build results
                pixels_detected = []
                for detector in detectors:
                    detection = detector.build_detection()
                    if detection:
                        pixels_detected.append(detection)
                        self.logger.info(
                            f"Found {detection.type.value} - "
                            f"Risk: {detection.risk_level.value}"
                        )
                
                scan_duration = time.time() - start_time
                
                metadata = ScanMetadata(
                    page_load_time=load_time,
                    total_requests=total_requests,
                    tracking_requests=tracking_requests,
                    blocked_requests=blocked_requests,
                    scan_duration=scan_duration,
                    browser_used="chromium",
                    stealth_mode=self.stealth_mode,
                )
                
                result = ScanResult(
                    domain=clean_domain,
                    url_scanned=domain,
                    pixels_detected=pixels_detected,
                    scan_metadata=metadata,
                    screenshot_path=screenshot_path,
                    success=True,
                )
                
                await browser.close()
                
                if not pixels_detected:
                    self.logger.info("No tracking pixels detected!")
                else:
                    self.logger.info(
                        f"Found {len(pixels_detected)} tracking pixel(s)"
                    )
                
                return result
                
        except Exception:
            # Re-raise the exception to trigger retry logic
            raise

    async def _launch_browser(self, playwright: Any) -> Browser:
        """Launch browser with appropriate settings"""
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
        ]
        
        if self.headless:
            launch_args.append("--single-process")
        
        browser: Browser = await playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )
        
        return browser

    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create browser context with privacy settings"""
        context = await browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,
            locale="en-US",
            timezone_id="America/New_York",
        )
        
        # Clear cookies and storage
        await context.clear_cookies()
        
        return context

    async def scan_multiple(self, domains: list[str]) -> list[ScanResult]:
        """Scan multiple domains concurrently with optional health checks"""
        # Perform health checks if enabled
        health_results = {}
        domains_to_scan = domains
        
        if self.pre_check_health:
            self.logger.info(f"Performing health checks on {len(domains)} domains...")
            health_results = await batch_health_check(domains, self.max_concurrent_scans)
            
            # Filter domains based on health check
            domains_to_scan = []
            skipped_domains = []
            
            for domain in domains:
                health = health_results.get(domain)
                if health and health.should_skip():
                    skipped_domains.append(domain)
                    self.logger.warning(f"Skipping {domain}: {health.error}")
                else:
                    domains_to_scan.append(domain)
            
            if skipped_domains:
                self.logger.info(f"Skipped {len(skipped_domains)} unreachable domains")
        
        async def scan_with_semaphore(domain: str) -> ScanResult:
            """Scan a domain with semaphore to limit concurrency"""
            async with self.semaphore:
                self.logger.debug(f"Starting scan for {domain}")
                
                # Adjust retry logic based on health check
                if domain in health_results:
                    health = health_results[domain]
                    if health.should_retry():
                        # Use more aggressive retry for protected sites
                        self.retry_config.max_retries = min(self.retry_config.max_retries + 2, 5)
                        self.logger.info(f"{domain} detected as protected, using enhanced retry logic")
                
                result = await self.scan_domain(domain)
                # Small delay to avoid overwhelming targets
                await asyncio.sleep(0.5)
                return result
        
        # Create results for skipped domains
        results = []
        if self.pre_check_health:
            for domain in domains:
                if domain in health_results and health_results[domain].should_skip():
                    # Create error result for skipped domain
                    results.append(ScanResult(
                        domain=domain,
                        url_scanned=f"https://{domain}",
                        pixels_detected=[],
                        scan_metadata=ScanMetadata(
                            page_load_time=0,
                            total_requests=0,
                            tracking_requests=0,
                            scan_duration=0,
                            errors=[f"Skipped: {health_results[domain].error}"],
                        ),
                        success=False,
                        error_message=f"Health check failed: {health_results[domain].error}",
                    ))
        
        # Create tasks for domains that passed health check
        if domains_to_scan:
            tasks = [scan_with_semaphore(domain) for domain in domains_to_scan]
            
            # Run all tasks concurrently and gather results
            self.logger.info(
                f"Starting concurrent scan of {len(domains_to_scan)} domains "
                f"(max {self.max_concurrent_scans} concurrent)"
            )
            
            scan_results = await asyncio.gather(*tasks, return_exceptions=False)
            results.extend(scan_results)
        
        return results