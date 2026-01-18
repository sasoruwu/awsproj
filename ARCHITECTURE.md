# Architecture Documentation

## System Architecture

The AWS Automated Image Processing System follows a serverless, event-driven architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  User/Application                                           │
│  Uploads Image                                              │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────┐                                       │
│  │  Source S3       │                                       │
│  │  Bucket          │                                       │
│  │  (Original       │                                       │
│  │   Images)        │                                       │
│  └────────┬─────────┘                                       │
│           │                                                 │
│           │ S3 Event Notification                           │
│           │ (ObjectCreated)                                 │
│           ▼                                                 │
│  ┌──────────────────┐                                       │
│  │  Lambda Function │                                       │
│  │  Image Processor │                                       │
│  │                  │                                       │
│  │  - Downloads     │                                       │
│  │  - Resizes       │                                       │
│  │  - Uploads       │                                       │
│  └────────┬─────────┘                                       │
│           │                                                 │
│           │ Processed Images                                │
│           ▼                                                 │
│  ┌──────────────────┐                                       │
│  │  Processed S3    │                                       │
│  │  Bucket          │                                       │
│  │  (Resized        │                                       │
│  │   Images)        │                                       │
│  └──────────────────┘                                       │
│                                                             │
│  CloudWatch Logs ────────► Lambda Logs                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Source S3 Bucket
- **Purpose**: Stores original uploaded images
- **Trigger**: Configured with S3 event notifications
- **Events**: Triggers on `.jpg`, `.jpeg`, `.png` file uploads
- **Access**: Read-only for Lambda function

### 2. Lambda Function
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 60 seconds
- **Trigger**: S3 ObjectCreated events
- **Libraries**: 
  - boto3: AWS SDK for Python
  - Pillow: Image processing library
- **Process**:
  1. Receives S3 event notification
  2. Downloads image from source bucket
  3. Opens image with Pillow
  4. Converts RGBA to RGB if needed
  5. Creates three resized versions
  6. Uploads all versions to processed bucket

### 3. Processed S3 Bucket
- **Purpose**: Stores processed/resized images
- **Structure**: Same folder structure as source
- **Naming**: `{original_name}_{size}.jpg`
- **Sizes**:
  - Thumbnail: 150x150px
  - Medium: 800x600px
  - Large: 1920x1080px
- **Access**: Write access for Lambda function

### 4. IAM Roles & Permissions
- **Lambda Execution Role**:
  - `s3:GetObject` on source bucket
  - `s3:PutObject` on processed bucket
  - CloudWatch Logs write permissions
- **S3 Bucket Policy**:
  - Allows Lambda invocation from S3 service

### 5. CloudWatch Logs
- **Purpose**: Application logging and monitoring
- **Log Group**: `/aws/lambda/{function-name}`
- **Retention**: Default (never expire)
- **Content**: 
  - Processing start/end events
  - Error messages
  - Performance metrics

## Data Flow

1. **Upload Phase**
   - User uploads image to source S3 bucket
   - S3 generates ObjectCreated event
   - Event matches configured filters (.jpg, .jpeg, .png)

2. **Processing Phase**
   - Lambda function receives event
   - Function extracts bucket name and object key
   - Downloads image content from S3
   - Loads image into memory with Pillow
   - Performs format conversion if needed
   - Creates three resized versions maintaining aspect ratio
   - Each version is saved as JPEG with 85% quality

3. **Storage Phase**
   - Each resized image is uploaded to processed bucket
   - Metadata includes original and processed dimensions
   - Content-Type is set to `image/jpeg`
   - Images are stored with descriptive names

4. **Completion Phase**
   - Lambda returns success response
   - CloudWatch logs record processing details
   - Images are available for download

## Scalability

### Automatic Scaling
- **Lambda**: Automatically scales to handle concurrent requests
  - Max concurrent executions: 1000 (default)
  - Can be increased via AWS support
- **S3**: Virtually unlimited storage and throughput
  - No pre-provisioning required
  - Automatic load distribution

### Performance Considerations
- **Cold Start**: First invocation may take 1-2 seconds
- **Warm Invocation**: Subsequent calls ~200-500ms
- **Processing Time**: Depends on image size
  - 1MB image: ~1-2 seconds
  - 5MB image: ~3-5 seconds
  - 10MB image: ~6-10 seconds

### Optimization Strategies
1. **Increase Lambda Memory**: More memory = more CPU
2. **Provisioned Concurrency**: Eliminate cold starts
3. **Image Pre-validation**: Check size/format before processing
4. **Async Processing**: Return immediately, process async
5. **Batch Processing**: Process multiple images in one invocation

## Security

### Data Protection
- **Encryption at Rest**: S3 buckets use default encryption
- **Encryption in Transit**: All S3/Lambda communication uses HTTPS
- **No Public Access**: Buckets not publicly accessible by default

### Access Control
- **IAM Roles**: Least-privilege principle
- **Resource Policies**: S3 bucket policies restrict access
- **Lambda Permissions**: Only S3 can invoke function

### Best Practices
1. Enable S3 bucket versioning
2. Configure bucket lifecycle policies
3. Enable CloudTrail for audit logging
4. Use VPC endpoints for enhanced security
5. Implement bucket policies for additional restrictions

## Cost Optimization

### Pay-per-Use Model
- **Lambda**: Charged per request and duration
  - 1M free requests/month
  - $0.20 per 1M requests after
  - $0.0000166667 per GB-second
  
- **S3**: Charged per storage and requests
  - Standard storage: ~$0.023/GB/month
  - PUT requests: $0.005 per 1000
  - GET requests: $0.0004 per 1000

### Cost Reduction Tips
1. Use S3 lifecycle policies to move old images to cheaper storage
2. Enable S3 Intelligent-Tiering
3. Delete source images after processing if not needed
4. Use CloudWatch Logs retention policies
5. Right-size Lambda memory allocation

## Monitoring & Alerting

### CloudWatch Metrics
- **Lambda Metrics**:
  - Invocations
  - Duration
  - Errors
  - Throttles
  - Concurrent executions

- **S3 Metrics**:
  - Bucket size
  - Number of objects
  - Request counts

### Recommended Alarms
1. Lambda error rate > 5%
2. Lambda duration > 50 seconds
3. Lambda throttles > 0
4. S3 4xx/5xx errors

### Logging Best Practices
- Log all image processing attempts
- Include image dimensions and processing time
- Log errors with full stack traces
- Use structured logging (JSON format)

## Disaster Recovery

### Backup Strategy
- **S3 Cross-Region Replication**: Copy buckets to another region
- **S3 Versioning**: Keep multiple versions of objects
- **Lambda Code Backup**: Store in version control (Git)

### Recovery Procedures
1. **Lambda Failure**: Automatic retry by S3
2. **Bucket Deletion**: Restore from backup/versioning
3. **Code Issues**: Rollback to previous Lambda version
4. **Region Outage**: Failover to replicated region

## Future Enhancements

### Potential Features
1. **Additional Formats**: WebP, AVIF conversion
2. **Watermarking**: Add logos or text to images
3. **Face Detection**: Auto-crop to faces
4. **Quality Control**: Reject low-quality images
5. **Batch Processing**: Process multiple images together
6. **CDN Integration**: CloudFront for faster delivery
7. **Metadata Extraction**: EXIF data preservation
8. **Custom Sizes**: User-defined dimensions
9. **Image Optimization**: Smart compression
10. **Video Thumbnail**: Generate thumbnails from videos

### Integration Options
1. **API Gateway**: REST API for uploads
2. **Step Functions**: Complex workflows
3. **SNS**: Notifications on completion
4. **DynamoDB**: Track processing status
5. **SQS**: Queue for high-volume processing
