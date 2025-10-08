#!/bin/bash
# Script to build and push Docker images for the singleuser-release workflow

# Build the Docker image
docker compose build

# Get the tag stub from docker-compose.yaml
TAG_STUB=$(eval "echo \"$(cat docker-compose.yaml | grep image: | awk '{ print $2 }' | grep singleuser)\"")

# Create target and latest tags
TARGET_TAG="${TAG_STUB}-$(git rev-parse --short HEAD)"
LATEST_TAG="${TAG_STUB}-latest"

# Output tags for GitHub Actions
echo "target_tag=${TARGET_TAG}" >> $GITHUB_OUTPUT
echo "latest_tag=${LATEST_TAG}" >> $GITHUB_OUTPUT

# Tag and push the images
docker tag $TAG_STUB $TARGET_TAG
docker tag $TAG_STUB $LATEST_TAG
docker push $TARGET_TAG
docker push $LATEST_TAG
