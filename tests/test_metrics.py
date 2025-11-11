"""Tests for metrics collection"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import psutil
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'device-agent'))

from metrics import SystemMetrics


def test_system_metrics_initialization():
    """Test SystemMetrics initializes correctly"""
    metrics = SystemMetrics()
    assert metrics is not None


def test_collect_basic_metrics():
    """Test basic system metrics collection"""
    metrics = SystemMetrics()
    data = metrics.collect()

    # Verify all required keys exist
    assert "uptime_seconds" in data
    assert "cpu_percent" in data
    assert "memory_percent" in data
    assert "disk_percent" in data
    assert "temperature_celsius" in data
    assert "ip_address" in data
    assert "mac_address" in data

    # Verify types
    assert isinstance(data["uptime_seconds"], (int, float))
    assert isinstance(data["cpu_percent"], (int, float))
    assert isinstance(data["memory_percent"], (int, float))
    assert isinstance(data["disk_percent"], (int, float))

    # Verify reasonable ranges
    assert data["uptime_seconds"] >= 0
    assert 0 <= data["cpu_percent"] <= 100
    assert 0 <= data["memory_percent"] <= 100
    assert 0 <= data["disk_percent"] <= 100


def test_collect_with_custom_temperature_path():
    """Test metrics collection with custom temperature path"""
    metrics = SystemMetrics(temperature_path="/fake/path/temp")
    data = metrics.collect()

    # Should handle missing temperature gracefully
    assert "temperature_celsius" in data
    assert data["temperature_celsius"] is None or data["temperature_celsius"] == 0.0


def test_collect_temperature_from_file():
    """Test temperature reading from file"""
    metrics = SystemMetrics()

    # Mock file reading
    with patch("builtins.open", mock_open(read_data="54321\n")):
        temp = metrics._get_temperature()
        assert temp == 54.3  # Should convert millidegrees to degrees


def test_collect_temperature_file_not_found():
    """Test temperature reading when file doesn't exist"""
    metrics = SystemMetrics()

    # Mock FileNotFoundError
    with patch("builtins.open", side_effect=FileNotFoundError):
        temp = metrics._get_temperature()
        assert temp is None


def test_collect_docker_metrics_docker_available():
    """Test Docker container metrics when Docker is available"""

    # Mock Docker containers
    mock_container_running = Mock()
    mock_container_running.name = "web-server"
    mock_container_running.status = "running"
    mock_container_running.image.tags = ["nginx:latest"]

    mock_container_exited = Mock()
    mock_container_exited.name = "worker"
    mock_container_exited.status = "exited"
    mock_container_exited.image.tags = ["python:3.11"]

    mock_docker_client = Mock()
    mock_docker_client.containers.list.return_value = [
        mock_container_running,
        mock_container_exited
    ]

    metrics = SystemMetrics()
    metrics.docker_client = mock_docker_client

    data = metrics.collect_docker_metrics()

    assert "containers_running" in data
    assert "containers_failed" in data
    assert "container_list" in data

    assert data["containers_running"] == 1
    assert data["containers_failed"] == 1
    assert len(data["container_list"]) == 2

    # Verify container details
    assert data["container_list"][0]["name"] == "web-server"
    assert data["container_list"][0]["status"] == "running"
    assert data["container_list"][0]["image"] == "nginx:latest"


def test_collect_docker_metrics_no_docker():
    """Test Docker metrics when Docker is not available"""
    metrics = SystemMetrics()
    metrics.docker_client = None

    data = metrics.collect_docker_metrics()

    assert data["containers_running"] == 0
    assert data["containers_failed"] == 0
    assert data["container_list"] == []


def test_collect_docker_metrics_docker_exception():
    """Test Docker metrics when Docker raises an exception"""
    mock_docker_client = Mock()
    mock_docker_client.containers.list.side_effect = Exception("Docker daemon not running")

    metrics = SystemMetrics()
    metrics.docker_client = mock_docker_client

    data = metrics.collect_docker_metrics()

    # Should handle exception gracefully
    assert data["containers_running"] == 0
    assert data["containers_failed"] == 0
    assert data["container_list"] == []


def test_collect_docker_metrics_container_no_tags():
    """Test Docker metrics when container image has no tags"""

    mock_container = Mock()
    mock_container.name = "test-container"
    mock_container.status = "running"
    mock_container.image.tags = []  # No tags

    mock_docker_client = Mock()
    mock_docker_client.containers.list.return_value = [mock_container]

    metrics = SystemMetrics()
    metrics.docker_client = mock_docker_client

    data = metrics.collect_docker_metrics()

    assert data["container_list"][0]["image"] == "unknown"


def test_network_interface_selection():
    """Test network interface selection prefers non-loopback interfaces"""
    metrics = SystemMetrics()

    # Mock psutil.net_if_addrs
    mock_addrs = {
        "lo": [
            MagicMock(
                family=2,  # AF_INET
                address="127.0.0.1",
            )
        ],
        "eth0": [
            MagicMock(
                family=2,  # AF_INET
                address="192.168.1.100",
            ),
            MagicMock(
                family=17,  # AF_PACKET (MAC)
                address="b8:27:eb:aa:bb:cc",
            )
        ]
    }

    with patch("psutil.net_if_addrs", return_value=mock_addrs):
        ip, mac = metrics._get_network_info()

        assert ip == "192.168.1.100"
        assert mac == "b8:27:eb:aa:bb:cc"


def test_network_info_only_loopback():
    """Test network info when only loopback is available"""
    metrics = SystemMetrics()

    # Mock psutil.net_if_addrs with only loopback
    mock_addrs = {
        "lo": [
            MagicMock(
                family=2,  # AF_INET
                address="127.0.0.1",
            )
        ]
    }

    with patch("psutil.net_if_addrs", return_value=mock_addrs):
        ip, mac = metrics._get_network_info()

        # Should fall back to loopback if nothing else available
        assert ip == "127.0.0.1"
        assert mac is None or mac == "00:00:00:00:00:00"


def test_network_info_exception():
    """Test network info handles exceptions gracefully"""
    metrics = SystemMetrics()

    with patch("psutil.net_if_addrs", side_effect=Exception("Network error")):
        ip, mac = metrics._get_network_info()

        assert ip is None
        assert mac is None


def test_collect_with_uptime_from_proc():
    """Test uptime collection using /proc/uptime"""
    metrics = SystemMetrics()

    # Mock /proc/uptime file
    with patch("builtins.open", mock_open(read_data="12345.67 98765.43\n")):
        uptime = metrics._get_uptime()
        assert uptime == 12345


def test_collect_uptime_fallback_to_psutil():
    """Test uptime falls back to psutil if /proc/uptime unavailable"""
    metrics = SystemMetrics()

    # Mock /proc/uptime file not found
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("psutil.boot_time", return_value=1000.0):
            with patch("time.time", return_value=2000.0):
                uptime = metrics._get_uptime()
                assert uptime == 1000


def test_integration_collect_all_metrics():
    """Integration test: collect all metrics at once"""
    metrics = SystemMetrics()

    # Collect system metrics
    system_data = metrics.collect()

    # Collect Docker metrics
    docker_data = metrics.collect_docker_metrics()

    # Verify both work and can be combined
    combined = {**system_data, **docker_data}

    # System metrics
    assert "cpu_percent" in combined
    assert "memory_percent" in combined
    assert "disk_percent" in combined

    # Docker metrics
    assert "containers_running" in combined
    assert "containers_failed" in combined

    # No key conflicts
    assert len(combined) >= 10
