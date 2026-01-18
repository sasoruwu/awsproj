# AWS Automated Image Processing System

## Quick Start Guide

### 1. Prerequisites Check
```bash
# Check if AWS CLI is installed
aws --version

# Check if SAM CLI is installed
sam --version

# Configure AWS credentials if not already done
aws configure
```

### 2. Deploy the System
```bash
# Quick deployment
./deploy.sh

# Or with custom settings
export STACK_NAME="my-image-processor"
export AWS_REGION="us-west-2"
./deploy.sh
```

### 3. Upload an Image
```bash
# Get your bucket name
SOURCE_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs[?OutputKey==`SourceBucketName`].OutputValue' \
  --output text)

# Upload your image
aws s3 cp path/to/your/image.jpg s3://$SOURCE_BUCKET/
```

### 4. Check Results
```bash
# Get processed bucket name
PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucketName`].OutputValue' \
  --output text)

# List processed images
aws s3 ls s3://$PROCESSED_BUCKET/

# Download processed images
aws s3 cp s3://$PROCESSED_BUCKET/your-image_thumbnail.jpg ./
aws s3 cp s3://$PROCESSED_BUCKET/your-image_medium.jpg ./
aws s3 cp s3://$PROCESSED_BUCKET/your-image_large.jpg ./
```

## What Happens?

1. You upload an image (JPG, JPEG, or PNG) to the source bucket
2. S3 automatically triggers the Lambda function
3. Lambda downloads the image, processes it, and creates:
   - **Thumbnail**: 150x150px
   - **Medium**: 800x600px  
   - **Large**: 1920x1080px
4. All processed images are uploaded to the processed bucket
5. You can download and use the processed images

## Local Testing

Test locally before deploying:
```bash
./test-local.sh
```

## Monitoring

View logs in real-time:
```bash
sam logs -n ImageProcessorFunction --stack-name image-processing-system --tail
```

## Cleanup

Remove all resources:
```bash
aws cloudformation delete-stack --stack-name image-processing-system

# Don't forget to empty the buckets first
aws s3 rm s3://$SOURCE_BUCKET --recursive
aws s3 rb s3://$SOURCE_BUCKET
aws s3 rm s3://$PROCESSED_BUCKET --recursive
aws s3 rb s3://$PROCESSED_BUCKET
```

## Troubleshooting

**Problem**: Images not being processed  
**Solution**: Check Lambda logs with `sam logs` command

**Problem**: Permission errors  
**Solution**: Ensure AWS CLI is configured: `aws configure`

**Problem**: Deployment fails  
**Solution**: Check if SAM CLI is installed: `sam --version`

For detailed information, see the main [README.md](README.md).
