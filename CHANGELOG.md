# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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