#!/bin/bash
# Pipelines startup script
# Last updated: 2025-12-31
#
# This script recreates the pipelines container.
# Pipelines code is mounted from ~/openwebui-pipelines or cloned from GitHub.

DOCKER="/Applications/Docker.app/Contents/Resources/bin/docker"
PIPELINES_DIR="$HOME/openwebui-pipelines"

# Clone pipelines repo if not present
if [ ! -d "$PIPELINES_DIR" ]; then
  echo "Cloning pipelines from GitHub..."
  git clone https://github.com/DonUsingGit/openwebui-pipelines.git "$PIPELINES_DIR"
fi

# Stop and remove existing container if it exists
$DOCKER stop pipelines 2>/dev/null
$DOCKER rm pipelines 2>/dev/null

# Start pipelines container
$DOCKER run -d -p 9099:9099 \
  --add-host=host.docker.internal:host-gateway \
  -v "$PIPELINES_DIR:/app/pipelines" \
  --name pipelines \
  --restart always \
  ghcr.io/open-webui/pipelines:main

echo "Pipelines started at http://localhost:9099"
