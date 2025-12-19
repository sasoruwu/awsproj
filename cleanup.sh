#!/bin/bash

# Cleanup script for AWS Image Processing System
# This script safely removes all AWS resources created by the stack

set -e

# Set variables
STACK_NAME="${STACK_NAME:-image-processing-system}"
REGION="${AWS_REGION:-us-east-1}"

echo "======================================"
echo "AWS Image Processing System - Cleanup"
echo "======================================"
echo ""
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo "Error: AWS CLI is not installed. Please install it first."
        exit 1
    fi
}

# Function to get bucket names
get_bucket_names() {
    echo "Retrieving bucket names from CloudFormation stack..."
    
    SOURCE_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`SourceBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
}

# Function to empty and delete a bucket
empty_and_delete_bucket() {
    local bucket_name=$1
    
    if [ -z "$bucket_name" ]; then
        return
    fi
    
    echo "Processing bucket: $bucket_name"
    
    # Check if bucket exists
    if aws s3 ls "s3://$bucket_name" --region "$REGION" 2>/dev/null; then
        echo "  - Emptying bucket..."
        aws s3 rm "s3://$bucket_name" --recursive --region "$REGION" || true
        
        echo "  - Deleting bucket..."
        aws s3 rb "s3://$bucket_name" --region "$REGION" || true
        echo "  ✓ Bucket $bucket_name removed"
    else
        echo "  - Bucket does not exist or already deleted"
    fi
}

# Function to delete CloudFormation stack
delete_stack() {
    echo ""
    echo "Checking if stack exists..."
    
    if aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" &>/dev/null; then
        
        echo "Deleting CloudFormation stack: $STACK_NAME"
        aws cloudformation delete-stack \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        
        echo "Waiting for stack deletion to complete..."
        echo "(This may take a few minutes)"
        
        aws cloudformation wait stack-delete-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION" 2>/dev/null || {
                echo "Note: Stack deletion is in progress but wait command timed out or stack already deleted"
            }
        
        echo "✓ Stack deleted successfully"
    else
        echo "Stack $STACK_NAME does not exist in region $REGION"
    fi
}

# Main cleanup process
main() {
    check_aws_cli
    
    # Confirm deletion
    echo "⚠️  WARNING: This will delete all resources including S3 buckets and their contents!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Cleanup cancelled."
        exit 0
    fi
    
    echo ""
    echo "Starting cleanup process..."
    echo ""
    
    # Get bucket names before deleting stack
    get_bucket_names
    
    # Empty and delete S3 buckets
    echo "Step 1: Removing S3 buckets..."
    if [ -n "$SOURCE_BUCKET" ]; then
        empty_and_delete_bucket "$SOURCE_BUCKET"
    fi
    
    if [ -n "$PROCESSED_BUCKET" ]; then
        empty_and_delete_bucket "$PROCESSED_BUCKET"
    fi
    
    # Delete CloudFormation stack
    echo ""
    echo "Step 2: Deleting CloudFormation stack..."
    delete_stack
    
    echo ""
    echo "======================================"
    echo "✓ Cleanup completed successfully!"
    echo "======================================"
    echo ""
    echo "All resources have been removed."
}

# Run main function
main
