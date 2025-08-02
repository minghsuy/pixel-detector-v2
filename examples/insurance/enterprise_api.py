#!/usr/bin/env python3
"""
Enterprise API Wrapper for Pixel Detector
Designed for cyber insurance company integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import os
from pathlib import Path

# Import pixel detector components
from pixel_detector import Scanner
from pixel_detector.models.pixel_detection import ScanResult

# Import risk scoring
from risk_scoring import PixelRiskScorer

app = FastAPI(
    title="Pixel Detector Enterprise API",
    description="Healthcare pixel tracking detection for cyber insurance underwriting",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Configuration
API_KEYS = os.getenv("API_KEYS", "demo-key-123").split(",")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "./scan_results"))
RESULTS_DIR.mkdir(exist_ok=True)

# Models
class ScanRequest(BaseModel):
    domain: str = Field(..., description="Domain to scan (e.g., hospital.com)")
    priority: str = Field("normal", description="Scan priority: urgent, high, normal")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook for results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class BatchScanRequest(BaseModel):
    domains: List[str] = Field(..., description="List of domains to scan")
    tag: Optional[str] = Field(None, description="Batch identifier")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook for results")

class UnderwritingCheckRequest(BaseModel):
    company_name: str
    domain: str
    annual_revenue: Optional[float] = None
    current_coverage: Optional[float] = None
    renewal_date: Optional[str] = None

class PortfolioMonitorRequest(BaseModel):
    client_domains: List[Dict[str, str]] = Field(..., description="List of {client_id, domain}")
    alert_threshold: str = Field("high", description="Alert level: critical, high, medium")

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials

# Scanner instance
scanner = Scanner()
risk_scorer = PixelRiskScorer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/scan")
async def scan_single(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Scan a single domain for pixel tracking"""
    
    # For urgent requests, scan immediately
    if request.priority == "urgent":
        try:
            result = await scanner.scan_domain(request.domain)
            risk_assessment = risk_scorer.calculate_risk_score(result.model_dump())
            
            return {
                "status": "completed",
                "scan_id": f"scan_{datetime.now().timestamp()}",
                "result": risk_assessment
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # For normal priority, queue in background
    scan_id = f"scan_{datetime.now().timestamp()}"
    background_tasks.add_task(
        background_scan,
        scan_id,
        request.domain,
        request.callback_url,
        request.metadata
    )
    
    return {
        "status": "queued",
        "scan_id": scan_id,
        "message": "Scan queued for processing"
    }

@app.post("/batch")
async def scan_batch(
    request: BatchScanRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Scan multiple domains in batch"""
    
    batch_id = f"batch_{request.tag or datetime.now().timestamp()}"
    
    background_tasks.add_task(
        batch_scan,
        batch_id,
        request.domains,
        request.callback_url
    )
    
    return {
        "status": "queued",
        "batch_id": batch_id,
        "domains_count": len(request.domains),
        "estimated_completion": (datetime.now() + timedelta(seconds=len(request.domains) * 10)).isoformat()
    }

@app.post("/underwriting/check")
async def underwriting_check(
    request: UnderwritingCheckRequest,
    api_key: str = Depends(verify_api_key)
):
    """Real-time underwriting decision based on pixel risk"""
    
    try:
        # Scan the domain
        scan_result = await scanner.scan_domain(request.domain)
        risk_assessment = risk_scorer.calculate_risk_score(scan_result.model_dump())
        
        # Make underwriting decision
        risk_score = risk_assessment["risk_assessment"]["risk_score"]
        risk_level = risk_assessment["risk_assessment"]["risk_level"]
        fine_exposure = risk_assessment["risk_assessment"]["total_fine_exposure"]
        
        # Calculate premium
        base_premium = 50000  # Base cyber insurance premium
        if request.annual_revenue:
            base_premium = request.annual_revenue * 0.001  # 0.1% of revenue
        
        premium_adjustment = risk_assessment["insurance_metrics"]["premium_adjustment_percentage"]
        adjusted_premium = base_premium * (1 + premium_adjustment / 100)
        
        # Determine decision
        if risk_level == "critical":
            decision = "DECLINE"
            reason = "Critical HIPAA violation risk - tracking pixels must be removed"
        elif risk_level == "high":
            decision = "CONDITIONAL"
            reason = "High risk - requires immediate remediation within 30 days"
        else:
            decision = "ACCEPT"
            reason = "Acceptable risk level"
        
        return {
            "underwriting_decision": {
                "decision": decision,
                "reason": reason,
                "risk_score": risk_score,
                "risk_level": risk_level
            },
            "pricing": {
                "base_premium": base_premium,
                "adjustment_percentage": premium_adjustment,
                "adjusted_premium": adjusted_premium,
                "fine_exposure": fine_exposure
            },
            "requirements": risk_assessment["recommendations"],
            "scan_details": {
                "domain": request.domain,
                "pixels_found": risk_assessment["risk_assessment"]["pixels_found"],
                "pixel_types": risk_assessment["risk_assessment"]["pixel_types"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/monitor")
async def monitor_portfolio(
    request: PortfolioMonitorRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Monitor entire portfolio for pixel compliance"""
    
    monitor_id = f"monitor_{datetime.now().timestamp()}"
    
    background_tasks.add_task(
        portfolio_monitor,
        monitor_id,
        request.client_domains,
        request.alert_threshold
    )
    
    return {
        "status": "monitoring_started",
        "monitor_id": monitor_id,
        "clients_count": len(request.client_domains),
        "alert_threshold": request.alert_threshold
    }

@app.get("/results/{scan_id}")
async def get_results(
    scan_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Retrieve scan results"""
    
    result_file = RESULTS_DIR / f"{scan_id}.json"
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    with open(result_file, 'r') as f:
        return json.load(f)

# Background tasks
async def background_scan(scan_id: str, domain: str, callback_url: Optional[str], metadata: Optional[Dict]):
    """Perform scan in background"""
    try:
        result = await scanner.scan_domain(domain)
        risk_assessment = risk_scorer.calculate_risk_score(result.model_dump())
        
        # Add metadata
        risk_assessment["scan_id"] = scan_id
        risk_assessment["metadata"] = metadata
        
        # Save results
        with open(RESULTS_DIR / f"{scan_id}.json", 'w') as f:
            json.dump(risk_assessment, f, indent=2)
        
        # Send webhook if configured
        if callback_url:
            # Implementation depends on your webhook service
            pass
            
    except Exception as e:
        error_result = {
            "scan_id": scan_id,
            "error": str(e),
            "status": "failed"
        }
        with open(RESULTS_DIR / f"{scan_id}.json", 'w') as f:
            json.dump(error_result, f, indent=2)

async def batch_scan(batch_id: str, domains: List[str], callback_url: Optional[str]):
    """Perform batch scan"""
    results = []
    
    for domain in domains:
        try:
            scan_result = await scanner.scan_domain(domain)
            risk_assessment = risk_scorer.calculate_risk_score(scan_result.model_dump())
            results.append(risk_assessment)
        except Exception as e:
            results.append({
                "domain": domain,
                "error": str(e),
                "status": "failed"
            })
    
    # Save batch results
    batch_summary = {
        "batch_id": batch_id,
        "completed_at": datetime.now().isoformat(),
        "total_scanned": len(domains),
        "results": results
    }
    
    with open(RESULTS_DIR / f"{batch_id}.json", 'w') as f:
        json.dump(batch_summary, f, indent=2)
    
    # Send webhook if configured
    if callback_url:
        # Implementation depends on your webhook service
        pass

async def portfolio_monitor(monitor_id: str, client_domains: List[Dict[str, str]], alert_threshold: str):
    """Monitor portfolio and generate alerts"""
    alerts = []
    
    for client in client_domains:
        try:
            scan_result = await scanner.scan_domain(client["domain"])
            risk_assessment = risk_scorer.calculate_risk_score(scan_result.model_dump())
            
            risk_level = risk_assessment["risk_assessment"]["risk_level"]
            
            # Check if alert needed
            should_alert = False
            if alert_threshold == "critical" and risk_level == "critical":
                should_alert = True
            elif alert_threshold == "high" and risk_level in ["critical", "high"]:
                should_alert = True
            elif alert_threshold == "medium" and risk_level in ["critical", "high", "medium"]:
                should_alert = True
            
            if should_alert:
                alerts.append({
                    "client_id": client.get("client_id"),
                    "domain": client["domain"],
                    "risk_level": risk_level,
                    "fine_exposure": risk_assessment["risk_assessment"]["fine_exposure_formatted"],
                    "pixels_found": risk_assessment["risk_assessment"]["pixel_types"],
                    "recommendations": risk_assessment["recommendations"]
                })
                
        except Exception as e:
            alerts.append({
                "client_id": client.get("client_id"),
                "domain": client["domain"],
                "error": str(e)
            })
    
    # Save monitoring results
    monitor_results = {
        "monitor_id": monitor_id,
        "completed_at": datetime.now().isoformat(),
        "total_monitored": len(client_domains),
        "alerts_generated": len(alerts),
        "alerts": alerts
    }
    
    with open(RESULTS_DIR / f"{monitor_id}.json", 'w') as f:
        json.dump(monitor_results, f, indent=2)
    
    # Send alerts via webhook/email/slack
    if alerts and WEBHOOK_URL:
        # Implementation depends on your alerting service
        pass

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize scanner on startup"""
    print(f"Pixel Detector Enterprise API started")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"API keys configured: {len(API_KEYS)}")

# Run with: uvicorn enterprise_api:app --host 0.0.0.0 --port 8000