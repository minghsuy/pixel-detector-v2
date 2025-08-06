"""Simple API server for pixel detector - for docker-compose testing only."""

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post("/scan")
async def scan_domain(request: ScanRequest):
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
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)