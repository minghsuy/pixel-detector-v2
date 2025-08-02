#!/usr/bin/env python3
"""
Cyber Insurance Risk Scoring System
Converts pixel detection results into insurance risk metrics
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from enum import Enum

class RiskLevel(Enum):
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"         # Significant risk
    MEDIUM = "medium"     # Moderate risk
    LOW = "low"          # Acceptable risk
    CLEAN = "clean"      # No tracking pixels


class PixelRiskScorer:
    """Calculate insurance risk scores based on pixel detection results"""
    
    # Risk weights based on HIPAA violation potential
    PIXEL_RISK_WEIGHTS = {
        "meta_pixel": 1.0,       # Highest risk - no BAA available
        "google_ads": 0.9,       # Critical - remarketing lists
        "google_analytics": 0.8, # High risk - no healthcare BAA
        "tiktok": 0.7,          # Foreign data sovereignty
        "linkedin": 0.6,        # B2B data sharing
        "twitter": 0.6,         # Social media targeting
        "pinterest": 0.5,       # Lower healthcare usage
        "snapchat": 0.5,        # Younger demographic
    }
    
    # HIPAA fine estimates based on historical data
    FINE_ESTIMATES = {
        "meta_pixel": 2_100_000,      # Based on Novant Health fine
        "google_ads": 1_800_000,      # Remarketing violations
        "google_analytics": 1_500_000, # Analytics without BAA
        "tiktok": 1_200_000,          # Emerging enforcement
        "linkedin": 800_000,          # Professional data
        "twitter": 800_000,           # Social targeting
        "pinterest": 600_000,         # Lower risk profile
        "snapchat": 600_000,          # Limited healthcare use
    }
    
    def calculate_risk_score(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a domain"""
        
        # Extract detected pixels
        pixels_detected = scan_result.get("pixels_detected", [])
        
        # Calculate base risk score
        risk_score = 0.0
        detected_types = []
        total_fine_exposure = 0
        
        for pixel in pixels_detected:
            pixel_type = pixel["type"]
            weight = self.PIXEL_RISK_WEIGHTS.get(pixel_type, 0.5)
            risk_score += weight
            detected_types.append(pixel_type)
            total_fine_exposure += self.FINE_ESTIMATES.get(pixel_type, 500_000)
        
        # Normalize risk score to 0-1 range
        max_possible_score = sum(self.PIXEL_RISK_WEIGHTS.values())
        normalized_score = min(risk_score / max_possible_score, 1.0)
        
        # Determine risk level
        if normalized_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif normalized_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif normalized_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        elif normalized_score > 0:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.CLEAN
        
        # Calculate premium adjustment
        premium_adjustment = self._calculate_premium_adjustment(normalized_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(detected_types, risk_level)
        
        return {
            "domain": scan_result.get("domain"),
            "scan_timestamp": scan_result.get("timestamp"),
            "risk_assessment": {
                "risk_score": round(normalized_score, 3),
                "risk_level": risk_level.value,
                "pixels_found": len(pixels_detected),
                "pixel_types": detected_types,
                "total_fine_exposure": total_fine_exposure,
                "fine_exposure_formatted": f"${total_fine_exposure:,.0f}"
            },
            "insurance_metrics": {
                "premium_adjustment_percentage": premium_adjustment,
                "requires_immediate_action": risk_level == RiskLevel.CRITICAL,
                "eligible_for_coverage": risk_level != RiskLevel.CRITICAL,
                "remediation_required": risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
            },
            "recommendations": recommendations,
            "compliance_status": {
                "hipaa_compliant": risk_level == RiskLevel.CLEAN,
                "requires_baa": len(detected_types) > 0,
                "violation_risk": risk_level.value
            }
        }
    
    def _calculate_premium_adjustment(self, risk_score: float) -> float:
        """Calculate premium adjustment based on risk score"""
        if risk_score >= 0.8:
            return 50.0  # 50% premium increase
        elif risk_score >= 0.6:
            return 25.0  # 25% premium increase
        elif risk_score >= 0.3:
            return 10.0  # 10% premium increase
        elif risk_score > 0:
            return 5.0   # 5% premium increase
        else:
            return -5.0  # 5% premium discount for clean sites
    
    def _generate_recommendations(self, pixel_types: List[str], 
                                 risk_level: RiskLevel) -> List[str]:
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Remove all tracking pixels before coverage")
        
        if "meta_pixel" in pixel_types:
            recommendations.append("Remove Meta/Facebook Pixel immediately - highest HIPAA violation risk")
        
        if "google_ads" in pixel_types:
            recommendations.append("Disable Google Ads remarketing on healthcare pages")
        
        if "google_analytics" in pixel_types:
            recommendations.append("Migrate to HIPAA-compliant analytics solution or obtain BAA")
        
        if any(p in pixel_types for p in ["tiktok", "snapchat"]):
            recommendations.append("Remove social media pixels - incompatible with healthcare privacy")
        
        if risk_level == RiskLevel.CLEAN:
            recommendations.append("Maintain current privacy practices - no tracking pixels detected")
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Conduct immediate privacy audit with legal counsel")
            recommendations.append("Implement pixel monitoring to prevent unauthorized additions")
        
        return recommendations


def analyze_portfolio(results_dir: str) -> Dict[str, Any]:
    """Analyze entire portfolio of scan results"""
    
    scorer = PixelRiskScorer()
    results_path = Path(results_dir)
    
    portfolio_analysis = {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_sites_scanned": 0,
        "risk_distribution": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "clean": 0
        },
        "total_fine_exposure": 0,
        "high_risk_clients": [],
        "clean_clients": [],
        "portfolio_metrics": {}
    }
    
    # Process each scan result
    for json_file in results_path.glob("*.json"):
        if json_file.name == "summary.json":
            continue
            
        with open(json_file, 'r') as f:
            scan_result = json.load(f)
        
        # Calculate risk score
        risk_assessment = scorer.calculate_risk_score(scan_result)
        
        # Update portfolio statistics
        portfolio_analysis["total_sites_scanned"] += 1
        risk_level = risk_assessment["risk_assessment"]["risk_level"]
        portfolio_analysis["risk_distribution"][risk_level] += 1
        portfolio_analysis["total_fine_exposure"] += risk_assessment["risk_assessment"]["total_fine_exposure"]
        
        # Track high-risk and clean clients
        if risk_level in ["critical", "high"]:
            portfolio_analysis["high_risk_clients"].append({
                "domain": risk_assessment["domain"],
                "risk_level": risk_level,
                "fine_exposure": risk_assessment["risk_assessment"]["fine_exposure_formatted"],
                "pixels": risk_assessment["risk_assessment"]["pixel_types"]
            })
        elif risk_level == "clean":
            portfolio_analysis["clean_clients"].append(risk_assessment["domain"])
    
    # Calculate portfolio metrics
    total = portfolio_analysis["total_sites_scanned"]
    if total > 0:
        portfolio_analysis["portfolio_metrics"] = {
            "high_risk_percentage": round((portfolio_analysis["risk_distribution"]["critical"] + 
                                         portfolio_analysis["risk_distribution"]["high"]) / total * 100, 1),
            "clean_percentage": round(portfolio_analysis["risk_distribution"]["clean"] / total * 100, 1),
            "average_fine_exposure": portfolio_analysis["total_fine_exposure"] / total,
            "total_fine_exposure_formatted": f"${portfolio_analysis['total_fine_exposure']:,.0f}"
        }
    
    return portfolio_analysis


def generate_executive_report(portfolio_analysis: Dict[str, Any]) -> str:
    """Generate executive summary for insurance leadership"""
    
    report = f"""
# Pixel Risk Portfolio Analysis - Executive Summary
Generated: {portfolio_analysis['analysis_timestamp']}

## Portfolio Overview
- **Total Healthcare Clients Scanned**: {portfolio_analysis['total_sites_scanned']}
- **Total Fine Exposure**: {portfolio_analysis['portfolio_metrics']['total_fine_exposure_formatted']}
- **High-Risk Clients**: {len(portfolio_analysis['high_risk_clients'])} ({portfolio_analysis['portfolio_metrics']['high_risk_percentage']}%)
- **Clean Clients**: {len(portfolio_analysis['clean_clients'])} ({portfolio_analysis['portfolio_metrics']['clean_percentage']}%)

## Risk Distribution
- Critical Risk: {portfolio_analysis['risk_distribution']['critical']} clients
- High Risk: {portfolio_analysis['risk_distribution']['high']} clients  
- Medium Risk: {portfolio_analysis['risk_distribution']['medium']} clients
- Low Risk: {portfolio_analysis['risk_distribution']['low']} clients
- Clean: {portfolio_analysis['risk_distribution']['clean']} clients

## Immediate Action Required
"""
    
    # Add high-risk clients
    if portfolio_analysis['high_risk_clients']:
        report += "\n### Critical/High Risk Clients Requiring Immediate Attention:\n"
        for client in portfolio_analysis['high_risk_clients'][:10]:  # Top 10
            report += f"- **{client['domain']}**: {client['risk_level'].upper()} - "
            report += f"{client['fine_exposure']} exposure - "
            report += f"Pixels: {', '.join(client['pixels'])}\n"
    
    # Add recommendations
    report += "\n## Strategic Recommendations\n"
    if portfolio_analysis['portfolio_metrics']['high_risk_percentage'] > 30:
        report += "- Launch immediate portfolio-wide remediation program\n"
        report += "- Consider coverage restrictions for non-compliant clients\n"
    
    report += "- Implement continuous monitoring for all healthcare clients\n"
    report += "- Require pixel compliance attestation at renewal\n"
    report += "- Develop pixel remediation resources for clients\n"
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python risk_scoring.py <results_directory>")
        sys.exit(1)
    
    # Analyze portfolio
    results = analyze_portfolio(sys.argv[1])
    
    # Generate report
    report = generate_executive_report(results)
    
    # Save outputs
    with open("risk_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("executive_report.md", "w") as f:
        f.write(report)
    
    print(report)
    print(f"\nDetailed analysis saved to: risk_analysis.json")