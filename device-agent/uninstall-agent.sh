#!/bin/bash
set -e

# Metrica Fleet Device Agent Uninstallation Script

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

echo "=========================================="
echo "Metrica Fleet Device Agent - Uninstaller"
echo "=========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${GREEN}✓${NC} Running as root"

# Confirm uninstallation
echo -e "${YELLOW}WARNING: This will remove the Metrica Fleet Device Agent${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Stop the service if running
if systemctl is-active --quiet metrica-agent; then
    echo "Stopping metrica-agent service..."
    systemctl stop metrica-agent
    echo -e "${GREEN}✓${NC} Service stopped"
else
    echo -e "${YELLOW}⚠${NC}  Service is not running"
fi

# Disable the service if enabled
if systemctl is-enabled --quiet metrica-agent 2>/dev/null; then
    echo "Disabling metrica-agent service..."
    systemctl disable metrica-agent
    echo -e "${GREEN}✓${NC} Service disabled"
else
    echo -e "${YELLOW}⚠${NC}  Service is not enabled"
fi

# Remove systemd service file
if [ -f "${SERVICE_PATH}" ]; then
    echo "Removing systemd service file..."
    rm "${SERVICE_PATH}"
    systemctl daemon-reload
    echo -e "${GREEN}✓${NC} Service file removed"
else
    echo -e "${YELLOW}⚠${NC}  Service file not found"
fi

# Remove installation directory
if [ -d "${INSTALL_DIR}" ]; then
    echo "Removing installation directory..."
    rm -rf "${INSTALL_DIR}"
    echo -e "${GREEN}✓${NC} Removed ${INSTALL_DIR}"
else
    echo -e "${YELLOW}⚠${NC}  Installation directory not found"
fi

# Ask about configuration and data
echo ""
read -p "Remove configuration directory ${CONFIG_DIR}? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy]es$ ]]; then
    if [ -d "${CONFIG_DIR}" ]; then
        rm -rf "${CONFIG_DIR}"
        echo -e "${GREEN}✓${NC} Removed ${CONFIG_DIR}"
    else
        echo -e "${YELLOW}⚠${NC}  Configuration directory not found"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Kept configuration directory ${CONFIG_DIR}"
fi

echo ""
read -p "Remove data directory ${DATA_DIR}? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy]es$ ]]; then
    if [ -d "${DATA_DIR}" ]; then
        rm -rf "${DATA_DIR}"
        echo -e "${GREEN}✓${NC} Removed ${DATA_DIR}"
    else
        echo -e "${YELLOW}⚠${NC}  Data directory not found"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Kept data directory ${DATA_DIR}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo "=========================================="
echo ""
echo "The Metrica Fleet Device Agent has been removed."
echo ""
