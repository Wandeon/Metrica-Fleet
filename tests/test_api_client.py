"""Tests for API client"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'device-agent'))

from api_client import APIClient, APIError, NetworkError, AuthenticationError


class TestAPIClientInitialization:
    """Tests for API client initialization"""

    def test_api_client_initialization(self):
        """Test API client initializes with config"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        assert client.api_url == "http://localhost:8080"
        assert client.device_id == "test-device-001"
        assert client.timeout == 10
        assert client.api_key is None

    def test_api_client_with_api_key(self):
        """Test API client initializes with API key"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001",
            api_key="test-api-key"
        )

        assert client.api_key == "test-api-key"
        assert client.session.headers.get('X-API-Key') == "test-api-key"

    def test_api_client_strips_trailing_slash(self):
        """Test API client strips trailing slash from URL"""
        client = APIClient(
            api_url="http://localhost:8080/",
            device_id="test-device-001"
        )

        assert client.api_url == "http://localhost:8080"

    def test_api_client_custom_timeout(self):
        """Test API client accepts custom timeout"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001",
            timeout=30
        )

        assert client.timeout == 30


class TestRegisterDevice:
    """Tests for device registration"""

    @patch('requests.Session.post')
    def test_register_device_success(self, mock_post):
        """Test successful device registration"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "device_id": "test-device-001",
            "status": "registered",
            "message": "Device registered successfully"
        }
        mock_post.return_value = mock_response

        result = client.register_device(
            hostname="rpi-001",
            role="audio-player",
            branch="main"
        )

        assert result["status"] == "registered"
        assert result["device_id"] == "test-device-001"

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['device_id'] == "test-device-001"
        assert call_args[1]['json']['hostname'] == "rpi-001"
        assert call_args[1]['json']['role'] == "audio-player"
        assert call_args[1]['timeout'] == 10

    @patch('requests.Session.post')
    def test_register_device_with_all_fields(self, mock_post):
        """Test device registration with all optional fields"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"device_id": "test-device-001", "status": "registered"}
        mock_post.return_value = mock_response

        result = client.register_device(
            hostname="rpi-001",
            role="audio-player",
            branch="develop",
            segment="beta",
            ip_address="192.168.1.100",
            mac_address="b8:27:eb:00:00:01",
            agent_version="1.2.0",
            device_metadata={"location": "lobby"}
        )

        # Verify all fields were sent
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['segment'] == "beta"
        assert payload['ip_address'] == "192.168.1.100"
        assert payload['mac_address'] == "b8:27:eb:00:00:01"
        assert payload['agent_version'] == "1.2.0"
        assert payload['device_metadata'] == {"location": "lobby"}

    @patch('requests.Session.post')
    def test_register_device_timeout(self, mock_post):
        """Test device registration handles timeout"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")

        with pytest.raises(NetworkError) as exc_info:
            client.register_device(
                hostname="rpi-001",
                role="audio-player"
            )

        assert "timeout" in str(exc_info.value).lower()

    @patch('requests.Session.post')
    def test_register_device_connection_error(self, mock_post):
        """Test device registration handles connection error"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(NetworkError) as exc_info:
            client.register_device(
                hostname="rpi-001",
                role="audio-player"
            )

        assert "Connection error" in str(exc_info.value)

    @patch('requests.Session.post')
    def test_register_device_authentication_error(self, mock_post):
        """Test device registration handles authentication error"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            client.register_device(
                hostname="rpi-001",
                role="audio-player"
            )

        assert "Invalid API key" in str(exc_info.value)

    @patch('requests.Session.post')
    def test_register_device_server_error(self, mock_post):
        """Test device registration handles server error"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.register_device(
                hostname="rpi-001",
                role="audio-player"
            )

        assert "Server error: 500" in str(exc_info.value)


class TestSendHeartbeat:
    """Tests for sending heartbeat"""

    @patch('requests.Session.post')
    def test_send_heartbeat_minimal(self, mock_post):
        """Test sending heartbeat with minimal data"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "acknowledged": True,
            "next_heartbeat_seconds": 30
        }
        mock_post.return_value = mock_response

        result = client.send_heartbeat(status="running")

        assert result["acknowledged"] is True
        assert result["next_heartbeat_seconds"] == 30

        # Verify the request
        call_args = mock_post.call_args
        assert call_args[1]['json']['status'] == "running"

    @patch('requests.Session.post')
    def test_send_heartbeat_with_metrics(self, mock_post):
        """Test sending heartbeat with all metrics"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"acknowledged": True}
        mock_post.return_value = mock_response

        result = client.send_heartbeat(
            status="running",
            uptime_seconds=3600,
            cpu_percent=45.2,
            memory_percent=62.8,
            disk_percent=28.5,
            temperature=52.3,
            containers_running=5,
            containers_failed=1,
            commit_hash="abc123"
        )

        # Verify all metrics were sent
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['status'] == "running"
        assert payload['uptime_seconds'] == 3600
        assert payload['cpu_percent'] == 45.2
        assert payload['memory_percent'] == 62.8
        assert payload['disk_percent'] == 28.5
        assert payload['temperature'] == 52.3
        assert payload['containers_running'] == 5
        assert payload['containers_failed'] == 1
        assert payload['commit_hash'] == "abc123"

    @patch('requests.Session.post')
    def test_send_heartbeat_device_not_found(self, mock_post):
        """Test heartbeat when device not registered"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.send_heartbeat(status="running")

        assert "not found" in str(exc_info.value)
        assert "registration" in str(exc_info.value).lower()

    @patch('requests.Session.post')
    def test_send_heartbeat_timeout(self, mock_post):
        """Test heartbeat handles timeout"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(NetworkError):
            client.send_heartbeat(status="running")


class TestGetConfiguration:
    """Tests for getting device configuration"""

    @patch('requests.Session.get')
    def test_get_configuration_success(self, mock_get):
        """Test successful configuration retrieval"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "device_id": "test-device-001",
            "role": "audio-player",
            "branch": "main",
            "segment": "production",
            "update_enabled": True,
            "version_lock": None,
            "maintenance_mode": False,
            "config": {"volume": 75}
        }
        mock_get.return_value = mock_response

        result = client.get_configuration()

        assert result["device_id"] == "test-device-001"
        assert result["role"] == "audio-player"
        assert result["update_enabled"] is True
        assert result["config"]["volume"] == 75

        # Verify the request
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "/api/devices/test-device-001/config" in call_args[0][0]

    @patch('requests.Session.get')
    def test_get_configuration_device_not_found(self, mock_get):
        """Test configuration when device not registered"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.get_configuration()

        assert "not found" in str(exc_info.value)

    @patch('requests.Session.get')
    def test_get_configuration_timeout(self, mock_get):
        """Test configuration handles timeout"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(NetworkError):
            client.get_configuration()

    @patch('requests.Session.get')
    def test_get_configuration_connection_error(self, mock_get):
        """Test configuration handles connection error"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(NetworkError):
            client.get_configuration()


class TestReportDeployment:
    """Tests for reporting deployment status"""

    @patch('requests.Session.post')
    def test_report_deployment_success(self, mock_post):
        """Test successful deployment report"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "deployment_id": "deploy-123",
            "status": "recorded"
        }
        mock_post.return_value = mock_response

        result = client.report_deployment(
            commit_hash="abc123def456",
            status="success"
        )

        assert result["status"] == "recorded"

        # Verify the request
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['commit_hash'] == "abc123def456"
        assert payload['status'] == "success"

    @patch('requests.Session.post')
    def test_report_deployment_with_error(self, mock_post):
        """Test deployment report with error"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "recorded"}
        mock_post.return_value = mock_response

        result = client.report_deployment(
            commit_hash="abc123",
            status="failed",
            error="Docker build failed"
        )

        # Verify error was sent
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['status'] == "failed"
        assert payload['error'] == "Docker build failed"

    @patch('requests.Session.post')
    def test_report_deployment_with_metadata(self, mock_post):
        """Test deployment report with metadata"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "recorded"}
        mock_post.return_value = mock_response

        metadata = {
            "duration_seconds": 120,
            "services": ["web", "api"]
        }

        result = client.report_deployment(
            commit_hash="abc123",
            status="success",
            deploy_metadata=metadata
        )

        # Verify metadata was sent
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['deploy_metadata'] == metadata

    @patch('requests.Session.post')
    def test_report_deployment_timeout(self, mock_post):
        """Test deployment report handles timeout"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(NetworkError):
            client.report_deployment(
                commit_hash="abc123",
                status="success"
            )

    @patch('requests.Session.post')
    def test_report_deployment_device_not_found(self, mock_post):
        """Test deployment report when device not registered"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.report_deployment(
                commit_hash="abc123",
                status="success"
            )

        assert "not found" in str(exc_info.value)


class TestSessionManagement:
    """Tests for session management"""

    def test_close_session(self):
        """Test closing API client session"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        # Should not raise any errors
        client.close()


class TestHeaders:
    """Tests for request headers"""

    def test_default_headers(self):
        """Test default headers are set"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001"
        )

        assert 'Content-Type' in client.session.headers
        assert client.session.headers['Content-Type'] == 'application/json'
        assert 'User-Agent' in client.session.headers

    def test_api_key_header(self):
        """Test API key is added to headers"""
        client = APIClient(
            api_url="http://localhost:8080",
            device_id="test-device-001",
            api_key="secret-key-123"
        )

        assert 'X-API-Key' in client.session.headers
        assert client.session.headers['X-API-Key'] == "secret-key-123"
