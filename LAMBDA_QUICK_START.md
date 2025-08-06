# Lambda Quick Start - For Learning, Not Production!

## Goal
Learn how to run Pixel Detector in AWS Lambda. This is NOT production-ready, it's for LEARNING.

## Prerequisites
- AWS account (personal is fine)
- Docker Desktop installed
- AWS CLI (`brew install awscli`)
- About $5 in AWS credits for experiments

## Part 1: Test Locally (10 minutes)

```bash
# 1. Test the Lambda handler works
python lambda_handler.py

# 2. Build the Docker image
docker build -f Dockerfile.lambda -t pixel-lambda:test .

# 3. Run Lambda locally
docker run -p 9000:8080 pixel-lambda:test

# 4. In another terminal, test it
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"domain": "example.com"}'
```

If this works, you're ready for AWS!

## Part 2: Deploy to Real Lambda (30 minutes)

### Option A: Use AWS Console (Easier for Learning!)

1. **Build and push your image:**
```bash
# Get your account ID
aws sts get-caller-identity

# Create ECR repo (one time)
aws ecr create-repository --repository-name pixel-detector

# Login to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag pixel-lambda:test [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/pixel-detector:v0.3
docker push [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/pixel-detector:v0.3
```

2. **Create Lambda in Console:**
- Go to AWS Lambda console
- Click "Create function"
- Choose "Container image"
- Browse and select your image
- **Important settings:**
  - Memory: 2048 MB (Chromium needs it)
  - Timeout: 5 minutes
  - Environment variables: `HOME=/tmp`

3. **Test in Console:**
- Click "Test"
- Create new test event:
```json
{
  "domain": "example.com"
}
```
- Click "Test" again
- See results!

### Option B: Use CLI (If You Like Pain)

See `deploy_lambda_v03.sh` - but honestly, use the console for learning.

## Part 3: Add API Gateway (Optional)

1. In Lambda console, click "Add trigger"
2. Choose "API Gateway"
3. Create new HTTP API (cheaper than REST)
4. Security: Open (for now)
5. Click "Add"

Now you have a URL like:
```
https://abc123.execute-api.us-east-1.amazonaws.com/default/pixel-detector-learning
```

Test it:
```bash
curl -X POST https://YOUR_URL \
  -H "Content-Type: application/json" \
  -d '{"domain": "mountsinai.org"}'
```

## What You'll Learn

1. **Cold starts are real** - First request takes 20-30 seconds
2. **Logs are in CloudWatch** - Check them when things fail
3. **Costs are minimal** - Maybe $0.01 per day of testing
4. **Chromium in Lambda is hard** - That's why the image is 2GB

## Common Issues

**"Task timed out"**
- Increase timeout to 5 minutes
- Some sites just take forever

**"Container image is too large"**
- Our image is ~1.5GB, that's normal
- Lambda supports up to 10GB

**"Cannot find module"**
- Check the Dockerfile copied all files
- Check PYTHONPATH in environment variables

**"Chromium won't start"**
- Make sure HOME=/tmp is set
- Memory must be at least 2048 MB

## Monitoring Your Lambda

```bash
# Watch logs in real-time
aws logs tail /aws/lambda/pixel-detector-learning --follow

# See recent invocations
aws lambda list-functions | grep pixel

# Check costs (after 24 hours)
aws ce get-cost-and-usage \
  --time-period Start=2025-08-01,End=2025-08-10 \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --filter file://lambda-filter.json
```

## Next Steps After Learning

Once you understand Lambda basics:

1. **Add error handling** - See production checklist
2. **Add authentication** - API keys at minimum  
3. **Optimize cold starts** - Provisioned concurrency
4. **Add monitoring** - CloudWatch dashboards
5. **Read the overengineered guide** - AWS_LAMBDA_DEPLOYMENT_GUIDE.md

## Remember

This is for LEARNING. Don't put this in production without:
- Proper error handling
- Authentication
- Monitoring
- Cost controls
- Security review

But for learning? This is perfect. Total cost: <$5 for a week of experiments.

## Still Confused?

That's normal! Lambda + Docker + Chromium is complex. Try these:

1. Start with just the Lambda console test
2. Don't worry about API Gateway initially  
3. Use CloudWatch logs liberally
4. Ask specific questions, not "how do I do DevOps"

You got this! 🚀
