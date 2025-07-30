# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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