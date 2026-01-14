#!/bin/bash
# Open WebUI startup script - preserves all configuration
# Last updated: 2025-12-31
#
# This script recreates the open-webui container with correct settings.
# API keys are loaded from ~/.api_keys/api_keys
#
# Usage: ./open-webui-start.sh

DOCKER="/Applications/Docker.app/Contents/Resources/bin/docker"

# Load API keys from file
source ~/.api_keys/api_keys

# Stop and remove existing container if it exists
$DOCKER stop open-webui 2>/dev/null
$DOCKER rm open-webui 2>/dev/null

# Start Open WebUI with correct configuration
$DOCKER run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OPENAI_API_BASE_URL=http://host.docker.internal:9099 \
  -e OPENAI_API_KEY=0p3n-w3bu! \
  -e AUDIO_TTS_ENGINE=openai \
  -e AUDIO_TTS_OPENAI_API_BASE_URL=https://api.openai.com/v1 \
  -e AUDIO_TTS_OPENAI_API_KEY=$OPENAI_API_KEY \
  -e AUDIO_TTS_VOICE=nova \
  -e AUDIO_TTS_MODEL=tts-1 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main

echo "Open WebUI started at http://localhost:3000"
echo "For HTTPS with mic access: https://macbook-pro.local"
