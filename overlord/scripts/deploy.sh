#!/bin/bash
set -euo pipefail

# Metrica Fleet Overlord Deployment Script
# Deploys the Overlord system to VPS-01

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLORD_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   Metrica Fleet Overlord Deployment                  ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  This script should not be run as root"
   exit 1
fi

# Check for required tools
echo "🔍 Checking dependencies..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose is not installed."; exit 1; }

# Determine docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

echo "✅ Dependencies OK"
echo ""

# Check for .env file
if [ ! -f "$OVERLORD_DIR/.env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f "$OVERLORD_DIR/.env.example" ]; then
        cp "$OVERLORD_DIR/.env.example" "$OVERLORD_DIR/.env"
        echo "📝 Please edit $OVERLORD_DIR/.env with your configuration"
        echo "   Pay special attention to:"
        echo "   - POSTGRES_PASSWORD"
        echo "   - GRAFANA_ADMIN_PASSWORD"
        echo "   - API_SECRET_KEY"
        echo ""
        read -p "Press Enter after updating .env to continue..."
    else
        echo "❌ .env.example not found. Cannot continue."
        exit 1
    fi
fi

# Source .env file
set -a
source "$OVERLORD_DIR/.env"
set +a

echo "🔧 Configuration loaded"
echo ""

# Create required directories
echo "📁 Creating directories..."
mkdir -p "$OVERLORD_DIR/prometheus/targets"
mkdir -p "$OVERLORD_DIR/grafana/dashboards"
mkdir -p "$OVERLORD_DIR/grafana/provisioning/datasources"
mkdir -p "$OVERLORD_DIR/grafana/provisioning/dashboards"
mkdir -p "$OVERLORD_DIR/loki"
mkdir -p "$OVERLORD_DIR/alertmanager"
mkdir -p "$OVERLORD_DIR/nginx/ssl"
mkdir -p "$OVERLORD_DIR/init-db"

echo "✅ Directories created"
echo ""

# Pull latest images
echo "📥 Pulling Docker images..."
cd "$OVERLORD_DIR"
$DOCKER_COMPOSE pull

echo "✅ Images pulled"
echo ""

# Build custom images
echo "🔨 Building custom images..."
$DOCKER_COMPOSE build

echo "✅ Images built"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE down

echo "✅ Containers stopped"
echo ""

# Start services
echo "🚀 Starting Overlord services..."
$DOCKER_COMPOSE up -d

echo "✅ Services started"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

services=("postgres" "prometheus" "grafana" "loki" "fleet-api")
all_healthy=true

for service in "${services[@]}"; do
    if $DOCKER_COMPOSE ps | grep -q "$service.*running"; then
        echo "  ✅ $service: running"
    else
        echo "  ❌ $service: not running"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║   Overlord Deployment Complete! 🎉                    ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Access your services:"
    echo "  • Fleet Dashboard:  http://localhost:${DASHBOARD_PORT:-3001}"
    echo "  • Fleet API:        http://localhost:${API_PORT:-8080}"
    echo "  • Grafana:          http://localhost:${GRAFANA_PORT:-3000}"
    echo "  • Prometheus:       http://localhost:9090"
    echo ""
    echo "📚 API Documentation: http://localhost:${API_PORT:-8080}/docs"
    echo ""
    echo "🔐 Default Credentials:"
    echo "  • Grafana: admin / ${GRAFANA_ADMIN_PASSWORD}"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Change default passwords"
    echo "  2. Configure alerting (email, Slack)"
    echo "  3. Set up SSL certificates for production"
    echo "  4. Register your first Pi device"
    echo ""
    echo "📖 View logs: $DOCKER_COMPOSE logs -f"
    echo "🛑 Stop services: $DOCKER_COMPOSE down"
    echo ""
else
    echo "⚠️  Some services failed to start. Check logs with:"
    echo "   $DOCKER_COMPOSE logs"
    exit 1
fi
