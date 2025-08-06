# AWS Fargate Deployment Guide

## Why Fargate for Large-Scale Domain Analysis

Fargate is ideal for this workload because:
- No 15-minute time limits (unlike Lambda)
- Handles long-running batch jobs for portfolio analysis
- No GLIBC compatibility issues with Playwright
- Auto-scaling and managed infrastructure
- Cost-effective for batch processing

## Quick Start

### 1. Build and Push to ECR

```bash
# Build the Docker image
docker build -f Dockerfile.safe -t pixel-scanner:fargate .

# Tag for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker tag pixel-scanner:fargate $ECR_URI/pixel-scanner:latest
docker push $ECR_URI/pixel-scanner:latest
```

### 2. Create Fargate Task Definition

```json
{
  "family": "pixel-scanner-batch",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "16384",
  "containerDefinitions": [{
    "name": "pixel-scanner",
    "image": "ECR_URI/pixel-scanner:latest",
    "essential": true,
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/pixel-scanner",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "environment": [
      {"name": "PYTHONUNBUFFERED", "value": "1"}
    ],
    "mountPoints": [
      {
        "sourceVolume": "efs-results",
        "containerPath": "/app/results"
      }
    ]
  }],
  "volumes": [{
    "name": "efs-results",
    "efsVolumeConfiguration": {
      "fileSystemId": "fs-12345678",
      "transitEncryption": "ENABLED"
    }
  }]
}
```

### 3. Run Batch Job

```bash
# Upload domains file to S3
aws s3 cp portfolio_domains.txt s3://your-bucket/inputs/domains.txt

# Start Fargate task
aws ecs run-task \
  --cluster pixel-scanner-cluster \
  --task-definition pixel-scanner-batch:latest \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
  --overrides '{
    "containerOverrides": [{
      "name": "pixel-scanner",
      "command": [
        "python", "-m", "pixel_detector", "batch",
        "/app/input/domains.txt",
        "-o", "/app/results",
        "--screenshot",
        "--max-concurrent", "10"
      ]
    }]
  }'
```

### 4. Monitor Progress

```bash
# View logs
aws logs tail /ecs/pixel-scanner --follow

# Check task status
aws ecs describe-tasks \
  --cluster pixel-scanner-cluster \
  --tasks TASK_ARN
```

## Cost Optimization

For large portfolio analysis:
- Fargate Spot: 70% cost savings
- Regular Fargate: Predictable performance
- Lambda: Not suitable for long-running batches

## Production Setup

1. **Use EFS for results** - Persistent storage across tasks
2. **Enable Fargate Spot** - 70% cost savings for batch jobs
3. **Set up CloudWatch alarms** - Monitor for failures
4. **Use Step Functions** - Orchestrate retries and batching
5. **Add Dead Letter Queue** - Handle failed domains

## Batch Processing Strategy

Split large domain lists into manageable chunks:
```bash
# Split into smaller chunks for parallel processing
split -l 1000 domains.txt chunk_

# Run parallel Fargate tasks
for chunk in chunk_*; do
  aws ecs run-task ... --overrides "...command: batch $chunk..."
done
```

## Security Considerations

1. **VPC Endpoints** - Keep traffic private
2. **IAM Roles** - Minimal permissions
3. **Secrets Manager** - For any API keys
4. **Security Groups** - Outbound 443 only

This approach will handle large-scale domain portfolio analysis efficiently and reliably!