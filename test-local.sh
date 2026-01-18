#!/bin/bash

# Test script for Image Processing Lambda function
# Tests the lambda function locally using SAM CLI

set -e

echo "Testing Image Processing Lambda function locally..."

# Create test event
cat > /tmp/test-event.json << 'EOF'
{
  "Records": [
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "2023-01-01T00:00:00.000Z",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "test-bucket"
        },
        "object": {
          "key": "test-image.jpg"
        }
      }
    }
  ]
}
EOF

echo "Created test event at /tmp/test-event.json"

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: AWS SAM CLI is not installed. Please install it first."
    exit 1
fi

# Build the application
echo "Building SAM application..."
sam build

# Invoke function locally
echo "Invoking function locally..."
sam local invoke ImageProcessorFunction -e /tmp/test-event.json

echo "Test completed!"
