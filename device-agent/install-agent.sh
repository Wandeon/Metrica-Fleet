#!/bin/bash
set -e

# Metrica Fleet Device Agent Installation Script
# This script installs the agent as a systemd service

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/opt/metrica-agent"
CONFIG_DIR="/etc/metrica-agent"
DATA_DIR="/var/lib/metrica-agent"
SERVICE_FILE="metrica-agent.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_FILE}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Metrica Fleet Device Agent - Installer"
echo "========================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${GREEN}✓${NC} Running as root"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is installed"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python3 is not installed${NC}"
    echo "Please install Python3: sudo apt-get install python3 python3-pip"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python3 is installed ($(python3 --version))"

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}WARNING: pip3 is not installed, installing...${NC}"
    apt-get update && apt-get install -y python3-pip
fi

echo -e "${GREEN}✓${NC} pip3 is installed"

echo ""
echo "Creating directory structure..."

# Create directories
mkdir -p "${INSTALL_DIR}"
mkdir -p "${CONFIG_DIR}"
mkdir -p "${DATA_DIR}"
mkdir -p "${DATA_DIR}/safe-mode"

echo -e "${GREEN}✓${NC} Created ${INSTALL_DIR}"
echo -e "${GREEN}✓${NC} Created ${CONFIG_DIR}"
echo -e "${GREEN}✓${NC} Created ${DATA_DIR}"

echo ""
echo "Copying agent files..."

# Copy agent files
cp -r "${SCRIPT_DIR}"/*.py "${INSTALL_DIR}/"
cp -r "${SCRIPT_DIR}"/safe_mode "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/requirements.txt" "${INSTALL_DIR}/"

echo -e "${GREEN}✓${NC} Copied agent files to ${INSTALL_DIR}"

echo ""
echo "Installing Python dependencies..."

# Install Python requirements
pip3 install -r "${INSTALL_DIR}/requirements.txt" --quiet

echo -e "${GREEN}✓${NC} Python dependencies installed"

echo ""
echo "Setting up configuration..."

# Copy environment file if it doesn't exist
if [ ! -f "${CONFIG_DIR}/agent.env" ]; then
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
        cp "${SCRIPT_DIR}/.env.example" "${CONFIG_DIR}/agent.env"
        echo -e "${GREEN}✓${NC} Created ${CONFIG_DIR}/agent.env from template"
        echo -e "${YELLOW}⚠${NC}  You MUST edit ${CONFIG_DIR}/agent.env before starting the service"
    else
        echo -e "${RED}ERROR: .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC}  Configuration file ${CONFIG_DIR}/agent.env already exists, not overwriting"
fi

# Set correct paths in config
sed -i "s|REPO_PATH=.*|REPO_PATH=/opt/metrica-fleet|g" "${CONFIG_DIR}/agent.env"
sed -i "s|DATA_DIR=.*|DATA_DIR=/var/lib/metrica-agent|g" "${CONFIG_DIR}/agent.env"

echo ""
echo "Installing systemd service..."

# Copy systemd service file
cp "${SCRIPT_DIR}/${SERVICE_FILE}" "${SERVICE_PATH}"

echo -e "${GREEN}✓${NC} Installed service file to ${SERVICE_PATH}"

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}✓${NC} Reloaded systemd"

# Enable service
systemctl enable metrica-agent

echo -e "${GREEN}✓${NC} Enabled metrica-agent service"

echo ""
echo "========================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit the configuration file:"
echo "   sudo nano ${CONFIG_DIR}/agent.env"
echo ""
echo "   Required settings:"
echo "   - DEVICE_ID: Unique identifier for this device"
echo "   - DEVICE_ROLE: Role of this device (e.g., audio-player)"
echo "   - API_URL: URL of your Overlord server"
echo "   - API_KEY: API key for authentication"
echo ""
echo "2. Start the service:"
echo "   sudo systemctl start metrica-agent"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status metrica-agent"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u metrica-agent -f"
echo ""
echo "5. View real-time logs (last 20 lines):"
echo "   sudo journalctl -u metrica-agent -f --lines=20"
echo ""
echo "For more information, see the documentation."
echo ""
