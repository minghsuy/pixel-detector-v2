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
