#!/bin/bash
set -euo pipefail

# Update Overlord services with zero-downtime

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLORD_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔄 Updating Overlord services..."

cd "$OVERLORD_DIR"

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Pull latest changes
echo "📥 Pulling latest changes from Git..."
git pull origin main

# Pull new images
echo "📥 Pulling new Docker images..."
$DOCKER_COMPOSE pull

# Build updated images
echo "🔨 Building updated images..."
$DOCKER_COMPOSE build

# Rolling update
echo "🔄 Performing rolling update..."
$DOCKER_COMPOSE up -d --no-deps --build

echo "✅ Update complete"
echo ""
echo "📖 View logs: $DOCKER_COMPOSE logs -f"
