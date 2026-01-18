# Example: Complete Image Processing Workflow

This example demonstrates a complete workflow from deployment to image processing.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured (`aws configure`)
- AWS SAM CLI installed
- Sample image file (we'll create one if needed)

## Step-by-Step Walkthrough

### 1. Deploy the System

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd awsproj

# Deploy with default settings
./deploy.sh
```

Expected output:
```
Building SAM application...
Deploying SAM application...
Successfully created/updated stack - image-processing-system
```

### 2. Verify Deployment

```bash
# Get the stack outputs
aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs' \
  --output table
```

Expected output:
```
-----------------------------------------------------------------
|                       DescribeStacks                          |
+------------------------------+--------------------------------+
|         OutputKey            |         OutputValue            |
+------------------------------+--------------------------------+
|  SourceBucketName            |  image-processing-system-...   |
|  ProcessedBucketName         |  image-processing-system-...   |
|  ImageProcessorFunctionArn   |  arn:aws:lambda:us-east-1:... |
+------------------------------+--------------------------------+
```

### 3. Prepare Test Image

If you don't have a test image, create one:

```bash
# Install ImageMagick (if not installed)
# macOS: brew install imagemagick
# Ubuntu: sudo apt-get install imagemagick

# Create a test image
convert -size 2000x1500 xc:blue -pointsize 100 -fill white \
  -gravity center -annotate +0+0 "Test Image" test-image.jpg

# Or use Python to create a test image
python3 << 'EOF'
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 2000x1500 test image
img = Image.new('RGB', (2000, 1500), color='blue')
draw = ImageDraw.Draw(img)

# Add text
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
except:
    font = ImageFont.load_default()

text = "Test Image"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (2000 - text_width) // 2
y = (1500 - text_height) // 2
draw.text((x, y), text, fill='white', font=font)

img.save('test-image.jpg', 'JPEG', quality=95)
print("✓ Created test-image.jpg")
EOF
```

### 4. Upload Image for Processing

```bash
# Get the source bucket name
SOURCE_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs[?OutputKey==`SourceBucketName`].OutputValue' \
  --output text)

echo "Uploading to bucket: $SOURCE_BUCKET"

# Upload the test image
aws s3 cp test-image.jpg s3://$SOURCE_BUCKET/

# Upload to a subfolder (optional)
aws s3 cp test-image.jpg s3://$SOURCE_BUCKET/uploads/sample.jpg
```

Expected output:
```
upload: ./test-image.jpg to s3://image-processing-system-source-images/test-image.jpg
```

### 5. Monitor Processing

```bash
# Watch Lambda logs in real-time
sam logs -n ImageProcessorFunction \
  --stack-name image-processing-system \
  --tail

# Or check recent logs
sam logs -n ImageProcessorFunction \
  --stack-name image-processing-system \
  --start-time '5min ago'
```

Expected log output:
```
2024-12-19 12:00:01 START RequestId: abc123...
2024-12-19 12:00:01 Received event: {"Records": [...]}
2024-12-19 12:00:01 Processing image: test-image.jpg from bucket: ...
2024-12-19 12:00:02 Uploaded Thumbnail version: test-image_thumbnail.jpg
2024-12-19 12:00:02 Uploaded Medium version: test-image_medium.jpg
2024-12-19 12:00:03 Uploaded Large version: test-image_large.jpg
2024-12-19 12:00:03 Successfully processed all versions of test-image.jpg
2024-12-19 12:00:03 END RequestId: abc123...
```

### 6. Verify Processed Images

```bash
# Get the processed bucket name
PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-processing-system \
  --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucketName`].OutputValue' \
  --output text)

echo "Processed images in bucket: $PROCESSED_BUCKET"

# List processed images
aws s3 ls s3://$PROCESSED_BUCKET/ --recursive --human-readable

# Expected output:
# 2024-12-19 12:00:02   45.2 KiB test-image_thumbnail.jpg
# 2024-12-19 12:00:02  234.5 KiB test-image_medium.jpg
# 2024-12-19 12:00:03  567.8 KiB test-image_large.jpg
```

### 7. Download Processed Images

```bash
# Create output directory
mkdir -p processed-images

# Download all processed versions
aws s3 cp s3://$PROCESSED_BUCKET/test-image_thumbnail.jpg processed-images/
aws s3 cp s3://$PROCESSED_BUCKET/test-image_medium.jpg processed-images/
aws s3 cp s3://$PROCESSED_BUCKET/test-image_large.jpg processed-images/

echo "✓ Downloaded processed images to ./processed-images/"
ls -lh processed-images/
```

### 8. Inspect Image Metadata

```bash
# View image dimensions
for img in processed-images/*.jpg; do
  echo "File: $(basename $img)"
  identify -format "  Dimensions: %wx%h\n  Size: %b\n" "$img"
  echo ""
done

# Or using Python
python3 << 'EOF'
from PIL import Image
import os

for filename in sorted(os.listdir('processed-images')):
    if filename.endswith('.jpg'):
        filepath = os.path.join('processed-images', filename)
        with Image.open(filepath) as img:
            size_kb = os.path.getsize(filepath) / 1024
            print(f"{filename}:")
            print(f"  Dimensions: {img.size[0]}x{img.size[1]}")
            print(f"  Format: {img.format}")
            print(f"  Mode: {img.mode}")
            print(f"  Size: {size_kb:.1f} KB")
            print()
EOF
```

Expected output:
```
test-image_thumbnail.jpg:
  Dimensions: 150x112
  Format: JPEG
  Mode: RGB
  Size: 8.5 KB

test-image_medium.jpg:
  Dimensions: 800x600
  Format: JPEG
  Mode: RGB
  Size: 124.3 KB

test-image_large.jpg:
  Dimensions: 1920x1440
  Format: JPEG
  Mode: RGB
  Size: 456.7 KB
```

### 9. Test with Different Image Formats

```bash
# Test with PNG (with transparency)
python3 << 'EOF'
from PIL import Image, ImageDraw

# Create PNG with transparency
img = Image.new('RGBA', (1000, 1000), (255, 0, 0, 128))
draw = ImageDraw.Draw(img)
draw.ellipse([200, 200, 800, 800], fill=(0, 0, 255, 200))
img.save('test-image-transparent.png', 'PNG')
print("✓ Created test-image-transparent.png")
EOF

# Upload PNG image
aws s3 cp test-image-transparent.png s3://$SOURCE_BUCKET/

# Wait a few seconds and check processed images
sleep 5
aws s3 ls s3://$PROCESSED_BUCKET/ --recursive | grep test-image-transparent
```

### 10. Monitor Costs

```bash
# Check Lambda invocations (approximate cost)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=image-processing-system-image-processor \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum

# Check S3 storage (approximate cost)
aws s3 ls s3://$PROCESSED_BUCKET --recursive --summarize | tail -2
```

### 11. Cleanup (When Done)

```bash
# Remove all resources
./cleanup.sh

# This will:
# 1. Empty both S3 buckets
# 2. Delete both S3 buckets
# 3. Delete the CloudFormation stack
# 4. Remove the Lambda function
```

## Common Issues and Solutions

### Issue: Lambda Not Triggered

**Symptom**: Image uploaded but no processed versions appear

**Solutions**:
1. Check Lambda logs for errors
2. Verify file extension is .jpg, .jpeg, or .png
3. Check Lambda function has permission to be invoked by S3

```bash
# Verify permissions
aws lambda get-policy \
  --function-name image-processing-system-image-processor
```

### Issue: Out of Memory Error

**Symptom**: Lambda fails with "Task timed out" or memory errors

**Solutions**:
1. Increase Lambda memory in template.yaml
2. Test with smaller images first
3. Check image is not corrupted

```bash
# Check Lambda configuration
aws lambda get-function-configuration \
  --function-name image-processing-system-image-processor
```

### Issue: Permission Denied

**Symptom**: AccessDenied errors in logs

**Solutions**:
1. Verify IAM role has proper permissions
2. Check bucket policies
3. Ensure Lambda execution role is correct

```bash
# Check IAM role
aws cloudformation describe-stack-resources \
  --stack-name image-processing-system \
  --logical-resource-id ImageProcessorFunctionRole
```

## Advanced Usage

### Batch Upload Multiple Images

```bash
# Upload all JPG images from a directory
for img in /path/to/images/*.jpg; do
  aws s3 cp "$img" s3://$SOURCE_BUCKET/batch/
  echo "Uploaded $(basename $img)"
  sleep 1  # Rate limiting
done
```

### Sync Entire Directory

```bash
# Sync all images from a directory
aws s3 sync /path/to/images/ s3://$SOURCE_BUCKET/photos/ \
  --exclude "*" \
  --include "*.jpg" \
  --include "*.jpeg" \
  --include "*.png"
```

### Download All Processed Images

```bash
# Download all processed images
aws s3 sync s3://$PROCESSED_BUCKET/ ./all-processed-images/
```

## Performance Benchmarks

Typical processing times (512MB Lambda):

| Original Size | Resolution | Processing Time |
|---------------|------------|-----------------|
| 500 KB        | 1920x1080  | 1-2 seconds     |
| 2 MB          | 4000x3000  | 2-4 seconds     |
| 5 MB          | 6000x4000  | 4-6 seconds     |
| 10 MB         | 8000x6000  | 6-10 seconds    |

Note: First invocation (cold start) adds ~1-2 seconds.

## Next Steps

- Explore the [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
- Read [CONTRIBUTING.md](CONTRIBUTING.md) to add new features
- Check [CHANGELOG.md](CHANGELOG.md) for version history
- Review [README.md](README.md) for complete documentation
