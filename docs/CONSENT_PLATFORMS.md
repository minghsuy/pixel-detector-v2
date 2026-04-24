# Consent Management Platform Detection

## Overview

This document describes how the pixel detector identifies consent management platforms (CMPs). CMPs are compliance tools that help websites manage cookie consent under GDPR, CCPA, and other privacy regulations.

Consent platforms are classified as **LOW risk** because they are compliance tools, not tracking violations. However, detecting their presence is crucial for assessing overall privacy compliance.

## Supported Platforms

The detector currently supports the 6 most common consent management platforms, covering approximately 78% of the CMP market.

### OneTrust (40% market share)

**Market Position:** Industry leader, preferred by enterprise and healthcare organizations

**Detection Signals:**
- **Domains:**
  - `cdn.cookielaw.org`
  - `optanon.blob.core.windows.net`
  - `cookie-cdn.cookiepro.com`
- **Global Variables:** `OneTrust`, `OptanonWrapper`, `OnetrustActiveGroups`
- **Cookies:** `OptanonConsent`, `OptanonAlertBoxClosed`
- **DOM Elements:** `#onetrust-consent-sdk`, `#onetrust-banner-sdk`, `.optanon-alert-box-wrapper`

**Pixel ID Format:** UUID (e.g., `01234567-89ab-cdef-0123-456789abcdef`)

**Example Detection:**
```html
<script src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js"
        data-domain-script="01234567-89ab-cdef-0123-456789abcdef"></script>
```

**References:**
- [OneTrust CookiePro Documentation](https://my.onetrust.com/s/)
- [OneTrust Cookie Consent SDK](https://www.cookiepro.com/)

---

### Cookiebot (15% market share)

**Market Position:** Popular in Europe, GDPR-focused, good SMB adoption

**Detection Signals:**
- **Domains:**
  - `consent.cookiebot.com`
  - `cookiebot.com`
- **Global Variables:** `Cookiebot`, `CookieConsent`
- **Cookies:** `CookieConsent`, `CookieConsentBulkSetting`
- **DOM Elements:** `#CookiebotWidget`, elements with `[data-cookieconsent]`

**Pixel ID Format:** UUID in `data-cbid` attribute

**Example Detection:**
```html
<script id="Cookiebot"
        src="https://consent.cookiebot.com/uc.js"
        data-cbid="12345678-90ab-cdef-1234-567890abcdef"></script>
```

**References:**
- [Cookiebot Developer Documentation](https://www.cookiebot.com/en/developer/)
- [Cookiebot API Reference](https://www.cookiebot.com/en/developer-api/)

---

### Osano (8% market share)

**Market Position:** Growing platform, strong privacy-by-design focus

**Detection Signals:**
- **Domains:**
  - `cmp.osano.com`
  - `api.osano.com`
- **Global Variables:** `Osano`, `osano.consentmanager`
- **Cookies:** `osano_consentmanager`, `osano_consentmanager_uuid`
- **DOM Elements:** `.osano-cm-window`, `.osano-cm-widget`

**Pixel ID Format:** Alphanumeric customer ID (5+ characters)

**Example Detection:**
```html
<script src="https://cmp.osano.com/12ABC3/osano.js"></script>
```

**References:**
- [Osano Documentation](https://www.osano.com/cookieconsent/documentation/)
- [Osano Consent Manager](https://www.osano.com/)

---

### TrustArc (7% market share)

**Market Position:** Established player, strong in financial services and healthcare

**Detection Signals:**
- **Domains:**
  - `consent.trustarc.com`
  - `consent-pref.trustarc.com`
  - `trustarc.mgr.consensu.org`
- **Global Variables:** `truste`, `TrustArc`
- **Cookies:** `notice_preferences`, `notice_gdpr_prefs`, `cmapi_cookie_privacy`
- **DOM Elements:** `#truste-consent-track`, `.truste_box_overlay`

**Pixel ID Format:** Domain identifier (e.g., `example.com`)

**Example Detection:**
```html
<script src="https://consent.trustarc.com/notice?domain=example.com"></script>
```

**References:**
- [TrustArc Consent Manager](https://trustarc.com/products/consent-manager/)
- [TrustArc Documentation](https://trustarc.com/resources/)

---

### Usercentrics (5% market share)

**Market Position:** Strong in German/European markets, GDPR compliant

**Detection Signals:**
- **Domains:**
  - `app.usercentrics.eu`
  - `privacy-proxy.usercentrics.eu`
  - `aggregator.service.usercentrics.eu`
- **Global Variables:** `UC_UI`, `usercentrics`
- **Cookies:** `uc_user_interaction`, `uc_settings`
- **DOM Elements:** `#usercentrics-root`, `.usercentrics-modal`

**Pixel ID Format:** Settings ID (alphanumeric with dashes/underscores)

**Example Detection:**
```html
<script src="https://app.usercentrics.eu/latest/main.js"
        id="usercentrics-cmp"
        data-settings-id="ABC123XYZ"></script>
```

**References:**
- [Usercentrics Documentation](https://docs.usercentrics.com/)
- [Usercentrics CMP](https://usercentrics.com/consent-management-platform/)

---

### Termly (3% market share)

**Market Position:** Affordable option for SMBs, good for startups

**Detection Signals:**
- **Domains:**
  - `app.termly.io`
  - `consent.termly.io`
- **Global Variables:** `TermlyConsent`
- **Cookies:** `t_consent_status`, `termly-consent-preferences`
- **DOM Elements:** `#termly-code-snippet-support`, `.termly-consent-banner`

**Pixel ID Format:** UUID (36 characters)

**Example Detection:**
```html
<script src="https://app.termly.io/embed.min.js"
        data-auto-block="on"
        data-website-uuid="12345678-90ab-cdef-1234-567890abcdef"></script>
```

**References:**
- [Termly Consent Management](https://termly.io/products/consent-management/)
- [Termly Documentation](https://help.termly.io/)

---

## Risk Assessment

### Classification

All consent management platforms are classified as:
- **Risk Level:** `LOW`
- **HIPAA Concern:** `False`

**Rationale:** CMPs are compliance tools, not tracking violations. Their presence indicates the website operator is attempting to respect user privacy.

### Compliance Scoring

| Scenario | Risk Level | Premium Impact |
|----------|------------|----------------|
| **Tracking + Consent Platform** | 🟢 LOW-MEDIUM | Baseline or -10% |
| **Tracking + No Consent** | 🔴 CRITICAL | +50% to +200% |
| **No Tracking + Consent** | 🟢 LOW | -10% to -20% |
| **No Tracking + No Consent** | 🟢 LOW | Baseline |

---

## Insurance Use Cases

### 1. Underwriting Assessment

Evaluate consent implementation during quote generation:

```python
from pixel_detector import PixelScanner
from pixel_detector.models import PixelType

async def assess_consent_compliance(domain: str) -> dict:
    scanner = PixelScanner(headless=True)
    result = await scanner.scan_domain(domain)

    has_tracking = any(p.hipaa_concern for p in result.pixels_detected)
    has_consent = any(p.type.value in [
        "onetrust", "cookiebot", "osano",
        "trustarc", "usercentrics", "termly"
    ] for p in result.pixels_detected)

    if has_tracking and not has_consent:
        return {
            "risk_score": 0.9,
            "premium_adjustment": +50,
            "recommendation": "DECLINE or require consent platform implementation"
        }
    elif has_tracking and has_consent:
        return {
            "risk_score": 0.3,
            "premium_adjustment": 0,
            "recommendation": "ACCEPT - verify consent configuration"
        }
    else:
        return {
            "risk_score": 0.1,
            "premium_adjustment": -10,
            "recommendation": "ACCEPT - low risk profile"
        }
```

### 2. Portfolio Monitoring

Scan client sites weekly to detect compliance changes:

```python
# Weekly scan to identify new risks
for client in active_clients:
    current_scan = await scanner.scan_domain(client.domain)
    previous_scan = db.get_last_scan(client.id)

    # Alert on new tracking without consent
    if (not previous_scan.has_tracking and
        current_scan.has_tracking and
        not current_scan.has_consent_platform):
        alert_underwriter(
            client,
            "NEW CRITICAL RISK: Tracking added without consent platform"
        )

    # Alert on consent platform removal
    if (previous_scan.has_consent_platform and
        not current_scan.has_consent_platform):
        alert_underwriter(
            client,
            "WARNING: Consent platform removed, verify compliance"
        )
```

### 3. Gap Analysis

Use the included example script to analyze entire portfolios:

```bash
# Scan your portfolio
uv run python examples/consent_gap_analysis.py portfolio.txt

# Output includes:
# - CRITICAL sites: tracking without consent
# - REVIEW sites: has consent, verify configuration
# - LOW sites: compliant or no tracking
# - CSV report with detailed findings
```

---

## Detection Methodology

### Multi-Signal Detection

Each platform is detected through multiple signals to ensure accuracy:

1. **Network Requests:** Monitor requests to known CMP domains
2. **Script Analysis:** Search page source for CMP script tags
3. **Cookie Detection:** Identify platform-specific consent cookies
4. **DOM Analysis:** Find consent banner elements in page structure
5. **JavaScript Globals:** Check for platform-specific global variables
6. **ID Extraction:** Extract customer/domain IDs for verification

### Confidence Levels

Detection requires multiple signals:
- **High Confidence:** 3+ signals detected (domain + cookie + script)
- **Medium Confidence:** 2 signals detected
- **Low Confidence:** 1 signal detected (may be false positive)

Current implementation reports all detections regardless of signal count. Future versions may include confidence scoring.

---

## Future Enhancements

### Phase 2: Banner Interaction Testing (Planned)

Verify consent platforms function correctly:

```python
# Planned feature - not yet implemented
async def test_consent_rejection(domain: str) -> dict:
    """
    Test if 'Reject All' actually blocks tracking.

    Process:
    1. Load page, wait for consent banner
    2. Click "Reject All" button
    3. Verify no tracking pixels fire
    4. Check cookies are not set

    Returns compliance score based on behavior.
    """
    pass
```

### Phase 3: Timing Analysis (Planned)

Detect GDPR violations where tracking fires before consent:

```python
# Planned feature - not yet implemented
async def analyze_consent_timing(domain: str) -> dict:
    """
    Verify pixels don't fire before consent given.

    Returns:
    - timestamp_consent_given
    - timestamp_first_tracking_request
    - violation: bool (tracking before consent)
    - severity: "critical" | "moderate" | "compliant"
    """
    pass
```

---

## Troubleshooting

### Platform Not Detected

**Problem:** Site has consent banner but no detection

**Solutions:**
1. Check if platform is in supported list (only 6 platforms currently)
2. Verify site loads completely (increase timeout: `PixelScanner(timeout=60000)`)
3. Check browser console for custom implementations
4. Some sites use white-label CMPs not in our detection patterns

### False Positives

**Problem:** Detection reported but no consent banner visible

**Solutions:**
1. Banner may load conditionally (first visit only, specific regions)
2. Check if detection has low signal count (future feature)
3. Verify cookies exist: `document.cookie` in browser console
4. Platform may be installed but not activated

### ID Extraction Failing

**Problem:** `pixel_id` is `null` in results

**Solutions:**
1. Platform may use different ID format than expected
2. Check implementation method (async loading may delay ID)
3. Some platforms don't expose IDs in detectable way
4. Review platform documentation for ID location

---

## References

- [GDPR Cookie Consent Requirements](https://gdpr.eu/cookies/)
- [CCPA Consumer Privacy Act](https://oag.ca.gov/privacy/ccpa)
- [IAB TCF 2.0 Specification](https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework)
- [HIPAA Tracking Technology Guidance (OCR)](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/hipaa-online-tracking/index.html)

---

## Contact

For questions about consent platform detection or to request support for additional platforms, please open an issue on the GitHub repository.

---

# Phase 2: Banner Interaction Testing

## Overview

**Phase 2** adds automated interaction testing to verify that consent platforms actually work correctly. This closes the compliance gap between having a consent banner installed versus the banner functioning properly.

### Why This Matters

Many sites have consent banners that are **malfunctioning**:
- Tracking fires BEFORE user consent (dark pattern)
- "Reject All" doesn't actually block tracking (GDPR/CCPA violation)
- Banner doesn't appear when it should

These malfunctions expose organizations to regulatory fines despite having a CMP installed.

## Quick Start

```bash
# Test consent banner functionality
pixel-detector scan healthcare-site.com --test-consent
```

## The 3-Phase Testing Approach

### 1. Baseline Test (Dark Pattern Detection)

**Purpose:** Detect if tracking fires before user interacts with consent banner

**Method:**
1. Load the page
2. Wait 5 seconds (don't interact with banner)
3. Check which tracking pixels have fired

**Expected Result:**
- ✅ **Compliant (Score: 100)**: Only consent platform detected, no tracking pixels
- ❌ **Violation (Score: 0)**: Tracking pixels fire before consent given

**Example Violation:**
```
BASELINE TEST: malfunctioning
Score: 0/100
❌ Google Analytics fired before consent given (dark pattern)
💡 Move all tracking scripts behind consent check
```

### 2. Reject All Test (Critical GDPR/CCPA Compliance)

**Purpose:** Verify that clicking "Reject All" actually blocks tracking

**Method:**
1. Wait for consent banner to appear
2. Find and click "Reject All" button
3. Wait 2 seconds for rejection to take effect
4. Check if any tracking pixels fire

**Expected Result:**
- ✅ **Compliant (Score: 100)**: No tracking after rejection
- ❌ **Violation (Score: 0)**: Tracking continues despite rejection
- ⚠️ **Missing (Score: 0)**: No consent banner detected

**Button Selectors:**
The system knows how to find reject buttons for all 6 supported CMPs:
- **OneTrust**: `#onetrust-reject-all-handler`, `.ot-pc-refuse-all-handler`
- **Cookiebot**: `#CybotCookiebotDialogBodyButtonDecline`, `[data-cookieconsent="reject"]`
- **Osano**: `.osano-cm-denyAll`, `.osano-cm-dialog__close`
- **TrustArc**: `.truste-button2`, `.pdynamicbutton .decline`
- **Usercentrics**: `[data-testid="uc-deny-all-button"]`, `.sc-bczRLJ.sc-gsnTZi`
- **Termly**: `.t-declineAllButton`, `.t-preference-button[data-action="decline"]`

**Example Violation:**
```
REJECT_ALL TEST: malfunctioning
Score: 0/100
❌ Google Analytics fired AFTER rejection
❌ Meta Pixel detected after clicking reject
💡 Verify consent platform configuration blocks all tracking
```

### 3. Accept All Test (Validation)

**Purpose:** Confirm that tracking works correctly after consent (validates our detection)

**Method:**
1. Wait for consent banner
2. Click "Accept All" button
3. Check that tracking pixels fire correctly

**Expected Result:**
- ✅ **Always passes (Score: 100)**: Validates detection is working
- This is NOT a compliance test, it's a sanity check

## Compliance Scoring

### Score Calculation

Overall score is the average of all test scores:
```
Overall Score = (Baseline Score + Reject Score + Accept Score) / 3
```

### Individual Test Scoring

**Baseline Test:**
- 100 points: No tracking before consent
- 0 points: Any tracking pixel detected

**Reject All Test:**
- 100 points: Banner found, clicked, no tracking after
- 50 points: Banner not found or click failed (inconclusive)
- 0 points: Tracking continues after rejection

**Accept All Test:**
- 100 points: Always (it's a validation test)

### Overall Status

Based on overall score:
- **90-100**: COMPLIANT
- **70-89**: REVIEW (minor issues)
- **50-69**: INCONCLUSIVE (testing failed)
- **0-49**: MISSING/MALFUNCTIONING (critical violations)

## Output Format

### Console Output

```
=== Consent Compliance Testing ===

Overall Compliance Score: 33/100
Status: MISSING

✅ BASELINE TEST: malfunctioning
   Score: 0/100
   ❌ Google Analytics fired before consent given (dark pattern)
   💡 Move all tracking scripts behind consent check

✅ REJECT_ALL TEST: missing
   Score: 0/100
   ❌ No consent banner detected
   💡 Implement consent management platform

🟡 ACCEPT_ALL TEST: inconclusive
   Score: 100/100
   💡 No consent banner detected - test skipped

Recommended Action: DECLINE - Critical consent violations, high risk of privacy lawsuits
```

### JSON Output

```json
{
  "consent_test_results": [
    {
      "test_type": "baseline",
      "compliance_status": "malfunctioning",
      "violation_severity": "critical",
      "compliance_score": 0,
      "violations_detected": [
        "Google Analytics fired before consent given (dark pattern)"
      ],
      "recommendation": "Move all tracking scripts behind consent check",
      "evidence": {
        "action_taken": "baseline",
        "banner_detected": true,
        "banner_platform": "cookiebot",
        "pixels_before_interaction": ["google_analytics", "cookiebot"],
        "timeline": [
          {
            "timestamp_seconds": 0.5,
            "event_type": "banner_detected",
            "details": "Consent banner detected: cookiebot"
          },
          {
            "timestamp_seconds": 1.2,
            "event_type": "tracker_fired",
            "details": "google_analytics detected before consent",
            "pixel_type": "google_analytics"
          }
        ]
      }
    }
  ],
  "consent_compliance_summary": {
    "overall_score": 33,
    "overall_status": "missing",
    "banner_platform": "cookiebot",
    "violations_found": [
      "Google Analytics fired before consent given (dark pattern)",
      "No consent banner detected"
    ],
    "recommended_action": "DECLINE - Critical consent violations, high risk of privacy lawsuits"
  }
}
```

## Timeline Events

Each test captures a detailed timeline of events with sub-second precision:

**Event Types:**
- `test_start`: Test begins
- `banner_detected`: Consent banner found
- `no_banner`: Banner not found within timeout
- `button_clicked`: Successfully clicked button
- `button_not_found`: Could not find button
- `click_failed`: Button found but click failed
- `tracker_fired`: Tracking pixel detected
- `tracker_after_reject`: Tracking detected after rejection
- `wait_complete`: Waiting period finished

**Example Timeline:**
```json
{
  "timeline": [
    {"timestamp_seconds": 0.0, "event_type": "test_start", "details": "Baseline test started"},
    {"timestamp_seconds": 0.52, "event_type": "banner_detected", "details": "Consent banner detected: cookiebot"},
    {"timestamp_seconds": 1.18, "event_type": "tracker_fired", "details": "google_analytics detected before consent", "pixel_type": "google_analytics"},
    {"timestamp_seconds": 5.03, "event_type": "wait_complete", "details": "Waited 3 seconds for tracking to fire"}
  ]
}
```

## Technical Implementation

### Architecture

1. **BannerSelector** (`button_selectors.py`)
   - Contains CSS selectors for all 6 CMP platforms
   - Smart banner detection with platform identification
   - Multi-retry clicking with scroll-into-view and force-click fallbacks

2. **BannerInteractionTester** (`banner_interaction.py`)
   - Performs the 3 test types
   - Captures evidence and timeline events
   - Manages fresh browser pages for each test

3. **ComplianceChecker** (`compliance_checker.py`)
   - Calculates compliance scores
   - Generates violation reports
   - Provides platform-specific recommendations

4. **Data Models** (`models/consent_test.py`)
   - `ConsentTestResult`: Complete test results
   - `ConsentTestEvidence`: Detailed evidence collection
   - `ConsentComplianceSummary`: Overall assessment
   - `TimelineEvent`: Event tracking

### Integration

The consent testing is fully integrated into the main scanner:

```python
scanner = PixelScanner(test_consent=True)
result = await scanner.scan_domain("healthcare-site.com")

# Results include consent testing
if result.consent_compliance_summary:
    print(f"Score: {result.consent_compliance_summary.overall_score}/100")
    print(f"Status: {result.consent_compliance_summary.overall_status}")
```

## Real-World Results

### goodsamsanjose.com

**Platform Detected:** Cookiebot

**Results:**
- Overall Score: 33/100
- Status: MISSING
- **Critical Finding:** Google Analytics fires BEFORE consent (dark pattern)

**Violations:**
1. Google Analytics detected before user interaction
2. No functional reject mechanism

**Recommendation:** DECLINE - Critical violations

### elcaminohealth.org

**Platform Detected:** TrustArc

**Results:**
- Overall Score: 33/100
- Status: MISSING
- **Finding:** No pre-consent tracking (good), but banner didn't appear

**Violations:**
1. Banner not detected during test (implementation issue)

**Recommendation:** REVIEW - Platform installed but not functioning

## Limitations

### Current Limitations

1. **Button Selector Coverage**
   - Covers 6 major CMPs (78% of market)
   - Custom implementations may not be detected
   - Platform updates may break selectors

2. **Test Execution**
   - Single-page test only (doesn't navigate site)
   - 5-second baseline wait (some tracking may load later)
   - Assumes English language buttons

3. **Geographic Restrictions**
   - Tests from scanner's location (may affect banner display)
   - Some banners only show to EU/CA visitors
   - Regional compliance requirements vary

### Planned Improvements

- [ ] Support for additional CMP platforms
- [ ] Multi-language button detection
- [ ] Geographic simulation (EU/CA testing)
- [ ] Multi-page journey testing
- [ ] Cookie persistence testing
- [ ] Banner A/B testing detection

## Troubleshooting

### Banner Not Detected

**Problem:** Test shows "No consent banner detected" but banner exists

**Solutions:**
1. Increase timeout: `pixel-detector scan site.com --test-consent --timeout 60000`
2. Banner may only show to certain regions (EU/CA)
3. Banner may only show on first visit (clear cookies)
4. Platform may not be in supported list

### Button Click Failed

**Problem:** Banner detected but button click failed

**Solutions:**
1. Platform may have updated their button classes
2. Banner may be loading dynamically (timing issue)
3. Custom CMP implementation not in our selectors
4. Check browser console for JavaScript errors

### Inconsistent Results

**Problem:** Different results on repeated scans

**Solutions:**
1. Consent state may persist across scans
2. A/B testing may show different banners
3. Network timing may affect loading order
4. Use fresh browser contexts for each test

## API Reference

### CLI Usage

```bash
# Basic consent testing
pixel-detector scan domain.com --test-consent

# With increased timeout
pixel-detector scan slow-site.com --test-consent --timeout 60000

# Save results
pixel-detector scan site.com --test-consent -o results.json --pretty
```

### Python API

```python
from pixel_detector import PixelScanner

# Create scanner with consent testing
scanner = PixelScanner(test_consent=True)

# Scan domain
result = await scanner.scan_domain("healthcare-site.com")

# Access results
if result.consent_compliance_summary:
    summary = result.consent_compliance_summary
    print(f"Overall Score: {summary.overall_score}/100")
    print(f"Status: {summary.overall_status.value}")
    print(f"Platform: {summary.banner_platform}")
    
    for violation in summary.violations_found:
        print(f"  ❌ {violation}")
    
    print(f"\nRecommendation: {summary.recommended_action}")

# Access individual test results
if result.consent_test_results:
    for test in result.consent_test_results:
        print(f"\n{test.test_type.value.upper()} TEST:")
        print(f"  Score: {test.compliance_score}/100")
        print(f"  Status: {test.compliance_status.value}")
        
        for violation in test.violations_detected:
            print(f"  ❌ {violation}")
```

## Best Practices

### For Cyber Insurers

1. **Risk Assessment**
   - Scores < 70 indicate significant compliance risk
   - Dark patterns (baseline violations) are highest risk
   - Missing banners on sites with tracking = critical

2. **Portfolio Analysis**
   - Run consent testing on all insured healthcare providers
   - Track score trends over time
   - Prioritize remediation for scores < 50

3. **Underwriting**
   - Include consent compliance score in risk assessment
   - Higher premiums for sites with critical violations
   - Require remediation plans for scores < 70

### For Healthcare Providers

1. **Compliance Verification**
   - Test consent platform after any website updates
   - Verify no pre-consent tracking (baseline test)
   - Confirm reject functionality works (critical for GDPR/CCPA)

2. **Remediation Priority**
   - Fix dark patterns immediately (pre-consent tracking)
   - Ensure reject buttons actually block tracking
   - Consider removing tracking entirely if compliance is challenging

3. **Documentation**
   - Save test results as compliance evidence
   - Include timeline data in privacy assessments
   - Use results in vendor management processes

## References

- [GDPR Article 7: Conditions for consent](https://gdpr-info.eu/art-7-gdpr/)
- [CCPA: Right to Opt-Out](https://oag.ca.gov/privacy/ccpa)
- [OCR HIPAA Tracking Technology Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/hipaa-online-tracking/index.html)
- [Dark Patterns in Cookie Consent (EDPB)](https://edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052021-deceptive-design-patterns-social-media_en)

---

**Version:** 2.3.0
**Last Updated:** November 2025
**Status:** Production Ready

