"""URL normalization and validation utilities for handling various domain formats."""

import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx
import tldextract

from ..logging_config import get_logger

logger = get_logger(__name__)


class URLNormalizer:
    """Handles URL normalization and validation for various domain formats."""
    
    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self.common_redirects = {
            # Common redirect patterns
            "www": True,
            "non-www": True,
            "https": True,
            "trailing-slash": True,
        }
    
    def normalize_url(self, url_input: str) -> tuple[str, str]:
        """
        Normalize various URL formats into a proper URL.
        
        Returns:
            Tuple[normalized_url, clean_domain]
        
        Examples:
            - "example.com" -> "https://example.com", "example.com"
            - "http://example.com/path" -> "http://example.com/path", "example.com"
            - "sub.example.com:8080" -> "https://sub.example.com:8080", "sub.example.com"
            - "192.168.1.1" -> "https://192.168.1.1", "192.168.1.1"
        """
        url_input = url_input.strip()
        
        # Handle empty input
        if not url_input:
            raise ValueError("Empty URL input")
        
        # Remove common copy-paste artifacts
        url_input = self._clean_url_artifacts(url_input)
        
        # Add protocol if missing
        if not re.match(r"^https?://", url_input, re.IGNORECASE):
            # Check if it looks like it has a port
            if ":" in url_input and not url_input.startswith("["):
                # Could be domain:port or IPv6
                parts = url_input.split(":")
                if len(parts) == 2 and parts[1].isdigit():
                    url_input = f"https://{url_input}"
                else:
                    # Might be IPv6 or malformed
                    url_input = f"https://{url_input}"
            else:
                url_input = f"https://{url_input}"
        
        # Parse the URL
        try:
            parsed = urlparse(url_input.lower())
        except Exception as e:
            logger.error(f"Failed to parse URL {url_input}: {e}")
            raise ValueError(f"Invalid URL format: {url_input}") from e
        
        # Extract the clean domain
        if parsed.hostname:
            clean_domain = parsed.hostname
            # Remove www. prefix for clean domain
            if clean_domain.startswith("www."):
                clean_domain = clean_domain[4:]
        else:
            # Fallback to netloc
            clean_domain = parsed.netloc or parsed.path.split("/")[0]
            if clean_domain.startswith("www."):
                clean_domain = clean_domain[4:]
        
        # Rebuild the URL with normalized components
        normalized = urlunparse((
            parsed.scheme or "https",
            parsed.netloc or clean_domain,
            parsed.path or "/",
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return normalized, clean_domain
    
    def _clean_url_artifacts(self, url: str) -> str:
        """Remove common copy-paste artifacts from URLs."""
        # Remove surrounding quotes
        url = url.strip('"\'')
        
        # Remove markdown link syntax [text](url)
        md_link = re.search(r"\[.*?\]\((.*?)\)", url)
        if md_link:
            url = md_link.group(1)
        
        # Remove HTML anchor tags
        html_link = re.search(r'<a\s+href=["\']?(.*?)["\']?[\s>]', url, re.IGNORECASE)
        if html_link:
            url = html_link.group(1)
        
        # Remove trailing punctuation often from copy-paste
        url = re.sub(r"[.,;:!?\s]+$", "", url)
        
        return url
    
    async def find_accessible_url(self, domain: str, max_attempts: int = 4) -> Optional[str]:
        """
        Try to find the most accessible version of a domain.
        
        Attempts in order:
        1. https://domain (as provided)
        2. https://www.domain (add www)
        3. http://domain (fallback to http)
        4. https://domain without path (if path was included)
        """
        normalized, clean_domain = self.normalize_url(domain)
        
        # Parse the normalized URL
        parsed = urlparse(normalized)
        base_domain = parsed.netloc
        
        # URLs to try in order
        attempts = []
        
        # 1. Try the normalized URL as-is
        attempts.append(normalized)
        
        # 2. Try with/without www
        if base_domain.startswith("www."):
            # Try without www
            no_www = normalized.replace(f"://{base_domain}", f"://{base_domain[4:]}", 1)
            attempts.append(no_www)
        else:
            # Try with www
            with_www = normalized.replace(f"://{base_domain}", f"://www.{base_domain}", 1)
            attempts.append(with_www)
        
        # 3. Try http if we started with https
        if parsed.scheme == "https":
            http_version = normalized.replace("https://", "http://", 1)
            attempts.append(http_version)
        
        # 4. Try base domain only (no path) if path exists
        if parsed.path and parsed.path != "/":
            base_only = f"{parsed.scheme}://{parsed.netloc}/"
            if base_only not in attempts:
                attempts.append(base_only)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_attempts = []
        for url in attempts:
            if url not in seen:
                seen.add(url)
                unique_attempts.append(url)
        
        # Try each URL
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for url in unique_attempts[:max_attempts]:
                try:
                    logger.debug(f"Attempting to reach: {url}")
                    response = await client.head(url, follow_redirects=True)
                    
                    # Check if we got a successful response
                    if response.status_code < 400:
                        # Get the final URL after redirects
                        final_url = str(response.url)
                        logger.info(f"Successfully reached {domain} via {final_url}")
                        return final_url
                    
                except httpx.HTTPError as e:
                    logger.debug(f"Failed to reach {url}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Unexpected error reaching {url}: {e}")
                    continue
        
        # If all attempts failed, return None
        logger.warning(f"Could not find accessible URL for {domain}")
        return None
    
    def extract_root_domain(self, url: str) -> str:
        """
        Extract the root domain from a URL using tldextract.
        
        Examples:
            - "https://blog.example.com/path" -> "example.com"
            - "sub.domain.co.uk" -> "domain.co.uk"
        """
        extracted = tldextract.extract(url)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return url
    
    def is_valid_domain(self, domain: str) -> bool:
        """
        Check if a domain appears to be valid.
        
        This includes:
        - Standard domains (example.com)
        - Subdomains (sub.example.com)
        - IP addresses (192.168.1.1)
        - Localhost
        """
        # Remove protocol if present
        domain = re.sub(r"^https?://", "", domain, flags=re.IGNORECASE)
        
        # Check for localhost
        if domain.lower() in ["localhost", "127.0.0.1", "::1"]:
            return True
        
        # Check for IP address (v4)
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if re.match(ip_pattern, domain):
            # Validate IP octets
            octets = domain.split(".")
            return all(0 <= int(octet) <= 255 for octet in octets)
        
        # Check for valid domain pattern
        # Allow letters, numbers, dots, and hyphens
        domain_pattern = r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(domain_pattern, domain))
    
    def suggest_alternatives(self, failed_url: str) -> list[str]:
        """
        Suggest alternative URLs when the original fails.
        
        Returns a list of suggestions based on common patterns.
        """
        suggestions = []
        normalized, clean_domain = self.normalize_url(failed_url)
        parsed = urlparse(normalized)
        
        # Extract root domain
        root = self.extract_root_domain(normalized)
        
        suggestions.extend([
            f"https://{root}",
            f"https://www.{root}",
            f"http://{root}",
            f"http://www.{root}",
        ])
        
        # If it's a subdomain, try the root domain
        if parsed.netloc and parsed.netloc.count(".") > 1:
            suggestions.append(f"https://{root}")
        
        # Remove duplicates and return
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen and s != normalized:
                seen.add(s)
                unique.append(s)
        
        return unique[:5]  # Return top 5 suggestions