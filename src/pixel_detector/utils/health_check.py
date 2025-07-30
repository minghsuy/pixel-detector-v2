"""Website health check utilities for pre-flight validation."""

import asyncio
from typing import Optional
from urllib.parse import urlparse

import httpx
from dns import resolver

from ..logging_config import get_logger

logger = get_logger(__name__)


class HealthCheckResult:
    """Result of a website health check."""
    
    def __init__(
        self,
        url: str,
        is_alive: bool,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
        dns_resolves: bool = False,
        http_accessible: bool = False,
        has_bot_protection: bool = False,
        redirect_url: Optional[str] = None,
        response_time: float = 0.0,
    ):
        self.url = url
        self.is_alive = is_alive
        self.status_code = status_code
        self.error = error
        self.dns_resolves = dns_resolves
        self.http_accessible = http_accessible
        self.has_bot_protection = has_bot_protection
        self.redirect_url = redirect_url
        self.response_time = response_time
    
    def should_retry(self) -> bool:
        """Determine if this site should use retry logic."""
        # Retry if site is alive but has protection or slow response
        return self.is_alive and (self.has_bot_protection or self.response_time > 5.0)
    
    def should_skip(self) -> bool:
        """Determine if this site should be skipped entirely."""
        # Skip if DNS doesn't resolve or fundamental network issues
        return not self.dns_resolves or (not self.is_alive and not self.has_bot_protection)


class WebsiteHealthChecker:
    """Check website health before attempting full scan."""
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.logger = get_logger(__name__)
        
    async def check_dns(self, domain: str) -> tuple[bool, Optional[str]]:
        """Check if domain resolves via DNS."""
        try:
            # Run DNS resolution in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                resolver.resolve, 
                domain, 
                "A"
            )
            if result:
                self.logger.debug(f"DNS resolved {domain} to {result[0]}")
                return True, None
            return False, "No DNS records found"
        except resolver.NXDOMAIN:
            return False, "Domain does not exist (NXDOMAIN)"
        except resolver.NoAnswer:
            return False, "No DNS answer received"
        except Exception as e:
            return False, f"DNS error: {str(e)}"
    
    async def check_http(self, url: str) -> tuple[bool, Optional[int], Optional[str], float]:
        """Check if website responds to HTTP requests."""
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            verify=False  # Many healthcare sites have cert issues  # noqa: S501
        ) as client:
            try:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; HealthCheck/1.0)"
                    }
                )
                
                response_time = asyncio.get_event_loop().time() - start_time
                final_url = str(response.url) if response.url != url else None
                
                return True, response.status_code, final_url, response_time
                
            except httpx.TimeoutException:
                response_time = asyncio.get_event_loop().time() - start_time
                return False, None, None, response_time
            except httpx.ConnectError:
                return False, None, "Connection refused", 0.0
            except Exception as e:
                return False, None, str(e), 0.0
    
    def detect_bot_protection(self, status_code: Optional[int], error: Optional[str]) -> bool:
        """Detect common bot protection patterns."""
        if not status_code and not error:
            return False
            
        # Common bot protection status codes
        protection_codes = [403, 429, 503]
        if status_code in protection_codes:
            return True
            
        # Common bot protection error patterns
        if error:
            error_lower = error.lower()
            protection_patterns = [
                "cloudflare", "captcha", "challenge", "bot", 
                "automated", "rate limit", "too many requests",
                "access denied", "forbidden"
            ]
            return any(pattern in error_lower for pattern in protection_patterns)
            
        return False
    
    async def check_website(self, url: str) -> HealthCheckResult:
        """Perform comprehensive health check on a website."""
        # Ensure URL has protocol
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
            
        parsed = urlparse(url)
        domain = parsed.netloc
        
        self.logger.info(f"Health check for {domain}")
        
        # Step 1: DNS Check
        dns_ok, dns_error = await self.check_dns(domain)
        if not dns_ok:
            self.logger.warning(f"DNS failed for {domain}: {dns_error}")
            return HealthCheckResult(
                url=url,
                is_alive=False,
                error=dns_error,
                dns_resolves=False
            )
        
        # Step 2: HTTP Check
        http_ok, status_code, redirect_or_error, response_time = await self.check_http(url)
        
        # Detect bot protection
        has_bot_protection = self.detect_bot_protection(status_code, redirect_or_error)
        
        # Determine if site is alive
        is_alive = http_ok or has_bot_protection or (status_code is not None)
        
        # Parse redirect URL if it's a URL
        redirect_url = None
        error_msg = None
        if redirect_or_error and redirect_or_error.startswith("http"):
            redirect_url = redirect_or_error
        else:
            error_msg = redirect_or_error
        
        result = HealthCheckResult(
            url=url,
            is_alive=is_alive,
            status_code=status_code,
            error=error_msg,
            dns_resolves=True,
            http_accessible=http_ok,
            has_bot_protection=has_bot_protection,
            redirect_url=redirect_url,
            response_time=response_time
        )
        
        # Log summary
        if result.should_skip():
            self.logger.warning(f"{domain}: Should skip - {error_msg}")
        elif result.should_retry():
            self.logger.info(
                f"{domain}: Alive but needs retry logic "
                f"(protection: {has_bot_protection}, response time: {response_time:.1f}s)"
            )
        else:
            self.logger.info(f"{domain}: Healthy (status: {status_code}, time: {response_time:.1f}s)")
            
        return result


async def batch_health_check(
    urls: list[str], max_concurrent: int = 10
) -> dict[str, HealthCheckResult]:
    """Perform health checks on multiple URLs concurrently."""
    checker = WebsiteHealthChecker()
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_with_semaphore(url: str) -> tuple[str, HealthCheckResult]:
        async with semaphore:
            result = await checker.check_website(url)
            return url, result
    
    tasks = [check_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    return dict(results)
