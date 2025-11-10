#!/bin/bash
set -euo pipefail

# View Overlord logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLORD_DIR="$(dirname "$SCRIPT_DIR")"

cd "$OVERLORD_DIR"

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# If service name provided, show logs for that service
if [ $# -eq 1 ]; then
    echo "📖 Logs for $1..."
    $DOCKER_COMPOSE logs -f --tail=100 "$1"
else
    echo "📖 All service logs..."
    $DOCKER_COMPOSE logs -f --tail=50
fi
