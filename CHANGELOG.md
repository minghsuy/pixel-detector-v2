# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2025-11-07

### Added
- **Consent Banner Interaction Testing (Phase 2)**: Automated testing to verify consent platforms actually work
  - **Baseline Test**: Detects dark patterns where tracking fires before user consent
  - **Reject All Test**: Verifies that clicking "Reject All" actually blocks tracking (GDPR/CCPA compliance)
  - **Accept All Test**: Validates that tracking works correctly after consent given
  - Timeline tracking with sub-second precision to detect exactly when trackers fire
  - Comprehensive compliance scoring (0-100) with actionable recommendations
- **Button Selector Module**: Smart detection of consent buttons across 6 major platforms
  - OneTrust: 8 button selectors with retry logic
  - Cookiebot: 6 button selectors with fallback patterns
  - Osano: 6 button selectors for modern implementations
  - TrustArc: 8 selectors including legacy and modern patterns
  - Usercentrics: 7 selectors with European variations
  - Termly: 6 selectors for SMB-focused implementations
  - Intelligent banner detection with platform-specific container selectors
  - Multi-retry clicking with scroll-into-view and force-click fallbacks
- **Compliance Checker**: Sophisticated violation detection and scoring
  - Detects pre-consent tracking (critical violation)
  - Identifies post-rejection tracking (GDPR/CCPA violation)
  - Generates actionable recommendations based on violation patterns
  - Risk severity classification (CRITICAL, HIGH, MEDIUM, LOW, NONE)
  - Platform-specific remediation guidance
- **Enhanced Data Models**: New Pydantic models for consent testing
  - `ConsentTestResult`: Complete test results with evidence and scores
  - `ConsentTestEvidence`: Detailed evidence collection (pixels, cookies, requests, timeline)
  - `ConsentComplianceSummary`: Overall compliance assessment across all tests
  - `TimelineEvent`: Sub-second event tracking for dark pattern detection
  - Enums: `ConsentAction`, `ConsentCompliance`, `ViolationSeverity`
- **CLI Integration**: New `--test-consent` flag for consent testing
  - Rich console output with color-coded compliance scores
  - Emoji indicators for test results (✅/🔴/🟡)
  - Detailed violation reporting with recommendations
  - Overall compliance score and recommended action (APPROVE/REVIEW/DECLINE)

### Changed
- **ScanResult Model**: Extended to include optional consent test results
  - Added `consent_test_results` field for all 3 test results
  - Added `consent_compliance_summary` field for overall assessment
  - Model rebuild required for forward reference resolution
- **Scanner Architecture**: Integrated consent testing into main scan workflow
  - Creates fresh browser pages for each test to avoid state contamination
  - Resets detectors between tests for accurate tracking detection
  - Runs all 3 tests sequentially (baseline, reject, accept)
  - Graceful error handling - scan completes even if consent tests fail
- **CLI Output**: Enhanced to display rich consent testing results
  - Color-coded compliance scores (green ≥90, yellow ≥70, red <70)
  - Platform detection displayed prominently
  - Violations listed with specific details
  - Recommendations highlighted for quick action

### Fixed
- **Pydantic Forward References**: Proper import ordering to resolve circular dependencies
  - Import `pixel_detection` models first, then `consent_test` models
  - Call `ScanResult.model_rebuild()` after all imports
  - Use `Optional["Type"]` instead of `"Type" | None` for forward references

### Technical Details
- **3-Phase Testing Approach**:
  1. **Baseline (No Interaction)**: Loads page, waits 5s, detects any tracking before consent
  2. **Reject All**: Finds and clicks reject button, verifies tracking stops
  3. **Accept All**: Clicks accept button, validates tracking works (confirms detection accuracy)
- **Evidence Collection**: Captures pixel types, cookies, network requests, and timeline events
- **Compliance Scoring Algorithm**:
  - Baseline: 0 if tracking before consent, 100 if clean
  - Reject: 0 if banner missing, 0 if tracking continues, 100 if properly blocks
  - Accept: Always 100 (validates our detection works)
  - Overall: Average of all test scores
- **Real-World Validation**: Tested on goodsamsanjose.com and elcaminohealth.org
  - Successfully detected Cookiebot dark pattern (Google Analytics before consent)
  - Validated TrustArc detection (no pre-consent tracking)

### Documentation
- Enhanced CLI help with consent testing examples
- Rich console output for compliance reporting
- Timeline events provide audit trail for compliance verification

## [2.2.0] - 2025-11-07

### Added
- **Consent Management Platform Detection**: Added 6 new detectors for privacy compliance tools
  - OneTrust (40% market share) - Industry-leading consent platform
  - Cookiebot (15% market share) - GDPR/CCPA compliance tool
  - Osano (8% market share) - Privacy platform with consent management
  - TrustArc (7% market share) - Enterprise privacy management
  - Usercentrics (5% market share) - European consent management
  - Termly (3% market share) - SMB-focused compliance solution
- **Compliance Gap Analysis**: Identify sites with tracking pixels but no consent management
  - Consent platforms classified as `RiskLevel.LOW`
  - `hipaa_concern = False` for all consent management platforms
  - Detection helps assess GDPR/CCPA compliance posture
- **Enhanced PixelType Enum**: Added 6 new consent platform types to detection model
- **Comprehensive Testing**: 100+ new test cases for consent platform detection
  - Property validation tests for all 6 platforms
  - Network request detection tests
  - Pixel ID extraction tests
  - Global variable and DOM element detection tests
  - Registry integration tests

### Changed
- **Detection Scope**: Expanded from 8 to 14 total detector types
- **Documentation**: Updated README with consent platform detection table
- **Risk Classification**: Consent platforms distinguished from tracking pixels

## [2.1.0] - 2025-08-08

### Added
- **AWS Fargate / S3 Support**: New batch processing capabilities for cloud deployment
  - Read input CSV files directly from S3 buckets
  - Write results back to S3 buckets
  - Support for AWS Fargate task execution
  - New `run_batch.py` module for S3 integration
- **Production Dockerfile**: Specialized `Dockerfile.production` for Fargate deployment
  - Optimized for batch processing workloads
  - Configured with S3 support via boto3
  - Health check endpoint for container orchestration
- **Enhanced Documentation**: Comprehensive AWS deployment guide
  - Fargate task definition examples
  - IAM permission requirements
  - ECR push instructions

### Fixed
- **Security Improvements**: Replaced hardcoded `/tmp` paths with `tempfile.mkdtemp()`
- **Type Safety**: Added complete type annotations to batch processing modules
- **CI/CD**: Fixed all linting and type checking errors

## [2.0.0] - 2025-08-07

### Fixed (2025-08-07 Update)
- **Critical Bug Fix**: Production scanner was not detecting pixels correctly
  - Removed broken `production_scanner.py` that had false negatives
  - Now using the working CLI scanner that correctly detects all pixel types
- **CLI Enhancement**: Added CSV batch support to existing CLI
  - `pixel-detector batch` now accepts CSV files with custom_id,url columns
  - Output includes timestamps and duration for each scan
  - Pipe-separated pixel names for easy parsing
- **Docker Simplification**
  - Removed unnecessary wrapper scripts (docker_wrapper.py)
  - Docker now uses the working CLI tool directly
  - Fixed all Docker commands in documentation
- **Documentation Cleanup**
  - Updated all .md files to reflect simplified architecture
  - Fixed Docker commands to use correct CLI syntax
  - Added corporate proxy handling instructions
  - Removed references to broken production_scanner.py

### Removed (2025-08-07 Update)
- `production_scanner.py` - Broken pixel detection (false negatives)
- `docker_wrapper.py` - Unnecessary wrapper
- `url_handler.py` - Redundant URL handling
- `Dockerfile.corporate` - Consolidated into single Dockerfile

### Added
- **Unified Production Scanner** (`production_scanner.py`)
  - Consolidated all scanner variants into single production-ready file
  - Smart URL variations (automatically tries www/non-www, http/https)
  - Two workflow modes:
    - Portfolio mode: CSV with custom_id for data integration
    - On-demand mode: Simple TXT domain list
  - Checkpoint/resume capability for interrupted scans
  - Proper input validation (rejects emails, phones, "none")
  - Memory-efficient streaming saves
- **Production Docker Support**
  - Simplified `Dockerfile` for production use
  - `docker-compose.batch.yml` for batch processing
  - `DOCKER_DEPLOYMENT.md` comprehensive deployment guide
  - Rancher/Kubernetes deployment examples
- **URL Handler** (`url_handler.py`)
  - RFC-compliant domain validation
  - International domain (IDN) support with punycode
  - TLD validation using public suffix list
  - Handles IP addresses and ports

### Changed
- **Major Refactor**: Consolidated multiple scanner files into one
  - Removed: ultra_reliable_scanner.py, strict_scanner.py, smart_url_scanner.py
  - Removed: unified_pipeline.py, pipeline_processor.py
  - Single source of truth: production_scanner.py
- **Timeout Improvements**
  - Default 30s timeout (was variable)
  - Maximum 60s timeout (prevents 15+ minute hangs)
  - Configurable per deployment
- **Better Error Handling**
  - Specific rejection messages for invalid input
  - Clear distinction between validation and scan failures
  - Detailed error logging

### Removed
- **Lambda Deployment** (completely removed)
  - Deleted all Lambda-related files and documentation
  - Focus on Docker/Rancher deployment only
  - Removed lambda_handler.py, AWS_LAMBDA_DEPLOYMENT_GUIDE.md
  - Removed test_lambda_handler.py
- **Redundant Docker Files**
  - Removed Dockerfile.api, Dockerfile.safe, Dockerfile.secure
  - Removed Dockerfile.lambda, Dockerfile.test, Dockerfile.ultra
  - Single production Dockerfile

### Fixed
- **URL Redirect Handling**: Now properly handles domains that redirect
  - Example: badensports.com → www.badensports.com
  - Tries multiple variations before giving up
- **Memory Issues**: Results now stream to disk immediately
- **Timeout Issues**: Hard limits prevent infinite hangs
- **Input Validation**: Properly rejects invalid data before scanning
- **Docker Compatibility**: Fixed module imports for container environment
- **GitHub Actions**: Fixed CI/CD pipeline for new structure

### Documentation
- Added `DOCKER_DEPLOYMENT.md` - Main deployment guide for Docker/Rancher
- Updated `README.md` with new scanner usage
- Updated `.gitignore` to exclude test files and redundant code
- Removed all Lambda-related documentation

### Breaking Changes
- Command-line interface changed for production_scanner.py
- Lambda deployment no longer supported
- Must use new production_scanner.py instead of individual scanner files
- CSV format requires exactly `custom_id` and `url` columns

## [0.3.0] - 2025-08-06

### Added
- **Comprehensive Docker Support** for production deployments
  - `Dockerfile.safe` - Production-ready container with non-root user
  - `Dockerfile.secure` - Hardened container with AppArmor/Firejail
  - `Dockerfile.api` - REST API wrapper for service deployments
  - Docker Compose configuration for full stack deployment
- **AWS Fargate Deployment Guide** - Recommended for large-scale scanning
  - No time limits (unlike Lambda's 15-minute constraint)
  - Better resource allocation for Playwright
  - Handles portfolio analysis at scale
- **Batch Processing Enhancements**
  - `batch_manager.py` - Checkpoint and resume capability
  - `batch_processor.py` - Concurrent domain processing
  - Health checks before scanning to avoid wasted attempts
- **Local Development Improvements**
  - `__main__.py` - Made module directly executable
  - `api.py` - FastAPI wrapper for REST endpoints
  - VSCode Docker integration guide
  - M3 Pro optimized settings

### Changed
- **Pivoted from Lambda to Fargate** due to GLIBC incompatibility
  - Lambda + Playwright faces fundamental compatibility issues
  - Fargate provides better long-running batch job support
  - More cost-effective for portfolio analysis
- **Improved Docker configurations**
  - Fixed Poetry `--no-root` issues across all Dockerfiles
  - Added proper PYTHONPATH configuration
  - Created working docker-compose setup

### Fixed
- Docker build failures due to missing `--no-root` flag
- Module execution issues (missing `__main__.py`)
- docker-compose expecting API server that didn't exist
- Lambda GLIBC version incompatibility with Playwright

### Documentation
- Added `DOCKER_SAFE_SCANNING.md` for production batch scanning
- Added `FARGATE_DEPLOYMENT.md` for AWS deployment
- Added `LOCAL_DOCKER_VSCODE_GUIDE.md` for local development
- Added `DOCKER_FIXES_APPLIED.md` documenting all corrections
- Updated examples for portfolio analysis use cases

## [0.2.1] - 2025-08-02

### Added
- Comprehensive cyber insurance adoption documentation
  - CYBER_INSURANCE_ADOPTION.md with ROI models and implementation roadmap
  - QUICK_START_INSURERS.md for 5-minute proof of value
  - WHY_THIS_MATTERS.md with $66M in fines context
- Insurance-specific examples
  - Risk scoring system (examples/insurance/risk_scoring.py)
  - Enterprise API wrapper (examples/insurance/enterprise_api.py)
- Docker Compose configuration for one-command deployment
- GitHub Actions CI/CD pipeline with coverage reporting
- Insurance workflow concept tests

### Changed
- Streamlined README to focus on quick start and core value
- Improved documentation structure for dual audiences (healthcare + insurers)
- Enhanced .gitignore for cleaner repository

### Fixed
- Repository URLs throughout documentation
- CI/CD pipeline issues with proper test configuration
- Import errors in test files

### Documentation
- Added comprehensive lessons learned in CLAUDE.md
- Created focused documentation for cyber insurance market
- Removed placeholder content and unrealistic promises

## [0.2.0] - 2025-07-30

### Added
- **Enhanced URL Handling**: Smart URL normalization that handles various input formats
  - Automatically adds `https://` protocol if missing
  - Handles domains with paths, ports, and subdomains
  - Cleans copy-paste artifacts (quotes, markdown syntax, HTML tags)
  - Case-insensitive domain handling
- **Intelligent Domain Resolution**: Finds the most accessible version of a domain
  - Tries multiple variations (www/non-www, http/https)
  - Follows redirects automatically
  - Provides helpful suggestions when domains fail
- **URL Validation**: Validates domain format before attempting connection
  - Supports standard domains, subdomains, IP addresses, and localhost
  - Better error messages with alternative suggestions
- New dependency: `tldextract` for robust domain extraction

### Changed
- Improved `scan_domain` method to use the new URL normalizer
- Enhanced error handling with more descriptive messages
- Updated DNS pre-check to work with normalized URLs

### Fixed
- Better handling of edge cases in domain inputs
- More robust error recovery for unreachable domains

## [0.1.0] - 2025-07-20

### Added
- Core pixel detection functionality for 8 major tracking platforms
  - Meta Pixel (Facebook)
  - Google Analytics
  - Google Ads
  - TikTok Pixel
  - LinkedIn Insight Tag
  - Twitter Pixel
  - Pinterest Tag
  - Snapchat Pixel
- Multiple detection methods: network requests, DOM analysis, JavaScript globals, cookies
- Stealth mode with playwright-stealth to avoid bot detection
- Concurrent batch scanning with configurable parallelism
- Retry logic with exponential backoff
- Health checks to skip unreachable domains
- CLI interface with single and batch scanning modes
- JSON and table output formats
- Screenshot capture capability
- 91% test coverage
- Comprehensive logging with Python logging module
- Example scan results for NY healthcare systems
- Production readiness checklist and documentation

### Performance
- 5x speed improvement with concurrent scanning
- Smart DNS pre-checks to avoid wasting time on dead domains
- Configurable timeouts and retry strategies

### Documentation
- Comprehensive README with real-world examples
- Architecture documentation
- Contributing guidelines
- Executive summary for business stakeholders