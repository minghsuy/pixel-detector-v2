"""Simple API server for pixel detector - for docker-compose testing only."""


from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from pydantic import BaseModel

from .scanner import PixelScanner

app = FastAPI(title="Pixel Detector API", version="0.3.0")


class ScanRequest(BaseModel):
    """Request model for scanning a domain."""
    domain: str
    screenshot: bool = False
    timeout: int = 30000


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.3.0"


@app.get("/health", response_model=HealthResponse)  # type: ignore[misc]
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.post("/scan")  # type: ignore[misc]
async def scan_domain(request: ScanRequest) -> JSONResponse:
    """Scan a single domain for pixel tracking."""
    try:
        scanner = PixelScanner(
            headless=True,
            stealth_mode=True,
            screenshot=request.screenshot,
            timeout=request.timeout
        )
        
        result = await scanner.scan_domain(request.domain)
        return JSONResponse(content=result.dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="127.0.0.1", port=8000)  # Use localhost for security