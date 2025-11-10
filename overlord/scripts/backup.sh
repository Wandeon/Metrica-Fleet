#!/bin/bash
set -euo pipefail

# Backup Overlord data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLORD_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$OVERLORD_DIR/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "💾 Starting Overlord backup..."

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

cd "$OVERLORD_DIR"

# Backup PostgreSQL database
echo "📦 Backing up PostgreSQL database..."
$DOCKER_COMPOSE exec -T postgres pg_dump -U fleet fleet | gzip > "$BACKUP_DIR/postgres_${TIMESTAMP}.sql.gz"

# Backup Prometheus data
echo "📦 Backing up Prometheus data..."
tar -czf "$BACKUP_DIR/prometheus_${TIMESTAMP}.tar.gz" -C "$OVERLORD_DIR" prometheus/

# Backup Grafana data
echo "📦 Backing up Grafana data..."
tar -czf "$BACKUP_DIR/grafana_${TIMESTAMP}.tar.gz" -C "$OVERLORD_DIR" grafana/

# Backup configuration files
echo "📦 Backing up configuration..."
tar -czf "$BACKUP_DIR/config_${TIMESTAMP}.tar.gz" \
    "$OVERLORD_DIR/.env" \
    "$OVERLORD_DIR/docker-compose.yml" \
    "$OVERLORD_DIR/prometheus/" \
    "$OVERLORD_DIR/loki/" \
    "$OVERLORD_DIR/alertmanager/"

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR"
echo ""
echo "📦 Backup files:"
ls -lh "$BACKUP_DIR"/*_${TIMESTAMP}*
