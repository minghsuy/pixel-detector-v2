from abc import ABC, abstractmethod
from re import Pattern

from playwright.async_api import Page, Request

from ..models import PixelDetection, PixelEvidence, PixelType, RiskLevel


class BasePixelDetector(ABC):
    """Base class for all pixel detectors"""

    def __init__(self) -> None:
        self.network_requests: list[str] = []
        self.cookies_found: set[str] = set()
        self.script_tags: list[str] = []
        self.global_variables: list[str] = []
        self.dom_elements: list[str] = []
        self.meta_tags: list[str] = []
        self.pixel_ids: set[str] = set()

    @property
    @abstractmethod
    def pixel_type(self) -> PixelType:
        """Return the type of pixel this detector identifies"""
        pass

    @property
    @abstractmethod
    def tracking_domains(self) -> list[str]:
        """List of domains used by this tracking pixel"""
        pass

    @property
    @abstractmethod
    def script_patterns(self) -> list[Pattern[str]]:
        """Regex patterns to identify tracking scripts"""
        pass

    @property
    @abstractmethod
    def cookie_names(self) -> list[str]:
        """Cookie names used by this tracker"""
        pass

    @property
    def risk_level(self) -> RiskLevel:
        """Default risk level for this pixel type"""
        return RiskLevel.HIGH

    @property
    def hipaa_concern(self) -> bool:
        """Whether this pixel type raises HIPAA concerns"""
        return True

    def reset(self) -> None:
        """Reset detector state for new scan"""
        self.network_requests.clear()
        self.cookies_found.clear()
        self.script_tags.clear()
        self.global_variables.clear()
        self.dom_elements.clear()
        self.meta_tags.clear()
        self.pixel_ids.clear()

    async def check_request(self, request: Request) -> bool:
        """Check if a network request is from this tracker"""
        url = request.url
        for domain in self.tracking_domains:
            if domain in url:
                self.network_requests.append(url)
                # Try to extract pixel ID from URL
                pixel_id = self.extract_pixel_id(url)
                if pixel_id:
                    self.pixel_ids.add(pixel_id)
                return True
        return False

    async def check_cookies(self, page: Page) -> None:
        """Check for tracking cookies"""
        cookies = await page.context.cookies()
        for cookie in cookies:
            if cookie["name"] in self.cookie_names:
                self.cookies_found.add(cookie["name"])

    async def check_dom(self, page: Page) -> None:
        """Check DOM for tracking elements"""
        # Check for script tags
        scripts = await page.evaluate(
            """() => {
            return Array.from(document.querySelectorAll('script')).map(s => s.outerHTML);
        }"""
        )
        
        for script in scripts:
            for pattern in self.script_patterns:
                if pattern.search(script):
                    self.script_tags.append(script[:500])  # Limit length
                    # Try to extract pixel ID from script
                    pixel_id = self.extract_pixel_id_from_script(script)
                    if pixel_id:
                        self.pixel_ids.add(pixel_id)

        # Check for global variables
        await self.check_global_variables(page)

        # Check for specific DOM elements
        await self.check_dom_elements(page)

        # Check meta tags
        await self.check_meta_tags(page)

    @abstractmethod
    async def check_global_variables(self, page: Page) -> None:
        """Check for tracker-specific global variables"""
        # Override in subclasses for specific checks
        pass

    @abstractmethod
    async def check_dom_elements(self, page: Page) -> None:
        """Check for tracker-specific DOM elements"""
        # Override in subclasses for specific checks
        pass

    @abstractmethod
    async def check_meta_tags(self, page: Page) -> None:
        """Check for tracker-specific meta tags"""
        # Override in subclasses for specific checks
        pass

    def extract_pixel_id(self, url: str) -> str | None:
        """Extract pixel ID from URL"""
        # Override in subclasses for specific extraction logic
        return None

    def extract_pixel_id_from_script(self, script: str) -> str | None:
        """Extract pixel ID from script content"""
        # Override in subclasses for specific extraction logic
        return None

    def build_detection(self) -> PixelDetection | None:
        """Build detection result if pixel was found"""
        if not self.is_detected():
            return None

        evidence = PixelEvidence(
            network_requests=self.network_requests,
            script_tags=self.script_tags,
            cookies_set=list(self.cookies_found),
            global_variables=self.global_variables,
            dom_elements=self.dom_elements,
            meta_tags=self.meta_tags,
        )

        pixel_id = self.pixel_ids.pop() if self.pixel_ids else None

        return PixelDetection(
            type=self.pixel_type,
            evidence=evidence,
            risk_level=self.risk_level,
            hipaa_concern=self.hipaa_concern,
            description=self.get_description(),
            pixel_id=pixel_id,
        )

    def is_detected(self) -> bool:
        """Check if pixel was detected"""
        return bool(
            self.network_requests
            or self.script_tags
            or self.cookies_found
            or self.global_variables
            or self.dom_elements
        )

    def get_description(self) -> str:
        """Get description of what was detected"""
        detections = []
        if self.network_requests:
            detections.append(f"{len(self.network_requests)} tracking requests")
        if self.script_tags:
            detections.append(f"{len(self.script_tags)} tracking scripts")
        if self.cookies_found:
            detections.append(f"{len(self.cookies_found)} tracking cookies")
        if self.pixel_ids:
            detections.append(f"Pixel ID: {', '.join(self.pixel_ids)}")

        return f"{self.pixel_type.value} detected: {', '.join(detections)}"