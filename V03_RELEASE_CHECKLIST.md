# v0.3 Release Checklist - Lambda Learning Edition

## Goal
Get Pixel Detector running in AWS Lambda for learning purposes. Not production-ready, just functional.

## Pre-Release Testing (Do These First!)

### 1. Local Lambda Test
```bash
# Test the handler directly
python lambda_handler.py

# Build Docker image
docker build -f Dockerfile.lambda -t pixel-lambda:test .

# Run Lambda runtime locally
docker run -d -p 9000:8080 pixel-lambda:test

# Test with curl
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"domain": "example.com"}'
```

✅ Success = You get JSON response with mock or real data

### 2. AWS Deployment Test

Follow LAMBDA_QUICK_START.md Part 2. Minimum success criteria:
- [ ] Image pushes to ECR successfully
- [ ] Lambda function creates in console
- [ ] Test event works in Lambda console
- [ ] Function completes without timeout
- [ ] CloudWatch logs show your print statements

### 3. Quick Functionality Check

From Lambda console, test these domains:
- `example.com` - Should work quickly
- `mountsinai.org` - Should find Google Analytics
- `nyulangone.org` - Should find no pixels

## Release Steps

### 1. Code Freeze
- [ ] No new features! Just Lambda deployment
- [ ] All tests still pass: `poetry run pytest`
- [ ] No linting errors: `poetry run ruff check src/`

### 2. Update Version
```bash
# In pyproject.toml
version = "0.3.0"
```

### 3. Finalize Changelog
- [ ] Add release date to CHANGELOG.md
- [ ] Move items from "Unreleased" to "[0.3.0] - 2025-08-XX"

### 4. Commit and Tag
```bash
git add -A
git commit -m "Release v0.3.0 - AWS Lambda support for learning"
git tag -a v0.3.0 -m "AWS Lambda deployment (learning edition)"
git push origin main --tags
```

### 5. Create GitHub Release
- Go to GitHub releases
- Create new release from tag v0.3.0
- Title: "v0.3.0 - AWS Lambda Support (Learning Edition)"
- Description:
  ```
  ## 🎓 Learning Release
  
  This release adds basic AWS Lambda support for learning purposes.
  
  ### What's New
  - Run Pixel Detector in AWS Lambda
  - Docker container with Chromium support  
  - Simple deployment process (not production-ready)
  - Costs < $5 for experimentation
  
  ### Quick Start
  See `LAMBDA_QUICK_START.md` for 30-minute deployment guide.
  
  ### Note
  This is for learning AWS Lambda. For production use, wait for v0.4.
  ```

### 6. Update README
Add section about Lambda:
```markdown
## 🌩️ AWS Lambda Support (v0.3+)

Basic Lambda deployment available for learning:
- See [Lambda Quick Start](LAMBDA_QUICK_START.md)
- Costs ~$0.01/day for testing
- Not production-ready yet
```

## Post-Release

### Share Your Learning!
1. Write a blog post about Lambda + Chromium challenges
2. Share cost analysis (how much did learning cost?)
3. Document what didn't work (helps others!)

### Start Planning v0.4
Based on what you learned:
- What was harder than expected?
- What features are actually needed?
- What can stay simple?

## Success Metrics for v0.3

✅ **Shipped = Success**

You succeeded if:
- Lambda function runs (even if slow)
- You learned how Lambda + Docker works
- Total AWS cost < $10
- You can explain Lambda cold starts to someone

You did NOT fail if:
- Some sites timeout
- Cold starts are slow
- You didn't add authentication
- It's not "production ready"

## Common Release Blockers (and Solutions)

**"The Docker image is 2GB!"**
- That's normal with Chromium. Ship it.

**"Cold starts take 30 seconds!"**
- That's normal. Document it and ship.

**"Some sites fail to scan!"**
- That's fine for v0.3. Document which ones.

**"It's not secure!"**
- It's for learning. Add security in v0.4.

## Final Reminder

This is v0.3, not v1.0. The goal is to LEARN Lambda, not build perfect infrastructure.

If it runs in Lambda and you learned something, you succeeded! 🎉
