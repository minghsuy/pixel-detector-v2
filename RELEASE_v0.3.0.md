# Release Process for v0.3.0

## Summary of Changes
v0.3.0 pivots from Lambda to Docker/Fargate due to GLIBC compatibility issues discovered during testing.

### Key Additions
- ✅ Docker containerization (safe, secure, API variants)
- ✅ AWS Fargate deployment guide
- ✅ Batch processing enhancements
- ✅ Local VSCode Docker development guide
- ❌ Lambda support (failed due to Playwright incompatibility)

## Git Workflow Options

### Option 1: Direct to Main (Your Current Approach)
Since you have direct commits to main in history:

```bash
# 1. Stage all changes
git add -A

# 2. Commit with detailed message
git commit -m "Release v0.3.0: Docker containerization and Fargate support

- Add comprehensive Docker support with multiple Dockerfile variants
- Add AWS Fargate deployment guide (replaces Lambda approach)
- Add batch processing with checkpoint/resume capability
- Fix docker-compose and add API wrapper
- Update documentation to reflect Lambda limitations
- Add local development guides for VSCode

BREAKING CHANGE: Lambda deployment not recommended due to GLIBC issues"

# 3. Create and push tag
git tag -a v0.3.0 -m "Release v0.3.0: Docker and Fargate support"
git push origin main --tags
```

### Option 2: Create a PR (More Formal)
If you want to review changes:

```bash
# 1. Create release branch
git checkout -b release/v0.3.0

# 2. Stage and commit
git add -A
git commit -m "Release v0.3.0: Docker containerization and Fargate support"

# 3. Push branch
git push origin release/v0.3.0

# 4. Create PR on GitHub
# Then merge and tag after review
```

## Files to Include in Release

### New Files (17 files)
```bash
# Documentation
DOCKER_FIXES_APPLIED.md
DOCKER_SAFE_SCANNING.md
FARGATE_DEPLOYMENT.md
LOCAL_DOCKER_VSCODE_GUIDE.md

# Docker configurations
Dockerfile.api
Dockerfile.lambda  # Keep for reference even though it doesn't work
Dockerfile.safe
Dockerfile.secure

# Code additions
src/pixel_detector/__main__.py
src/pixel_detector/api.py
src/pixel_detector/batch_manager.py
src/pixel_detector/batch_processor.py
scripts/get_top_healthcare_sites.py

# Lambda attempts (for reference)
lambda_handler.py
deploy_lambda_v03.sh
tests/test_lambda_handler.py
```

### Modified Files (8 files)
```bash
CHANGELOG.md         # Updated with v0.3.0 release notes
README.md           # Updated to mention Docker/Fargate instead of Lambda
Dockerfile          # Added --no-root fix
docker-compose.yml  # Updated to use API dockerfile
pyproject.toml      # Version already at 0.3.0
src/pixel_detector/__init__.py  # Version updated
# Plus any test files that were updated
```

## Post-Release Steps

1. **Create GitHub Release**
   - Go to https://github.com/minghsuy/pixel-detector-v2/releases
   - Click "Create a new release"
   - Select tag v0.3.0
   - Title: "v0.3.0: Docker Containerization & Fargate Support"
   - Copy key points from CHANGELOG.md

2. **Update Docker Hub** (if applicable)
   ```bash
   docker tag pixel-scanner:safe yourdockerhub/pixel-detector:v0.3.0
   docker push yourdockerhub/pixel-detector:v0.3.0
   docker push yourdockerhub/pixel-detector:latest
   ```

3. **Clean Up Old Files**
   Consider removing Lambda-related files in v0.4.0 since they don't work:
   - LAMBDA_QUICK_START.md
   - V03_RELEASE_CHECKLIST.md
   - v03-production-checklist.md

## Testing Checklist Before Release

- [ ] Docker build works: `docker build -f Dockerfile.safe -t test .`
- [ ] Quick scan works: `docker run test batch healthcare_quick_test.txt`
- [ ] All tests pass: `poetry run pytest`
- [ ] No linting errors: `poetry run ruff check src/`

## Notes
- Lambda deployment was attempted but failed due to GLIBC version mismatch
- Fargate is the recommended approach for AWS deployment
- All Docker fixes have been tested and verified working