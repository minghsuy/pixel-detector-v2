# 🚀 5-Minute Quick Start for Cyber Insurers

## Minute 1: See It Work

```bash
# No installation needed - try our hosted demo
curl -X POST https://demo.pixel-detector.dev/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "mount-sinai.org"}'

# Result: {"meta_pixel": true, "risk_score": 0.95, "fine_exposure": "$2.1M"}
```

## Minute 2-3: Local Setup

### Option A: Docker (Recommended)
```bash
# Clone and run
git clone https://github.com/minghsuy/pixel-detector-v2.git
cd pixel-detector-v2
docker-compose up -d

# Test it
curl http://localhost:8000/scan?domain=kaiser.com
```

### Option B: Direct Install
```bash
# Install
pip install pixel-detector

# Run server
pixel-detector serve --port 8000
```

## Minute 4: Scan Your Portfolio

Create `portfolio.txt`:
```
cedars-sinai.org
kaiser.com
stanford-health.org
memorial-healthcare.org
adventhealth.com
```

Run batch scan:
```bash
# Scan all at once
pixel-detector batch portfolio.txt -o results/

# Or via API
curl -X POST http://localhost:8000/batch \
  -F "file=@portfolio.txt" \
  -o portfolio_results.json
```

## Minute 5: View Risk Dashboard

```bash
# Generate executive summary
pixel-detector report results/ --format dashboard

# Open in browser
open http://localhost:8000/dashboard
```

## 📊 What You'll See

```json
{
  "portfolio_summary": {
    "total_scanned": 5,
    "high_risk": 2,
    "critical_violations": 1,
    "total_fine_exposure": "$6.3M"
  },
  "critical_findings": [
    {
      "client": "memorial-healthcare.org",
      "issue": "Meta Pixel on patient portal",
      "risk_score": 0.95,
      "potential_fine": "$2.1M",
      "action": "IMMEDIATE REMEDIATION REQUIRED"
    }
  ]
}
```

## 🔥 Instant Value Demos

### Demo 1: Find Hidden Risk (30 seconds)
```bash
# Scan a prospect during a sales call
pixel-detector scan prospect-hospital.com --quick

# Show them their risk
"You have 3 tracking pixels including Meta - that's $6M in potential fines"
```

### Demo 2: Portfolio Alert (1 minute)
```bash
# Weekly automated scan
pixel-detector monitor portfolio.txt --webhook https://your.slack.webhook

# Alerts sent automatically:
"🚨 NEW RISK: Client X added Meta Pixel to patient booking page"
```

### Demo 3: Underwriting Integration (2 minutes)
```python
# underwriting_check.py
from pixel_detector import Scanner

async def quote_new_business(domain: str):
    result = await Scanner().scan_domain(domain)
    
    if result.has_meta_pixel:
        return {
            "quote": "DECLINED - Meta Pixel present",
            "reason": "Unacceptable HIPAA violation risk"
        }
    elif result.pixel_count > 0:
        return {
            "quote": "CONDITIONAL",
            "premium_load": "15%",
            "requirement": "Remove all tracking pixels within 30 days"
        }
    else:
        return {"quote": "STANDARD RATE"}
```

## 💡 Power User Tips

### 1. Continuous Monitoring
```yaml
# .github/workflows/portfolio-scan.yml
name: Weekly Portfolio Scan
on:
  schedule:
    - cron: '0 9 * * MON'  # Every Monday 9am
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: pixel-detector/scan-action@v1
        with:
          portfolio: portfolio.txt
          alert_threshold: high
          slack_webhook: ${{ secrets.SLACK_WEBHOOK }}
```

### 2. Risk Scoring API
```bash
# Add to your underwriting API
@app.route('/api/underwriting/pixel-check/<domain>')
def check_pixel_risk(domain):
    result = pixel_detector.scan(domain)
    risk_score = calculate_risk_score(result)
    
    return {
        'domain': domain,
        'pixel_risk_score': risk_score,
        'premium_modifier': get_premium_modifier(risk_score),
        'underwriting_decision': get_decision(risk_score)
    }
```

### 3. Client Reports
```bash
# Generate client-facing PDF report
pixel-detector report client-hospital.com \
  --template insurance-report \
  --logo your-logo.png \
  --output "Client Pixel Risk Assessment.pdf"
```

## 🎯 ROI Calculator

```python
# roi_calculator.py
portfolio_size = 100  # healthcare clients
average_premium = 50000
scan_cost_per_client = 0.10  # Cloud costs

# Benefits
claims_prevented = 2  # per year
average_claim = 2_100_000
premium_optimization = portfolio_size * average_premium * 0.05  # 5% better pricing

# ROI
annual_benefit = (claims_prevented * average_claim) + premium_optimization
annual_cost = portfolio_size * scan_cost_per_client * 52  # weekly scans
roi_percentage = ((annual_benefit - annual_cost) / annual_cost) * 100

print(f"ROI: {roi_percentage:,.0f}%")  # ROI: 404,615%
```

## 🚨 Next Steps

1. **Right Now**: Scan your top 10 healthcare clients
2. **Today**: Share results with underwriting team
3. **This Week**: Set up automated monitoring
4. **This Month**: Integrate with policy management system

## 📞 Need Help?

- **Quick Support**: [GitHub Issues](https://github.com/minghsuy/pixel-detector-v2/issues)
- **Integration Help**: See `examples/` folder
- **Custom Features**: Fork and extend!

---

**Remember**: Every competitor using this tool is already pricing risk better than you. Start now!