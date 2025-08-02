# Contributing to Pixel Detector

Thank you for your interest in contributing to Pixel Detector! This tool helps protect patient privacy by detecting tracking pixels on healthcare websites.

## 🤝 Code of Conduct

By participating in this project, you agree to:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Poetry package manager
- Git

### Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/pixel-detector.git
cd pixel-detector

# 2. Install dependencies
poetry install

# 3. Install Playwright browsers
poetry run playwright install chromium

# 4. Install development dependencies
poetry install --with dev

# 5. Run tests to ensure everything works
poetry run pytest
```

## 📝 How to Contribute

### 1. Find an Issue
- Check our [issue tracker](https://github.com/minghsuy/pixel-detector-v2/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to let others know you're working on it

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Your Changes
- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Code Standards

#### Python Style
- We use Black for formatting (line length: 120)
- We use Ruff for linting
- We use mypy for type checking (strict mode)

Run these before committing:
```bash
# Format code
poetry run black src/ tests/

# Check linting
poetry run ruff check src/

# Check types
poetry run mypy src/
```

#### Type Annotations
- Use modern Python 3.11+ type hints
- Prefer `list[str]` over `List[str]`
- Add return type annotations to all functions
- Use `-> None` for functions without return values

#### Testing
- Write tests for all new functionality
- Maintain our 90%+ test coverage
- Use pytest for all tests
- Use AsyncMock for async code

### 5. Commit Your Changes
```bash
# Use conventional commit messages
git commit -m "feat: add new pixel detector for XYZ platform"
git commit -m "fix: correct detection pattern for Meta pixel"
git commit -m "docs: update README with new examples"
git commit -m "test: add tests for DNS pre-check"
```

### 6. Push and Create a Pull Request
```bash
git push origin your-branch-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what and why
- Reference to any related issues
- Screenshots if UI changes

## 🎯 Areas for Contribution

### High Priority
- **New Pixel Detectors**: Add detection for new tracking platforms
- **Performance**: Optimize scanning speed and resource usage
- **Documentation**: Improve guides and examples
- **Testing**: Increase coverage, add edge cases

### Feature Ideas
- Web dashboard UI
- API development
- Database integration
- Real-time monitoring
- Compliance report generation

### Bug Fixes
- Check [open issues](https://github.com/minghsuy/pixel-detector-v2/issues)
- Improve error handling
- Fix edge cases

## 🧪 Testing

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Tests
```bash
# Run a specific test file
poetry run pytest tests/test_scanner.py

# Run with coverage
poetry run pytest --cov=src/pixel_detector --cov-report=html

# Run with verbose output
poetry run pytest -v -s
```

### Writing Tests
- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Test both success and failure cases

Example test:
```python
import pytest
from pixel_detector.models import PixelType, Detection

def test_detection_creation():
    detection = Detection(
        pixel_type=PixelType.META_PIXEL,
        pixel_id="123456789",
        risk_level="critical"
    )
    assert detection.pixel_type == PixelType.META_PIXEL
    assert detection.hipaa_concern is True
```

## 📚 Documentation

### Where to Document
- **Code**: Use docstrings for all public functions
- **README**: Update for new features or changes
- **CLAUDE.md**: Add technical implementation details
- **Docs folder**: Add guides for complex features

### Documentation Style
```python
async def scan_domain(self, domain: str) -> ScanResult:
    """Scan a domain for tracking pixels.
    
    Args:
        domain: The domain to scan (with or without protocol)
        
    Returns:
        ScanResult with detected pixels and metadata
        
    Raises:
        TimeoutError: If the scan exceeds the timeout
    """
```

## 🚨 Important Notes

### Security
- Never commit sensitive data
- Don't add actual healthcare site data to tests
- Use example.com for documentation
- Report security issues privately

### HIPAA Compliance
- This tool is for detection only
- Don't store or transmit PHI
- Focus on privacy protection
- Be ethical in usage examples

## 📦 Release Process

Maintainers will:
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a GitHub release
4. Publish to PyPI (future)

## 💬 Getting Help

- **Questions**: Open a [Discussion](https://github.com/minghsuy/pixel-detector-v2/discussions)
- **Bugs**: Open an [Issue](https://github.com/minghsuy/pixel-detector-v2/issues)
- **Security**: Create a private security advisory on GitHub

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Part of making healthcare more private!

Thank you for contributing to patient privacy! 🏥🔒