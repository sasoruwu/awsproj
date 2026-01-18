#!/bin/bash

# Script to run tests locally
# Requires Python 3.11+ and pip

set -e

echo "Setting up test environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo "Installing test dependencies..."
pip install -q -r tests/requirements.txt

# Add src to PYTHONPATH so tests can import modules
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run tests
echo "Running tests..."
pytest tests/ -v --tb=short

echo "Tests completed!"
