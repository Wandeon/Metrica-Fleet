"""Tests for device agent"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add device-agent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'device-agent'))


def test_agent_initialization():
    """Test agent initializes with configuration"""
    from agent import DeviceAgent

    with patch('agent.config') as mock_config:
        mock_config.DEVICE_ID = "test-device-001"
        agent = DeviceAgent()

        assert agent.device_id == "test-device-001"
        assert agent.running is False


def test_agent_configuration_validation():
    """Test configuration validation catches missing values"""
    from config import AgentConfig

    # Save original values
    original_device_id = AgentConfig.DEVICE_ID
    original_api_url = AgentConfig.API_URL

    # Test with missing DEVICE_ID
    AgentConfig.DEVICE_ID = ""
    errors = AgentConfig.validate()
    assert any("DEVICE_ID" in error for error in errors)

    # Restore values
    AgentConfig.DEVICE_ID = original_device_id
    AgentConfig.API_URL = original_api_url


def test_agent_stop():
    """Test agent can be stopped"""
    from agent import DeviceAgent

    with patch('agent.config') as mock_config:
        mock_config.DEVICE_ID = "test-device-001"
        agent = DeviceAgent()
        agent.running = True

        agent.stop()

        assert agent.running is False


def test_signal_handler():
    """Test signal handler stops agent gracefully"""
    from agent import DeviceAgent

    with patch('agent.config') as mock_config:
        mock_config.DEVICE_ID = "test-device-001"
        agent = DeviceAgent()
        agent.running = True

        agent._signal_handler(15, None)  # SIGTERM

        assert agent.running is False
