#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define variables
IMAGE_NAME="finance-dashboard"
DOCKER_HUB_USERNAME="$1"
VERSION="$2"

# Function to display help
show_help() {
    echo "SEC Filings Dashboard Docker Publisher"
    echo ""
    echo "Usage: $0 <docker-hub-username> [version]"
    echo ""
    echo "Arguments:"
    echo "  docker-hub-username   Your Docker Hub username"
    echo "  version               (Optional) Version tag for the image. Defaults to 'latest'"
    echo ""
    echo "Examples:"
    echo "  $0 yourusername                # Pushes as yourusername/finance-dashboard:latest"
    echo "  $0 yourusername 1.0.0          # Pushes as yourusername/finance-dashboard:1.0.0"
    echo ""
}

# Check if help was requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check if Docker Hub username was provided
if [ -z "$DOCKER_HUB_USERNAME" ]; then
    echo "Error: Docker Hub username is required"
    echo ""
    show_help
    exit 1
fi

# If version is not provided, use 'latest'
if [ -z "$VERSION" ]; then
    VERSION="latest"
    echo "No version specified, using 'latest'"
fi

FULL_IMAGE_NAME="$DOCKER_HUB_USERNAME/$IMAGE_NAME:$VERSION"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if user is logged in to Docker Hub
echo "Checking Docker Hub login status..."
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "You are not logged in to Docker Hub. Please log in:"
    docker login
fi

echo "Building Docker image: $FULL_IMAGE_NAME"
docker build -t "$FULL_IMAGE_NAME" .

echo "Pushing Docker image to Docker Hub..."
docker push "$FULL_IMAGE_NAME"

echo "===================================================="
echo "Success! Image $FULL_IMAGE_NAME has been pushed to Docker Hub"
echo ""
echo "Others can now run your dashboard with:"
echo "docker run -p 8080:8080 -p 8002:8002 $FULL_IMAGE_NAME"
echo ""
echo "Or with Docker Compose using the configuration in README.md"
echo "====================================================" 