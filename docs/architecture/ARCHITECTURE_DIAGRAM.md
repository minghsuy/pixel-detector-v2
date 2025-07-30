# Pixel Detector Architecture Diagrams

## Current Architecture (As-Is)

```mermaid
graph TB
    subgraph "Local Environment"
        User[User/Terminal]
        CLI[CLI Interface<br/>pixel-detector]
        
        subgraph "Core Components"
            Scanner[Scanner Module<br/>- Playwright automation<br/>- Concurrent processing]
            
            subgraph "Detectors"
                Meta[Meta Pixel<br/>Detector]
                GA[Google Analytics<br/>Detector]
                GAds[Google Ads<br/>Detector]
                TT[TikTok<br/>Detector]
                LI[LinkedIn<br/>Detector]
                TW[Twitter<br/>Detector]
                PI[Pinterest<br/>Detector]
                SC[Snapchat<br/>Detector]
            end
        end
        
        subgraph "Output"
            JSON[JSON Files]
            Console[Terminal Output]
            Screenshots[PNG Files]
        end
    end
    
    subgraph "External"
        Target[Target Healthcare<br/>Websites]
    end
    
    User --> CLI
    CLI --> Scanner
    Scanner --> Meta
    Scanner --> GA
    Scanner --> GAds
    Scanner --> TT
    Scanner --> LI
    Scanner --> TW
    Scanner --> PI
    Scanner --> SC
    Scanner --> Target
    Scanner --> JSON
    Scanner --> Console
    Scanner --> Screenshots
    
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style Target fill:#faa,stroke:#333,stroke-width:2px
```

## Target Architecture (To-Be)

```mermaid
graph TB
    subgraph "Client Layer"
        WebUI[Web Dashboard<br/>React/Vue]
        CLIUI[CLI Tool]
        API[REST API<br/>Clients]
    end
    
    subgraph "API Gateway"
        APIGW[AWS API Gateway<br/>- Authentication<br/>- Rate Limiting<br/>- Request Routing]
    end
    
    subgraph "Compute Layer"
        Lambda1[Scan Lambda<br/>- Single domain<br/>- Real-time results]
        Lambda2[Batch Lambda<br/>- Multi-domain<br/>- Async processing]
        Container[ECS/Fargate<br/>- Long-running scans<br/>- Scheduled jobs]
    end
    
    subgraph "Queue Layer"
        SQS[SQS Queue<br/>- Batch jobs<br/>- Retry handling]
        SNS[SNS Topics<br/>- Notifications<br/>- Alerts]
    end
    
    subgraph "Storage Layer"
        S3[S3 Bucket<br/>- Reports<br/>- Screenshots<br/>- Archives]
        DDB[DynamoDB<br/>- Scan history<br/>- Metadata<br/>- User data]
        Cache[ElastiCache<br/>- API cache<br/>- Session data]
    end
    
    subgraph "Monitoring"
        CW[CloudWatch<br/>- Logs<br/>- Metrics<br/>- Alarms]
        XRay[X-Ray<br/>- Tracing<br/>- Performance]
    end
    
    subgraph "External Services"
        Sites[Healthcare<br/>Websites]
        Email[SES<br/>Email Service]
        Auth[Cognito<br/>Authentication]
    end
    
    WebUI --> APIGW
    CLIUI --> APIGW
    API --> APIGW
    
    APIGW --> Lambda1
    APIGW --> Lambda2
    APIGW --> Container
    
    Lambda1 --> Sites
    Lambda2 --> SQS
    Container --> Sites
    
    SQS --> Lambda2
    
    Lambda1 --> S3
    Lambda1 --> DDB
    Lambda2 --> S3
    Lambda2 --> DDB
    Container --> S3
    Container --> DDB
    
    Lambda1 --> CW
    Lambda2 --> CW
    Container --> CW
    
    CW --> SNS
    SNS --> Email
    
    APIGW --> Auth
    APIGW --> Cache
    
    Lambda1 --> XRay
    Lambda2 --> XRay
    
    style WebUI fill:#90EE90,stroke:#333,stroke-width:2px
    style Sites fill:#FFB6C1,stroke:#333,stroke-width:2px
    style DDB fill:#87CEEB,stroke:#333,stroke-width:2px
    style S3 fill:#87CEEB,stroke:#333,stroke-width:2px
    style Lambda1 fill:#FFE4B5,stroke:#333,stroke-width:2px
    style Lambda2 fill:#FFE4B5,stroke:#333,stroke-width:2px
    style Container fill:#FFE4B5,stroke:#333,stroke-width:2px
    style APIGW fill:#DDA0DD,stroke:#333,stroke-width:2px
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Lambda
    participant Queue
    participant Scanner
    participant DB
    participant S3
    participant Notification
    
    User->>API: POST /scan {domains: [...]}
    API->>API: Validate & Authenticate
    API->>Lambda: Invoke scan function
    
    alt Single Domain
        Lambda->>Scanner: Direct scan
        Scanner->>Scanner: Launch browser
        Scanner->>Scanner: Run 8 detectors
        Scanner->>S3: Store screenshots
        Scanner->>DB: Save results
        Scanner->>Lambda: Return results
        Lambda->>API: Return JSON
        API->>User: 200 OK {results}
    else Batch Domains
        Lambda->>Queue: Queue scan jobs
        Lambda->>DB: Create job record
        Lambda->>API: Return job ID
        API->>User: 202 Accepted {job_id}
        
        Queue->>Lambda: Process job
        Lambda->>Scanner: Scan domain
        Scanner->>S3: Store results
        Scanner->>DB: Update job status
        
        alt Violations Found
            Lambda->>Notification: Send alert
            Notification->>User: Email notification
        end
    end
    
    User->>API: GET /results/{job_id}
    API->>DB: Query results
    DB->>API: Return data
    API->>User: 200 OK {results}
```

## Component Interaction Matrix

| Component | Talks To | Protocol | Purpose |
|-----------|----------|----------|---------|
| CLI | API Gateway | HTTPS | Submit scan requests |
| Web UI | API Gateway | HTTPS | View results, manage scans |
| API Gateway | Lambda | AWS SDK | Invoke functions |
| Lambda | DynamoDB | AWS SDK | Store/retrieve data |
| Lambda | S3 | AWS SDK | Store files |
| Lambda | SQS | AWS SDK | Queue batch jobs |
| Lambda | CloudWatch | AWS SDK | Log events |
| CloudWatch | SNS | AWS Events | Trigger alerts |
| SNS | SES | AWS SDK | Send emails |
| Lambda | Target Sites | HTTPS | Scan websites |

## Security Architecture

```mermaid
graph TB
    subgraph "Public Internet"
        Users[Users]
        Targets[Target Websites]
    end
    
    subgraph "AWS Edge"
        CF[CloudFront<br/>- DDoS Protection<br/>- Geographic restrictions]
        WAF[WAF<br/>- Rate limiting<br/>- IP filtering]
    end
    
    subgraph "VPC"
        subgraph "Public Subnet"
            ALB[Application<br/>Load Balancer]
            NAT[NAT Gateway]
        end
        
        subgraph "Private Subnet"
            Lambda[Lambda Functions<br/>- No direct internet<br/>- IAM roles only]
            ECS[ECS Tasks<br/>- Security groups<br/>- Private IPs]
        end
        
        subgraph "Data Subnet"
            DB[(DynamoDB<br/>- Encryption at rest<br/>- VPC endpoints)]
            S3[(S3<br/>- Bucket policies<br/>- Encryption)]
        end
    end
    
    subgraph "Security Services"
        KMS[KMS<br/>- Key management<br/>- Encryption keys]
        SM[Secrets Manager<br/>- API keys<br/>- Credentials]
        CW[CloudWatch<br/>- Security events<br/>- Anomaly detection]
    end
    
    Users --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> Lambda
    Lambda --> NAT
    NAT --> Targets
    Lambda --> DB
    Lambda --> S3
    Lambda --> KMS
    Lambda --> SM
    Lambda --> CW
    
    style Users fill:#f9f,stroke:#333,stroke-width:2px
    style Targets fill:#faa,stroke:#333,stroke-width:2px
    style KMS fill:#9f9,stroke:#333,stroke-width:2px
```

## Scaling Strategy

### Current Limitations
- **Single machine**: Limited by local resources
- **Sequential scanning**: One domain at a time (or 5 with batch)
- **No persistence**: Results lost after execution
- **Manual process**: No automation or scheduling

### Future Capabilities
- **Horizontal scaling**: Unlimited Lambda concurrency
- **Batch processing**: 1000s of domains via SQS
- **Auto-scaling**: Based on queue depth
- **Scheduled scans**: Daily/weekly compliance checks
- **Global distribution**: Multi-region deployment

### Performance Targets
| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Domains/hour | 300 | 10,000 | Lambda concurrency |
| Availability | Local only | 99.9% | Multi-AZ deployment |
| Response time | N/A | <200ms | API caching |
| Storage | Local files | Unlimited | S3 + DynamoDB |
| Concurrent users | 1 | 1000+ | API Gateway scaling |