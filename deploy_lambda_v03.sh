#!/bin/bash
# deploy_lambda_v03.sh - Simplest possible Lambda deployment
# For LEARNING, not production!

echo "🎓 Learning Lambda Deployment - v0.3"
echo "===================================="

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install it first:"
    echo "   brew install awscli"
    exit 1
fi

# Basic config
FUNCTION_NAME="pixel-detector-learning"
AWS_REGION="us-east-1"  # Cheapest region

echo "📍 Using region: $AWS_REGION"
echo "📍 Function name: $FUNCTION_NAME"

# Step 1: Build locally first to test
echo ""
echo "🔨 Step 1: Building Docker image locally..."
docker build -f Dockerfile.lambda -t pixel-lambda:test .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed. Fix errors above first."
    exit 1
fi

echo "✅ Docker build successful!"

# Step 2: Test locally
echo ""
echo "🧪 Step 2: Testing locally with Docker..."
echo "Starting local Lambda runtime..."

# Run in background
docker run -d --name lambda-test -p 9000:8080 pixel-lambda:test

# Wait for it to start
sleep 3

# Test it
echo "Testing with curl..."
curl -s -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"domain": "example.com"}' | jq .

# Clean up
docker stop lambda-test && docker rm lambda-test

echo ""
echo "If the test worked, you're ready for AWS!"
echo ""
echo "📚 Next steps to deploy to AWS:"
echo "1. Create ECR repository:"
echo "   aws ecr create-repository --repository-name pixel-detector --region $AWS_REGION"
echo ""
echo "2. Login to ECR:"
echo "   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin [YOUR_ACCOUNT_ID].dkr.ecr.$AWS_REGION.amazonaws.com"
echo ""
echo "3. Push image:"
echo "   docker tag pixel-lambda:test [YOUR_ACCOUNT_ID].dkr.ecr.$AWS_REGION.amazonaws.com/pixel-detector:v0.3"
echo "   docker push [YOUR_ACCOUNT_ID].dkr.ecr.$AWS_REGION.amazonaws.com/pixel-detector:v0.3"
echo ""
echo "4. Create Lambda function in AWS Console (easier than CLI for learning!)"
echo "   - Go to Lambda console"
echo "   - Create function -> Container image"
echo "   - Select your pushed image"
echo "   - Set memory to 2048 MB"
echo "   - Set timeout to 5 minutes"
echo ""
echo "That's it! Don't overcomplicate it 🎉"
