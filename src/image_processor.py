"""
AWS Lambda function for automated image processing.
Processes images uploaded to S3 bucket by creating thumbnails and resized versions.
"""

import json
import os
import boto3
from PIL import Image
from io import BytesIO
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')

# Get environment variables
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET')

# Image processing configurations
THUMBNAIL_SIZE = (150, 150)
MEDIUM_SIZE = (800, 600)
LARGE_SIZE = (1920, 1080)


def lambda_handler(event, context):
    """
    Main Lambda handler function.
    Triggered by S3 upload events and processes images.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Process each record in the event
        for record in event['Records']:
            # Extract bucket and object information
            source_bucket = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            logger.info(f"Processing image: {object_key} from bucket: {source_bucket}")
            
            # Download the image from S3
            response = s3_client.get_object(Bucket=source_bucket, Key=object_key)
            image_content = response['Body'].read()
            
            # Process the image
            process_image(image_content, object_key)
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image processing completed successfully',
                'processed_images': len(event['Records'])
            })
        }
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing image',
                'error': str(e)
            })
        }


def process_image(image_content, original_key):
    """
    Process a single image by creating multiple versions.
    
    Args:
        image_content: Binary content of the image
        original_key: Original S3 object key
    """
    try:
        # Open image with Pillow
        image = Image.open(BytesIO(image_content))
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Get file name without extension
        file_name = os.path.splitext(original_key)[0]
        
        # Create and upload thumbnail
        create_and_upload_resized_image(
            image, 
            f"{file_name}_thumbnail.jpg", 
            THUMBNAIL_SIZE,
            "Thumbnail"
        )
        
        # Create and upload medium size
        create_and_upload_resized_image(
            image, 
            f"{file_name}_medium.jpg", 
            MEDIUM_SIZE,
            "Medium"
        )
        
        # Create and upload large size
        create_and_upload_resized_image(
            image, 
            f"{file_name}_large.jpg", 
            LARGE_SIZE,
            "Large"
        )
        
        logger.info(f"Successfully processed all versions of {original_key}")
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}", exc_info=True)
        raise


def create_and_upload_resized_image(original_image, key, size, size_name):
    """
    Resize an image and upload to S3.
    
    Args:
        original_image: PIL Image object
        key: S3 key for the resized image
        size: Tuple of (width, height) for resizing
        size_name: Name of the size for logging
    """
    try:
        # Create a copy of the image
        image = original_image.copy()
        
        # Resize using thumbnail method (maintains aspect ratio)
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, 'JPEG', quality=85, optimize=True)
        buffer.seek(0)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=key,
            Body=buffer,
            ContentType='image/jpeg',
            Metadata={
                'original-size': f"{original_image.size[0]}x{original_image.size[1]}",
                'processed-size': f"{image.size[0]}x{image.size[1]}",
                'size-type': size_name
            }
        )
        
        logger.info(f"Uploaded {size_name} version: {key}")
        
    except Exception as e:
        logger.error(f"Error creating {size_name} version: {str(e)}", exc_info=True)
        raise
