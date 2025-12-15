# AWS Automated Image Processing System

An automated serverless image processing system built on AWS using Lambda, S3, and CloudFormation. This system automatically processes images uploaded to an S3 bucket by creating multiple resized versions (thumbnail, medium, and large).

## Features

- **Automatic Processing**: Images are automatically processed when uploaded to the source S3 bucket
- **Multiple Sizes**: Generates three versions of each image:
  - Thumbnail: 150x150px
  - Medium: 800x600px
  - Large: 1920x1080px
- **Format Support**: Supports JPG, JPEG, and PNG image formats
- **Smart Resizing**: Maintains aspect ratio while resizing
- **Format Conversion**: Handles RGBA to RGB conversion for JPEG compatibility
- **Serverless Architecture**: No servers to manage, scales automatically
- **Cost Effective**: Pay only for what you use

## Architecture

The system consists of:

1. **Source S3 Bucket**: Upload your original images here
2. **Lambda Function**: Automatically triggered by S3 events to process images
3. **Processed S3 Bucket**: Stores the resized image versions
4. **CloudFormation Template**: Infrastructure as Code for easy deployment

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- AWS SAM CLI installed
- Python 3.11 or later (for local testing)

### Installing AWS SAM CLI

```bash
# macOS
brew install aws-sam-cli

# Windows
choco install aws-sam-cli

# Linux
pip install aws-sam-cli
```

## Project Structure

```
awsproj/
├── src/
│   ├── image_processor.py    # Lambda function code
│   └── requirements.txt       # Python dependencies
├── events/
│   └── s3-event.json         # Sample S3 event for testing
├── template.yaml             # SAM/CloudFormation template
├── deploy.sh                 # Deployment script
├── test-local.sh            # Local testing script
└── README.md                # This file
```

## Deployment

### Quick Deployment

1. Clone the repository:
```bash
git clone <repository-url>
cd awsproj
```

2. Run the deployment script:
```bash
./deploy.sh
```

This will:
- Build the SAM application
- Deploy the CloudFormation stack
- Create the necessary S3 buckets
- Set up the Lambda function with proper permissions

### Manual Deployment

If you prefer to deploy manually:

```bash
# Build the application
sam build

# Deploy with guided mode (first time)
sam deploy --guided

# Deploy with existing configuration
sam deploy
```

### Deployment Configuration

You can customize the deployment using environment variables:

```bash
export STACK_NAME="my-image-processor"
export AWS_REGION="us-west-2"
export S3_BUCKET="my-deployment-bucket"
./deploy.sh
```

## Usage

### Upload Images for Processing

After deployment, get your source bucket name:

```bash
SOURCE_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs[?OutputKey==`SourceBucketName`].OutputValue' \
  --output text)
```

Upload an image:

```bash
aws s3 cp my-image.jpg s3://$SOURCE_BUCKET/
```

The Lambda function will automatically:
1. Detect the upload
2. Download the image
3. Create three resized versions
4. Upload them to the processed bucket

### Retrieve Processed Images

Get your processed bucket name:

```bash
PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucketName`].OutputValue' \
  --output text)
```

List processed images:

```bash
aws s3 ls s3://$PROCESSED_BUCKET/
```

Download processed images:

```bash
aws s3 cp s3://$PROCESSED_BUCKET/my-image_thumbnail.jpg ./
aws s3 cp s3://$PROCESSED_BUCKET/my-image_medium.jpg ./
aws s3 cp s3://$PROCESSED_BUCKET/my-image_large.jpg ./
```

## Local Testing

Test the Lambda function locally before deploying:

```bash
./test-local.sh
```

Or manually:

```bash
sam build
sam local invoke ImageProcessorFunction -e events/s3-event.json
```

## Monitoring

### View Lambda Logs

```bash
# View recent logs
sam logs -n ImageProcessorFunction --stack-name image-processing-system

# Tail logs in real-time
sam logs -n ImageProcessorFunction --stack-name image-processing-system --tail
```

### CloudWatch Logs

You can also view logs in the AWS Console:
1. Navigate to CloudWatch Logs
2. Find the log group: `/aws/lambda/image-processing-system-image-processor`

## Configuration

### Modify Image Sizes

Edit `src/image_processor.py` and update the size constants:

```python
THUMBNAIL_SIZE = (150, 150)  # Modify as needed
MEDIUM_SIZE = (800, 600)     # Modify as needed
LARGE_SIZE = (1920, 1080)    # Modify as needed
```

### Supported File Types

The system currently supports:
- `.jpg`
- `.jpeg`
- `.png`

To add more file types, edit the `template.yaml` file and add additional S3 event filters.

## Cost Estimation

The system uses serverless architecture, so costs scale with usage:

- **Lambda**: First 1M requests/month are free, then $0.20 per 1M requests
- **S3**: Storage costs vary by region (~$0.023 per GB for standard storage)
- **Data Transfer**: First 100 GB/month free for data transfer out

Example: Processing 10,000 images/month (~2MB each):
- Lambda costs: ~$0.20
- S3 storage (60GB): ~$1.38
- Total: ~$1.58/month

## Cleanup

To delete all resources:

```bash
aws cloudformation delete-stack --stack-name image-processing-system

# Empty and delete buckets manually (CloudFormation won't delete non-empty buckets)
aws s3 rm s3://$SOURCE_BUCKET --recursive
aws s3 rb s3://$SOURCE_BUCKET

aws s3 rm s3://$PROCESSED_BUCKET --recursive
aws s3 rb s3://$PROCESSED_BUCKET
```

## Troubleshooting

### Lambda Function Fails

1. Check CloudWatch Logs for error messages
2. Verify the Lambda function has permissions to read from source bucket and write to processed bucket
3. Ensure the image format is supported

### Images Not Processing

1. Verify S3 event notifications are configured correctly
2. Check that the Lambda function has permission to be invoked by S3
3. Verify the image file extension matches the event filters (.jpg, .jpeg, .png)

### Permission Errors

Ensure your AWS CLI is configured with proper credentials:

```bash
aws configure
```

## Security Considerations

- S3 buckets are created with default encryption
- Lambda function uses IAM roles with minimal required permissions
- No public access to buckets by default
- Consider adding bucket policies for additional security

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check CloudWatch Logs for debugging information
- Review AWS Lambda and S3 documentation