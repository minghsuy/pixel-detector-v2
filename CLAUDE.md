# Healthcare Pixel Tracking Detection System

## Project Status (July 2025)
✅ **Phase 1 & 2 COMPLETE** - Core functionality implemented and tested
- Phase 1: Core Detection Script ✓
- Phase 2: Enhanced Detection ✓
- Testing: **91% code coverage achieved!** ✓
- Phase 3: AWS Deployment (Needs production hardening - see PRODUCTION_READINESS_CHECKLIST.md)
- Real-world validation: Successfully analyzed 10 healthcare providers

### Production Readiness Note
While the tool is fully functional for local use and demos, it needs ~1 week of hardening for production Lambda deployment. See [PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md) for full details.

## Project Overview
A system to detect pixel tracking usage on healthcare websites to identify potential HIPAA compliance violations and PII/PHI data leakage to advertising platforms.

## Quick Start
```bash
# Install and run
poetry install
poetry run playwright install chromium
pixel-detector scan healthcare-site.com

# Run the healthcare demo
pixel-detector batch santa_clara_healthcare.txt -o results/
```

## Project Setup
- **Python Version**: 3.11.13
- **Package Manager**: Poetry 2.1.3
- **Main Framework**: Playwright 1.53.0
- **Stealth Package**: playwright-stealth 1.0.6

## Major Pixel Trackers to Detect
All 8 pixel detectors are fully implemented with:
- Network request monitoring
- DOM element detection
- JavaScript global variable checking
- Cookie detection
- Pixel ID extraction capabilities

1. **Meta Pixel (Facebook Pixel)** - Most problematic for healthcare ✓
2. **Google Analytics & Google Ads Pixel** ✓
3. **TikTok Pixel** ✓
4. **LinkedIn Insight Tag** ✓
5. **Twitter/Pinterest/Snapchat Pixels** ✓

### Healthcare Compliance Concerns
- 33% of healthcare websites still use Meta pixel tracking despite HIPAA risks
- OCR clarified in December 2022 that HIPAA applies to tracking technologies
- No major ad platforms sign BAAs (Business Associate Agreements)
- Even consent banners don't constitute valid HIPAA authorization

## Technical Architecture

### Detection Methods
1. **Network Request Monitoring** - Intercept HTTP/HTTPS requests for tracking domains
2. **DOM Analysis** - Search for tracking script tags and pixel elements
3. **JavaScript Execution Monitoring** - Detect tracking libraries and global variables

### Implementation Phases
- **Phase 1**: Core Detection Script ✓
- **Phase 2**: Enhanced Detection ✓
- **Phase 2.5**: Performance & Reliability (5x speed improvement) ✓
- **Phase 3**: AWS Deployment (Container-based approach recommended)

## Output Format
```json
{
  "domain": "example-healthcare.com",
  "timestamp": "2025-01-19T10:30:00Z",
  "pixels_detected": [
    {
      "type": "meta_pixel",
      "evidence": {
        "network_requests": ["https://www.facebook.com/tr?id=..."],
        "script_tags": ["<script>fbq('init', '123456789');</script>"],
        "cookies_set": ["_fbp", "_fbc"]
      },
      "risk_level": "high",
      "hipaa_concern": true
    }
  ]
}
```

## Development Guidelines & Best Practices

### Code Quality Standards
To ensure all CI checks pass, follow these guidelines:

#### 1. Type Annotations (Python 3.11+)
- Use modern type hints: `list[str]` instead of `List[str]`
- Always add return type annotations (use `-> None` for void functions)
- For untyped libraries, add `# type: ignore` comment

#### 2. Pydantic Models (v2.x)
- Use `ConfigDict()` instead of class-based `Config`
- Use `model_dump()` instead of deprecated `dict()` method
- For datetime serialization, use `@field_serializer` decorator

#### 3. Abstract Base Classes
- When defining abstract methods, use `@abstractmethod` decorator
- All concrete implementations must implement abstract methods

#### 4. Ruff Configuration
```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "S", "B", "A", "C4", "PT", "Q"]
ignore = ["S101", "B008", "UP007"]  # S101: assert in tests, B008: typer defaults, UP007: typer needs Optional[T]
```

#### 5. Running CI Checks Locally
```bash
# Run all checks together
poetry run pytest tests/ && poetry run ruff check src/ && poetry run mypy src/
```

## Critical Lessons Learned

### 🚨 MANDATORY: Always Check Implementation First!

**BEFORE writing ANY test, you MUST:**
1. Read the actual implementation file completely
2. List all available methods: `grep "def " src/pixel_detector/scanner.py`
3. Verify method signatures and parameters
4. Only then start writing tests

**The Scanner Reality Check:**
- Public methods: `scan_domain()`, `scan_multiple()`
- Private methods that exist: `_launch_browser()`, `_create_context()`
- Everything else: DOES NOT EXIST

**Achievement**: Increased test coverage from 10% to 91% by focusing on actual implementation!

### Major Implementation Challenges & Solutions

#### 1. Base Class Pattern
**Problem**: Initially implemented detectors with direct attribute assignment
**Solution**: Base class uses `@property` decorators with abstract methods:
```python
@property
def pixel_type(self) -> PixelType:
    return PixelType.META_PIXEL
```

#### 2. Type Annotation Issues
**Key learnings**:
- Typer requires `Optional[Type]` not `Type | None`
- Python 3.11+ prefers `list[str]` over `List[str]`
- Mypy strict mode requires ALL functions to have return type annotations
- Override methods must match base class signatures exactly

#### 3. Evidence Collection Pattern
**Wrong**: `self.evidence.network_requests.append(url)`
**Correct**: `self.network_requests.append(url)`

### Testing Best Practices Discovered

1. **Use Isolated Test Runners**: For CLI tests, use `runner.isolated_filesystem()`
2. **Mock at the Right Level**: Mock internal methods, not public ones
3. **Async Test Patterns**: Always use `pytest.mark.asyncio` and AsyncMock
4. **Coverage Strategy**: Start with models → detectors → CLI → scanner

### CI/CD Debugging Lessons

#### 🚨 Always Check Actual Error Logs!
**Mistake**: Assumed GitHub Actions failure was due to Python 3.12 compatibility
**Reality**: It was linting errors in newly created files

**The Right Way**:
```bash
# List recent runs
gh run list --limit 5

# Get the actual error logs
gh run view [RUN_ID] --log-failed

# Or for the latest failed run
gh run list --limit 1 --status failure --json databaseId -q '.[0].databaseId' | xargs gh run view --log-failed
```

**What Actually Happened**:
- Created new files (`api.py`, `batch_manager.py`, `batch_processor.py`) during Docker work
- These had 31 linting errors (unused imports, quote style, line length)
- GitHub Actions runs `ruff check` and `mypy` which caught all issues
- Misdiagnosed as Python version issue without checking logs

**Common CI Linting Issues to Watch For**:
1. **Import errors**: Unused imports, unsorted imports
2. **Quote consistency**: Ruff prefers double quotes
3. **Line length**: Max 120 characters
4. **Exception handling**: Use `raise ... from e` for exception chaining
5. **Security**: Don't bind to `0.0.0.0`, use `127.0.0.1` instead
6. **Type annotations**: Every function needs return type (use `-> None` for void)
7. **Untyped libraries**: Add `# type: ignore` for fastapi, uvicorn, etc.

**Quick Fix Commands**:
```bash
# Auto-fix most linting issues
poetry run ruff check src/ --fix

# Check what can't be auto-fixed
poetry run ruff check src/

# Check type errors
poetry run mypy src/

# Run all CI checks locally before pushing
poetry run pytest && poetry run ruff check src/ && poetry run mypy src/
```

## Pixel Detection Patterns Reference

### Meta Pixel (Facebook)
- **Domains**: `connect.facebook.net`, `facebook.com/tr`
- **Global Variables**: `fbq`, `_fbq`
- **Cookies**: `_fbp`, `_fbc`, `datr`, `fr`

### Google Analytics
- **Domains**: `google-analytics.com`, `googletagmanager.com`
- **Global Variables**: `ga`, `gtag`, `dataLayer`
- **Cookies**: `_ga`, `_gid`, `_gat`

### Google Ads
- **Domains**: `googleadservices.com`, `googlesyndication.com`
- **Global Variables**: `google_tag_params`, `google_conversion_id`
- **Cookies**: `_gcl_aw`, `_gcl_dc`

### Other Pixels
- **TikTok**: `analytics.tiktok.com`, variable: `ttq`
- **LinkedIn**: `px.ads.linkedin.com`, variable: `_linkedin_partner_id`
- **Twitter**: `analytics.twitter.com`, variable: `twq`
- **Pinterest**: `ct.pinterest.com`, variable: `pintrk`
- **Snapchat**: `sc-static.net`, variable: `snaptr`

## Real-World Healthcare Tracking Insights

### Santa Clara County Healthcare Analysis
Based on scanning 10 major healthcare providers:
- **Google Analytics**: 50% of sites
- **Google Ads**: 10% of sites (health insurance!)
- **Meta Pixel**: 0% (excellent)
- **No Tracking**: 40% of sites

#### Key Findings
1. County-run facilities lead in privacy protection
2. Major systems (Stanford, Kaiser) still use Google Analytics
3. Insurance sites at highest risk for member privacy
4. Healthcare providers avoid social media pixels but don't recognize Google's risks

## Enterprise Adoption Strategy

### Documentation Architecture
- `README.md`: Concise, developer-focused
- `WHY_THIS_MATTERS.md`: Business impact with $66M in fines data
- `CYBER_INSURANCE_ADOPTION.md`: Insurance-specific value proposition

### Open Source as Market Strategy
- Core detection = open source (builds adoption)
- Risk models = proprietary (monetizable)
- Services = revenue (SaaS, consulting, support)

### One-Command Deployment
```yaml
# docker-compose.yml includes:
- Main app + API
- Redis caching
- PostgreSQL storage
- Grafana dashboards
```

## CI/CD Best Practices

### Start Simple
```yaml
# Basic CI that works
- run: poetry run pytest
- run: poetry run ruff check
- run: poetry run mypy

# Add features incrementally after testing locally
```

### Common CI Mistakes to Avoid
1. Don't add complex features without testing locally first
2. Never use "continue-on-error" to hide failures
3. Check package manager compatibility (Poetry vs pip)
4. Verify imports work in isolated environment
5. Tests shouldn't depend on external services

## Development Patterns & Best Practices

### URL/Domain Handling
Always handle these cases:
- Missing protocols (`example.com` → `https://example.com`)
- www vs non-www variations
- Subdomains and complex paths
- Port numbers, IP addresses, localhost
- Copy-paste artifacts (quotes, markdown, HTML)

### Creating New Features
1. Start with clear requirements
2. Create focused modules (one responsibility)
3. Use type hints consistently
4. Handle errors gracefully
5. Add logging for debugging
6. Consider async from the start

### Key Takeaways
- **5 seconds of checking > 2 hours of fixing bad assumptions**
- **Business First, Tech Second**: Lead with value ($66M in fines), not features
- **Remove ALL Friction**: One-command deployment, 5-minute demos
- **Test Like Production**: Real-world sites, performance benchmarks

## Common Pitfalls Summary
1. Don't assume implementation patterns - always verify first
2. Don't skip type annotations - mypy strict requires 100%
3. Don't mix Pydantic v1 and v2 patterns
4. Don't forget to test with real websites
5. Don't enhance working CI without understanding constraints

**Remember**: Read first, implement second. This principle saved hours of debugging and helped achieve 91% test coverage!