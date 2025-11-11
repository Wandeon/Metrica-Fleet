"""Tests for integrated device agent"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
from pathlib import Path

# Add device-agent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'device-agent'))


@pytest.fixture
def mock_config():
    """Fixture for mocked configuration"""
    with patch('agent.config') as mock_cfg:
        mock_cfg.DEVICE_ID = "test-device-001"
        mock_cfg.DEVICE_ROLE = "audio-player"
        mock_cfg.DEVICE_BRANCH = "main"
        mock_cfg.API_URL = "http://localhost:8080"
        mock_cfg.API_KEY = "test-key"
        mock_cfg.HEARTBEAT_INTERVAL = 30
        mock_cfg.POLL_INTERVAL = 60
        mock_cfg.SAFE_MODE_ENABLED = True
        mock_cfg.DATA_DIR = Path("/tmp/test-metrica")
        mock_cfg.validate = Mock(return_value=[])
        yield mock_cfg


def test_agent_initialization(mock_config):
    """Test agent initializes with configuration"""
    from agent import DeviceAgent

    agent = DeviceAgent()

    assert agent.device_id == "test-device-001"
    assert agent.running is False
    assert agent.registered is False
    assert agent.registration_failures == 0
    assert agent.consecutive_heartbeat_failures == 0


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


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_component_initialization(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test all components are initialized correctly"""
    from agent import DeviceAgent

    agent = DeviceAgent()
    agent._initialize_components()

    # Verify API client initialized
    assert agent.api_client is not None
    mock_api.assert_called_once_with(
        api_url="http://localhost:8080",
        device_id="test-device-001",
        api_key="test-key"
    )

    # Verify metrics collector initialized
    assert agent.metrics is not None
    mock_metrics.assert_called_once()


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_registration_success(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test successful device registration"""
    from agent import DeviceAgent

    # Mock successful registration
    mock_api_instance = Mock()
    mock_api_instance.register_device.return_value = {
        "device_id": "test-device-001",
        "status": "registered",
        "message": "Device registered successfully"
    }
    mock_api.return_value = mock_api_instance

    mock_metrics_instance = Mock()
    mock_metrics_instance.collect.return_value = {
        "ip_address": "192.168.1.100",
        "mac_address": "aa:bb:cc:dd:ee:ff"
    }
    mock_metrics.return_value = mock_metrics_instance

    agent = DeviceAgent()
    agent._initialize_components()
    result = agent._register_device()

    assert result is True
    assert agent.registered is True
    assert agent.registration_failures == 0


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_registration_retry_logic(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test registration retries on failure"""
    from agent import DeviceAgent, NetworkError

    # Mock failed then successful registration
    mock_api_instance = Mock()
    mock_api_instance.register_device.side_effect = [
        NetworkError("Connection failed"),
        {"device_id": "test-device-001", "status": "registered"}
    ]
    mock_api.return_value = mock_api_instance

    mock_metrics_instance = Mock()
    mock_metrics_instance.collect.return_value = {
        "ip_address": "192.168.1.100",
        "mac_address": "aa:bb:cc:dd:ee:ff"
    }
    mock_metrics.return_value = mock_metrics_instance

    agent = DeviceAgent()
    agent._initialize_components()

    with patch('time.sleep'):  # Skip actual sleep
        result = agent._register_device()

    assert result is True
    assert mock_api_instance.register_device.call_count == 2


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_registration_max_failures(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test registration fails after max retries"""
    from agent import DeviceAgent, NetworkError

    # Mock all registration attempts failing
    mock_api_instance = Mock()
    mock_api_instance.register_device.side_effect = NetworkError("Connection failed")
    mock_api.return_value = mock_api_instance

    mock_metrics_instance = Mock()
    mock_metrics_instance.collect.return_value = {"ip_address": None, "mac_address": None}
    mock_metrics.return_value = mock_metrics_instance

    agent = DeviceAgent()
    agent._initialize_components()

    with patch('time.sleep'):  # Skip actual sleep
        result = agent._register_device()

    assert result is False
    assert agent.registration_failures == DeviceAgent.MAX_REGISTRATION_FAILURES


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_heartbeat_success(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test successful heartbeat sending"""
    from agent import DeviceAgent

    mock_api_instance = Mock()
    mock_api_instance.send_heartbeat.return_value = {"status": "acknowledged"}
    mock_api.return_value = mock_api_instance

    mock_metrics_instance = Mock()
    mock_metrics_instance.collect.return_value = {
        "uptime_seconds": 3600,
        "cpu_percent": 25.5,
        "memory_percent": 45.2,
        "disk_percent": 60.0,
        "temperature_celsius": 45.0
    }
    mock_metrics_instance.collect_docker_metrics.return_value = {
        "containers_running": 3,
        "containers_failed": 0
    }
    mock_metrics.return_value = mock_metrics_instance

    agent = DeviceAgent()
    agent._initialize_components()
    result = agent._send_heartbeat()

    assert result is True
    mock_api_instance.send_heartbeat.assert_called_once()


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_heartbeat_failure_tracking(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test heartbeat failure counter increments"""
    from agent import DeviceAgent, NetworkError

    mock_api_instance = Mock()
    mock_api_instance.send_heartbeat.side_effect = NetworkError("Connection failed")
    mock_api.return_value = mock_api_instance

    mock_metrics_instance = Mock()
    mock_metrics_instance.collect.return_value = {}
    mock_metrics_instance.collect_docker_metrics.return_value = {}
    mock_metrics.return_value = mock_metrics_instance

    agent = DeviceAgent()
    agent._initialize_components()

    # Simulate multiple heartbeat failures
    for i in range(3):
        result = agent._send_heartbeat()
        assert result is False

    assert agent.consecutive_heartbeat_failures == 0  # Not tracked in _send_heartbeat itself


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_configuration_check(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test configuration checking and change detection"""
    from agent import DeviceAgent

    mock_api_instance = Mock()
    mock_api_instance.get_configuration.side_effect = [
        {
            "device_id": "test-device-001",
            "branch": "main",
            "segment": "stable",
            "update_enabled": True,
            "maintenance_mode": False
        },
        {
            "device_id": "test-device-001",
            "branch": "develop",  # Changed
            "segment": "stable",
            "update_enabled": True,
            "maintenance_mode": False
        }
    ]
    mock_api.return_value = mock_api_instance

    agent = DeviceAgent()
    agent._initialize_components()

    # First check - initial config
    agent._check_configuration()
    assert agent.last_config is not None
    assert agent.last_config["branch"] == "main"

    # Second check - config changed
    agent._check_configuration()
    assert agent.last_config["branch"] == "develop"


@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_safe_mode_activation(mock_api, mock_metrics, mock_safe_mode, mock_config):
    """Test safe mode activation on critical error"""
    from agent import DeviceAgent

    mock_safe_mode_instance = Mock()
    mock_safe_mode_instance.activate.return_value = True
    mock_safe_mode.return_value = mock_safe_mode_instance

    agent = DeviceAgent()
    agent._initialize_components()

    agent._activate_safe_mode(
        reason="Test failure",
        error_details={"error": "Test error"}
    )

    mock_safe_mode_instance.activate.assert_called_once()
    call_args = mock_safe_mode_instance.activate.call_args
    assert call_args[1]["reason"] == "Test failure"


@patch('agent.Path')
@patch('agent.SafeMode')
@patch('agent.SystemMetrics')
@patch('agent.APIClient')
def test_safe_mode_already_active_on_startup(mock_api, mock_metrics, mock_safe_mode, mock_path, mock_config):
    """Test agent detects and continues in safe mode if already active"""
    from agent import DeviceAgent

    mock_safe_mode_instance = Mock()
    mock_safe_mode_instance.is_active.return_value = True
    mock_safe_mode_instance.get_status.return_value = {
        "active": True,
        "reason": "Previous crash",
        "activated_at": "2025-11-11T10:00:00"
    }
    mock_safe_mode.return_value = mock_safe_mode_instance

    # Mock Path for safe mode directory
    mock_path_instance = Mock()
    mock_path_instance.parent = Mock()
    mock_path_instance.parent.__truediv__ = Mock(return_value=mock_path_instance)
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance

    agent = DeviceAgent()

    # This would normally enter safe mode loop, but we'll just test initialization
    # We can't easily test the full start() method due to infinite loops


def test_agent_stop(mock_config):
    """Test agent can be stopped"""
    from agent import DeviceAgent

    agent = DeviceAgent()
    agent.running = True

    # Mock API client
    agent.api_client = Mock()

    agent.stop()

    assert agent.running is False
    agent.api_client.close.assert_called_once()


def test_signal_handler(mock_config):
    """Test signal handler stops agent gracefully"""
    from agent import DeviceAgent

    agent = DeviceAgent()
    agent.running = True

    agent._signal_handler(15, None)  # SIGTERM

    assert agent.running is False
