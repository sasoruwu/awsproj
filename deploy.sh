#!/bin/bash

# Deploy script for AWS Image Processing System
# This script builds and deploys the SAM application

set -e

echo "Starting deployment of AWS Image Processing System..."

# Set variables
STACK_NAME="${STACK_NAME:-image-processing-system}"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${S3_BUCKET:-}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: AWS SAM CLI is not installed. Please install it first."
    exit 1
fi

echo "Building SAM application..."
sam build

echo "Deploying SAM application..."
if [ -z "$S3_BUCKET" ]; then
    # Guided deployment (interactive)
    sam deploy --guided --stack-name "$STACK_NAME" --region "$REGION" \
        --capabilities CAPABILITY_IAM
else
    # Non-interactive deployment
    sam deploy --stack-name "$STACK_NAME" --region "$REGION" \
        --s3-bucket "$S3_BUCKET" \
        --capabilities CAPABILITY_IAM \
        --no-fail-on-empty-changeset
fi

echo "Deployment completed successfully!"
echo ""
echo "Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "To upload an image for processing, use:"
echo '  SOURCE_BUCKET=$(aws cloudformation describe-stacks --stack-name '"$STACK_NAME"' --region '"$REGION"' --query '"'"'Stacks[0].Outputs[?OutputKey==`SourceBucketName`].OutputValue'"'"' --output text)'
echo '  aws s3 cp your-image.jpg s3://$SOURCE_BUCKET/'
