"""Tests for safe mode management"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add device-agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'device-agent'))

from safe_mode import SafeMode


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def safe_mode_dir(temp_dir):
    """Create safe mode directory structure"""
    safe_mode_path = temp_dir / "safe_mode"
    safe_mode_path.mkdir()

    # Create docker-compose.yml
    compose_file = safe_mode_path / "docker-compose.yml"
    compose_file.write_text("version: '3.8'\nservices:\n  test: {}\n")

    # Create status-page directory
    status_page = safe_mode_path / "status-page"
    status_page.mkdir()

    return safe_mode_path


@pytest.fixture
def state_file(temp_dir):
    """Create temporary state file path"""
    return temp_dir / "safe-mode.lock"


@pytest.fixture
def safe_mode(safe_mode_dir, state_file):
    """Create SafeMode instance"""
    return SafeMode(safe_mode_path=safe_mode_dir, state_file=state_file)


def test_safe_mode_initialization(safe_mode_dir, state_file):
    """Test SafeMode initializes correctly"""
    sm = SafeMode(safe_mode_path=safe_mode_dir, state_file=state_file)

    assert sm.safe_mode_path == safe_mode_dir
    assert sm.compose_file == safe_mode_dir / "docker-compose.yml"
    assert sm.state_file == state_file


def test_safe_mode_initialization_no_compose_file(temp_dir, state_file):
    """Test SafeMode raises error if docker-compose.yml doesn't exist"""
    with pytest.raises(FileNotFoundError):
        SafeMode(safe_mode_path=temp_dir, state_file=state_file)


@patch('subprocess.run')
def test_activate_safe_mode(mock_run, safe_mode):
    """Test activating safe mode"""
    # Mock subprocess calls
    mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

    reason = "Application failure"
    error_details = {"error": "Connection timeout", "code": 500}

    result = safe_mode.activate(reason=reason, error_details=error_details)

    assert result is True
    assert safe_mode.state_file.exists()

    # Verify state file contents
    with open(safe_mode.state_file) as f:
        state = json.load(f)

    assert state["active"] is True
    assert state["reason"] == reason
    assert state["error_details"] == error_details
    assert "activated_at" in state

    # Verify subprocess was called correctly
    assert mock_run.call_count == 2  # docker compose down + up


@patch('subprocess.run')
def test_activate_safe_mode_docker_failure(mock_run, safe_mode):
    """Test safe mode activation when docker command fails"""
    # Mock docker compose up to fail
    mock_run.return_value = Mock(returncode=1, stderr="Docker error", stdout="")

    result = safe_mode.activate(reason="Test failure")

    assert result is False


@patch('subprocess.run')
def test_deactivate_safe_mode(mock_run, safe_mode):
    """Test deactivating safe mode"""
    # First activate safe mode
    mock_run.return_value = Mock(returncode=0, stderr="", stdout="")
    safe_mode.activate(reason="Test")

    # Now deactivate
    result = safe_mode.deactivate()

    assert result is True
    assert not safe_mode.state_file.exists()


@patch('subprocess.run')
def test_deactivate_safe_mode_docker_failure(mock_run, safe_mode):
    """Test deactivation when docker command fails"""
    # Create state file manually
    safe_mode.state_file.write_text(json.dumps({"active": True}))

    # Mock docker compose down to fail
    mock_run.return_value = Mock(returncode=1, stderr="Docker error", stdout="")

    result = safe_mode.deactivate()

    assert result is False
    # State file should still exist
    assert safe_mode.state_file.exists()


def test_is_active_no_state_file(safe_mode):
    """Test is_active returns False when no state file exists"""
    assert safe_mode.is_active() is False


@patch('subprocess.run')
def test_is_active_with_state_file_and_containers(mock_run, safe_mode):
    """Test is_active returns True when state file exists and containers running"""
    # Create state file
    state = {"active": True, "reason": "Test"}
    safe_mode.state_file.write_text(json.dumps(state))

    # Mock docker ps to show safe mode container running
    mock_run.return_value = Mock(
        returncode=0,
        stdout="safe-mode-status",
        stderr=""
    )

    assert safe_mode.is_active() is True


@patch('subprocess.run')
def test_is_active_state_file_but_no_containers(mock_run, safe_mode):
    """Test is_active when state file exists but containers not running"""
    # Create state file
    state = {"active": True, "reason": "Test"}
    safe_mode.state_file.write_text(json.dumps(state))

    # Mock docker ps to show no safe mode containers
    mock_run.return_value = Mock(
        returncode=0,
        stdout="",
        stderr=""
    )

    assert safe_mode.is_active() is False


def test_is_active_inactive_state(safe_mode):
    """Test is_active returns False when state says inactive"""
    state = {"active": False, "reason": "Test"}
    safe_mode.state_file.write_text(json.dumps(state))

    assert safe_mode.is_active() is False


def test_get_status_not_active(safe_mode):
    """Test get_status when safe mode not active"""
    status = safe_mode.get_status()

    assert status["active"] is False
    assert status["reason"] is None
    assert status["activated_at"] is None
    assert status["error_details"] is None


@patch('subprocess.run')
def test_get_status_active(mock_run, safe_mode):
    """Test get_status when safe mode is active"""
    # Create state file
    state = {
        "active": True,
        "reason": "Application crash",
        "activated_at": "2024-01-01T12:00:00",
        "error_details": {"error": "Timeout"}
    }
    safe_mode.state_file.write_text(json.dumps(state))

    # Mock docker ps to show containers running
    mock_run.return_value = Mock(returncode=0, stdout="safe-mode-status", stderr="")

    status = safe_mode.get_status()

    assert status["active"] is True
    assert status["reason"] == "Application crash"
    assert status["activated_at"] == "2024-01-01T12:00:00"
    assert status["error_details"] == {"error": "Timeout"}


@patch('subprocess.run')
def test_activate_creates_status_json(mock_run, safe_mode):
    """Test that activate creates status.json for web page"""
    mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

    safe_mode.activate(reason="Test", error_details={"code": 500})

    # Check status.json was created
    status_file = safe_mode.safe_mode_path / "status-page" / "status.json"
    assert status_file.exists()

    with open(status_file) as f:
        status = json.load(f)

    assert status["reason"] == "Test"
    assert status["error_details"] == {"code": 500}


@patch('subprocess.run')
def test_deactivate_removes_status_json(mock_run, safe_mode):
    """Test that deactivate removes status.json"""
    # First activate to create status.json
    mock_run.return_value = Mock(returncode=0, stderr="", stdout="")
    safe_mode.activate(reason="Test")

    status_file = safe_mode.safe_mode_path / "status-page" / "status.json"
    assert status_file.exists()

    # Now deactivate
    safe_mode.deactivate()

    assert not status_file.exists()


def test_get_status_corrupted_state_file(safe_mode):
    """Test get_status handles corrupted state file gracefully"""
    # Create corrupted state file
    safe_mode.state_file.write_text("not valid json {")

    # Mock is_active to return True
    with patch.object(safe_mode, 'is_active', return_value=True):
        status = safe_mode.get_status()

        assert status["active"] is True
        assert "corrupted" in status["reason"].lower()
        assert "error" in status["error_details"]
