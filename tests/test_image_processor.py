"""
Unit tests for the image processor Lambda function.
"""

import json
import os
import boto3
from moto import mock_s3
import pytest
from PIL import Image
from io import BytesIO

# Set environment variables for testing
os.environ['PROCESSED_BUCKET'] = 'test-processed-bucket'

# Import after setting environment variables
from image_processor import lambda_handler, process_image, create_and_upload_resized_image


@mock_s3
def test_lambda_handler_success():
    """Test successful image processing through Lambda handler."""
    # Setup
    s3_client = boto3.client('s3', region_name='us-east-1')
    source_bucket = 'test-source-bucket'
    processed_bucket = 'test-processed-bucket'
    
    # Create buckets
    s3_client.create_bucket(Bucket=source_bucket)
    s3_client.create_bucket(Bucket=processed_bucket)
    
    # Create a test image
    image = Image.new('RGB', (1000, 1000), color='red')
    buffer = BytesIO()
    image.save(buffer, 'JPEG')
    buffer.seek(0)
    
    # Upload test image to source bucket
    s3_client.put_object(
        Bucket=source_bucket,
        Key='test-image.jpg',
        Body=buffer.getvalue()
    )
    
    # Create S3 event
    event = {
        'Records': [
            {
                's3': {
                    'bucket': {'name': source_bucket},
                    'object': {'key': 'test-image.jpg'}
                }
            }
        ]
    }
    
    # Execute
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Image processing completed successfully'
    assert body['processed_images'] == 1
    
    # Verify processed images exist
    objects = s3_client.list_objects_v2(Bucket=processed_bucket)
    assert 'Contents' in objects
    assert len(objects['Contents']) == 3  # thumbnail, medium, large


@mock_s3
def test_process_image_creates_all_versions():
    """Test that process_image creates all three image versions."""
    # Setup
    s3_client = boto3.client('s3', region_name='us-east-1')
    processed_bucket = 'test-processed-bucket'
    s3_client.create_bucket(Bucket=processed_bucket)
    
    # Create test image
    image = Image.new('RGB', (2000, 2000), color='blue')
    buffer = BytesIO()
    image.save(buffer, 'JPEG')
    buffer.seek(0)
    image_content = buffer.getvalue()
    
    # Execute
    process_image(image_content, 'folder/test-image.jpg')
    
    # Assert
    objects = s3_client.list_objects_v2(Bucket=processed_bucket)
    keys = [obj['Key'] for obj in objects['Contents']]
    
    assert 'folder/test-image_thumbnail.jpg' in keys
    assert 'folder/test-image_medium.jpg' in keys
    assert 'folder/test-image_large.jpg' in keys


@mock_s3
def test_rgba_to_rgb_conversion():
    """Test that RGBA images are properly converted to RGB."""
    # Setup
    s3_client = boto3.client('s3', region_name='us-east-1')
    processed_bucket = 'test-processed-bucket'
    s3_client.create_bucket(Bucket=processed_bucket)
    
    # Create RGBA image
    image = Image.new('RGBA', (500, 500), color=(255, 0, 0, 128))
    buffer = BytesIO()
    image.save(buffer, 'PNG')
    buffer.seek(0)
    image_content = buffer.getvalue()
    
    # Execute - should not raise exception
    process_image(image_content, 'rgba-image.png')
    
    # Assert - verify images were created
    objects = s3_client.list_objects_v2(Bucket=processed_bucket)
    assert len(objects['Contents']) == 3


@mock_s3
def test_create_and_upload_resized_image():
    """Test individual resized image creation and upload."""
    # Setup
    s3_client = boto3.client('s3', region_name='us-east-1')
    processed_bucket = 'test-processed-bucket'
    s3_client.create_bucket(Bucket=processed_bucket)
    
    # Create test image
    original_image = Image.new('RGB', (1000, 1000), color='green')
    
    # Execute
    create_and_upload_resized_image(
        original_image,
        'test-resized.jpg',
        (200, 200),
        'Test'
    )
    
    # Assert
    response = s3_client.get_object(Bucket=processed_bucket, Key='test-resized.jpg')
    image_data = response['Body'].read()
    
    # Verify image was resized
    resized_image = Image.open(BytesIO(image_data))
    assert resized_image.size[0] <= 200
    assert resized_image.size[1] <= 200


def test_lambda_handler_error_handling():
    """Test error handling in Lambda handler."""
    # Create invalid event
    event = {
        'Records': [
            {
                's3': {
                    'bucket': {'name': 'non-existent-bucket'},
                    'object': {'key': 'non-existent.jpg'}
                }
            }
        ]
    }
    
    # Execute
    response = lambda_handler(event, None)
    
    # Assert
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body
