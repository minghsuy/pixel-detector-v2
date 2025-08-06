#!/usr/bin/env python3
"""
Comprehensive URL/domain handler following RFC standards.
Uses tldextract for proper domain parsing.
"""

import re
import ipaddress
from typing import Tuple, Optional, Dict
from urllib.parse import urlparse, urlunparse
import idna  # For international domain names
import tldextract  # Install with: pip install tldextract


class URLHandler:
    """
    Robust URL/domain handler that:
    - Follows RFC 3986 (URI) and RFC 1035 (domain names)
    - Handles international domains (IDN)
    - Extracts clean domain (SLD + TLD)
    - Validates against public suffix list
    """
    
    def __init__(self):
        # Initialize tldextract with fresh public suffix list
        self.extractor = tldextract.TLDExtract(
            include_psl_private_domains=False  # Only use ICANN domains
        )
        
        # Common typos and fixes
        self.common_fixes = {
            'htpp': 'http',
            'htp': 'http',
            'htps': 'https',
            'httpss': 'https',
            'htttp': 'http',
            'htttps': 'https',
            'wwww': 'www',
            'ww.': 'www.',
            'ww ': 'www.',
        }
        
        # Invalid schemes we reject
        self.invalid_schemes = {
            'javascript', 'data', 'vbscript', 'about', 'file', 
            'ftp', 'ftps', 'telnet', 'ssh', 'ldap', 'mailto'
        }
        
    def clean_input(self, url: str) -> str:
        """
        Initial cleaning of input string.
        """
        if not url or not isinstance(url, str):
            return ""
        
        # Remove Unicode spaces and zero-width characters
        url = re.sub(r'[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000\uFEFF]', '', url)
        
        # Standard strip
        url = url.strip()
        
        # Remove quotes if wrapped
        if (url.startswith('"') and url.endswith('"')) or \
           (url.startswith("'") and url.endswith("'")):
            url = url[1:-1]
        
        # Fix common typos
        for typo, fix in self.common_fixes.items():
            if url.lower().startswith(typo):
                url = fix + url[len(typo):]
        
        # Remove trailing dots (valid in DNS but not needed)
        while url.endswith('.') and not url.endswith('..'):
            url = url[:-1]
        
        return url
    
    def is_ip_address(self, host: str) -> bool:
        """
        Check if host is an IP address.
        """
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False
    
    def validate_domain_part(self, domain: str) -> Tuple[bool, str]:
        """
        Validate domain according to RFC 1035.
        Returns (is_valid, error_message)
        """
        # Check length
        if len(domain) > 253:
            return False, "Domain too long (max 253 chars)"
        
        if len(domain) < 3:  # Minimum like "a.b"
            return False, "Domain too short"
        
        # Check for consecutive dots
        if '..' in domain:
            return False, "Consecutive dots not allowed"
        
        # Check each label
        labels = domain.split('.')
        for label in labels:
            if not label:
                return False, "Empty domain label"
            
            if len(label) > 63:
                return False, f"Label '{label}' too long (max 63 chars)"
            
            # Label can't start or end with hyphen
            if label.startswith('-') or label.endswith('-'):
                return False, f"Label '{label}' starts/ends with hyphen"
            
            # Check for valid characters (after IDN conversion)
            if not re.match(r'^[a-z0-9-]+$', label.lower()):
                # Try IDN encoding
                try:
                    idna.encode(label)
                except (idna.IDNAError, UnicodeError):
                    return False, f"Invalid characters in label '{label}'"
        
        return True, ""
    
    def extract_domain(self, url: str) -> Tuple[bool, str, Dict[str, any]]:
        """
        Main extraction method.
        Returns: (is_valid, clean_domain, metadata)
        
        Metadata includes:
        - original: Original input
        - cleaned: Cleaned input
        - scheme: Protocol used
        - subdomain: Subdomain if any
        - domain: SLD
        - tld: TLD
        - registered_domain: SLD + TLD
        - path: Path if any
        - is_ip: Whether it's an IP address
        - error: Error message if invalid
        """
        metadata = {
            'original': url,
            'cleaned': '',
            'scheme': '',
            'subdomain': '',
            'domain': '',
            'tld': '',
            'registered_domain': '',
            'path': '',
            'is_ip': False,
            'error': ''
        }
        
        # Step 1: Clean input
        url = self.clean_input(url)
        if not url:
            metadata['error'] = "Empty input"
            return False, "", metadata
        
        metadata['cleaned'] = url
        
        # Step 2: Add scheme if missing
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
            # No scheme, try to add one
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = 'https://' + url
        
        # Step 3: Parse URL
        try:
            parsed = urlparse(url.lower())
        except Exception as e:
            metadata['error'] = f"URL parse error: {str(e)}"
            return False, "", metadata
        
        # Step 4: Check scheme
        if parsed.scheme in self.invalid_schemes:
            metadata['error'] = f"Invalid scheme: {parsed.scheme}"
            return False, "", metadata
        
        if parsed.scheme not in ['http', 'https', '']:
            metadata['error'] = f"Unsupported scheme: {parsed.scheme}"
            return False, "", metadata
        
        metadata['scheme'] = parsed.scheme or 'https'
        
        # Step 5: Extract hostname
        hostname = parsed.hostname or parsed.netloc.split(':')[0]
        if not hostname:
            metadata['error'] = "No hostname found"
            return False, "", metadata
        
        # Step 6: Check if IP address
        if self.is_ip_address(hostname):
            metadata['is_ip'] = True
            metadata['registered_domain'] = hostname
            return True, hostname, metadata
        
        # Step 7: Validate domain
        is_valid, error = self.validate_domain_part(hostname)
        if not is_valid:
            metadata['error'] = error
            return False, "", metadata
        
        # Step 8: Extract with tldextract
        try:
            extracted = self.extractor(url)
        except Exception as e:
            metadata['error'] = f"Extraction error: {str(e)}"
            return False, "", metadata
        
        # Step 9: Check if valid TLD
        if not extracted.suffix:
            metadata['error'] = "No valid TLD found"
            return False, "", metadata
        
        if not extracted.domain:
            metadata['error'] = "No domain found"
            return False, "", metadata
        
        # Step 10: Build clean domain
        registered_domain = f"{extracted.domain}.{extracted.suffix}"
        
        # Handle IDN
        try:
            # Try to encode as ASCII (punycode)
            registered_domain_ascii = idna.encode(registered_domain).decode('ascii')
        except (idna.IDNAError, UnicodeError):
            registered_domain_ascii = registered_domain
        
        # Fill metadata
        metadata['subdomain'] = extracted.subdomain
        metadata['domain'] = extracted.domain
        metadata['tld'] = extracted.suffix
        metadata['registered_domain'] = registered_domain_ascii
        metadata['path'] = parsed.path if parsed.path and parsed.path != '/' else ''
        
        return True, registered_domain_ascii, metadata
    
    def normalize_for_scanning(self, url: str) -> Tuple[bool, str, str]:
        """
        Normalize URL for scanning purposes.
        Returns: (is_valid, scan_url, error_message)
        
        The scan_url will be just the registered domain with https://
        """
        is_valid, domain, metadata = self.extract_domain(url)
        
        if not is_valid:
            return False, "", metadata.get('error', 'Invalid URL')
        
        # For scanning, use just the registered domain
        scan_url = f"https://{domain}"
        
        return True, scan_url, ""


def test_handler():
    """
    Test the URL handler with various cases.
    """
    handler = URLHandler()
    
    test_cases = [
        # Valid cases
        "google.com",
        "www.google.com",
        "https://google.com",
        "GOOGLE.COM",
        "mail.google.com",
        "https://google.com/search?q=test",
        "google.com:8080",
        "münchen.de",
        "a.co",
        "subdomain.google.co.uk",
        "192.168.1.1",
        "https://192.168.1.1:8080",
        
        # Invalid cases
        "google",
        ".com",
        "google..com",
        "javascript:alert(1)",
        "data:text/html,test",
        "ftp://google.com",
        "",
        "none",
        "user@example.com",
        
        # Edge cases
        "google.com.",
        "  google.com  ",
        "https://google.com/",
        "htps://google.com",
        "wwww.google.com",
    ]
    
    print("URL Handler Test Results")
    print("=" * 80)
    print(f"{'Input':<30} {'Valid':<7} {'Clean Domain':<25} {'Error':<30}")
    print("-" * 80)
    
    for test_url in test_cases:
        is_valid, domain, metadata = handler.extract_domain(test_url)
        
        # Truncate for display
        input_display = test_url[:28] + ".." if len(test_url) > 30 else test_url
        domain_display = domain[:23] + ".." if len(domain) > 25 else domain
        error_display = metadata.get('error', '')[:28] + ".." if len(metadata.get('error', '')) > 30 else metadata.get('error', '')
        
        print(f"{input_display:<30} {str(is_valid):<7} {domain_display:<25} {error_display:<30}")


if __name__ == "__main__":
    # Run tests
    test_handler()
    
    # Example usage
    print("\n" + "=" * 80)
    print("Example Usage:")
    print("=" * 80)
    
    handler = URLHandler()
    
    test_url = "https://www.stanford.edu/medicine/research.html?page=1"
    is_valid, domain, metadata = handler.extract_domain(test_url)
    
    print(f"\nInput: {test_url}")
    print(f"Valid: {is_valid}")
    print(f"Clean domain: {domain}")
    print(f"Metadata:")
    for key, value in metadata.items():
        if value:
            print(f"  {key}: {value}")