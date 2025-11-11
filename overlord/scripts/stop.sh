#!/bin/bash
set -euo pipefail

# Stop Overlord services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLORD_DIR="$(dirname "$SCRIPT_DIR")"

echo "🛑 Stopping Overlord services..."

cd "$OVERLORD_DIR"

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose down
else
    docker compose down
fi

echo "✅ Overlord services stopped"
