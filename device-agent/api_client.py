"""API client for communicating with Overlord"""

import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors"""
    pass


class NetworkError(APIError):
    """Network-related errors"""
    pass


class AuthenticationError(APIError):
    """Authentication-related errors"""
    pass


class APIClient:
    """Client for Overlord API communication"""

    def __init__(
        self,
        api_url: str,
        device_id: str,
        api_key: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize API client

        Args:
            api_url: Base URL for Overlord API
            device_id: Unique device identifier
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 10)
        """
        self.api_url = api_url.rstrip('/')
        self.device_id = device_id
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Metrica-Fleet-Agent/1.0'
        })

        # Add API key header if provided
        if api_key:
            self.session.headers.update({
                'X-API-Key': api_key
            })

        logger.debug(f"APIClient initialized for device {device_id}")

    def register_device(
        self,
        hostname: str,
        role: str,
        branch: str = "main",
        segment: Optional[str] = None,
        ip_address: Optional[str] = None,
        mac_address: Optional[str] = None,
        agent_version: str = "1.0.0",
        device_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register device with Overlord

        Args:
            hostname: Device hostname
            role: Device role (e.g., 'audio-player', 'display')
            branch: Git branch to track (default: 'main')
            segment: Deployment segment (optional)
            ip_address: Device IP address (optional)
            mac_address: Device MAC address (optional)
            agent_version: Agent version string
            device_metadata: Additional device metadata (optional)

        Returns:
            Dict containing device_id, status, and message

        Raises:
            NetworkError: On network-related failures
            AuthenticationError: On authentication failures
            APIError: On other API errors
        """
        url = f"{self.api_url}/api/devices"

        payload = {
            "device_id": self.device_id,
            "hostname": hostname,
            "role": role,
            "branch": branch,
            "agent_version": agent_version
        }

        # Add optional fields
        if segment:
            payload["segment"] = segment
        if ip_address:
            payload["ip_address"] = ip_address
        if mac_address:
            payload["mac_address"] = mac_address
        if device_metadata:
            payload["device_metadata"] = device_metadata

        logger.info(f"Registering device {self.device_id} as {role}")

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)

            # Handle different HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or unauthorized")
            elif response.status_code == 403:
                raise AuthenticationError("Forbidden - check API permissions")
            elif response.status_code >= 500:
                raise APIError(f"Server error: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            logger.info(f"Device registered successfully: {data}")
            return data

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout registering device: {e}")
            raise NetworkError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error registering device: {e}")
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register device: {e}")
            if isinstance(e, (AuthenticationError, APIError)):
                raise
            raise APIError(f"Request failed: {e}")

    def send_heartbeat(
        self,
        status: str = "running",
        uptime_seconds: Optional[int] = None,
        cpu_percent: Optional[float] = None,
        memory_percent: Optional[float] = None,
        disk_percent: Optional[float] = None,
        temperature: Optional[float] = None,
        containers_running: Optional[int] = None,
        containers_failed: Optional[int] = None,
        commit_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send heartbeat to Overlord

        Args:
            status: Device status (e.g., 'running', 'error', 'maintenance')
            uptime_seconds: Device uptime in seconds
            cpu_percent: CPU usage percentage (0-100)
            memory_percent: Memory usage percentage (0-100)
            disk_percent: Disk usage percentage (0-100)
            temperature: CPU temperature in Celsius
            containers_running: Number of running containers
            containers_failed: Number of failed containers
            commit_hash: Current git commit hash

        Returns:
            Dict containing acknowledged status and next_heartbeat_seconds

        Raises:
            NetworkError: On network-related failures
            APIError: On other API errors
        """
        url = f"{self.api_url}/api/devices/{self.device_id}/heartbeat"

        payload = {
            "status": status,
        }

        # Add optional metrics
        if uptime_seconds is not None:
            payload["uptime_seconds"] = uptime_seconds
        if cpu_percent is not None:
            payload["cpu_percent"] = cpu_percent
        if memory_percent is not None:
            payload["memory_percent"] = memory_percent
        if disk_percent is not None:
            payload["disk_percent"] = disk_percent
        if temperature is not None:
            payload["temperature"] = temperature
        if containers_running is not None:
            payload["containers_running"] = containers_running
        if containers_failed is not None:
            payload["containers_failed"] = containers_failed
        if commit_hash is not None:
            payload["commit_hash"] = commit_hash

        logger.debug(f"Sending heartbeat for device {self.device_id}")

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)

            if response.status_code == 404:
                raise APIError(f"Device {self.device_id} not found - needs registration")
            elif response.status_code >= 500:
                raise APIError(f"Server error: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            logger.debug(f"Heartbeat acknowledged: {data}")
            return data

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout sending heartbeat: {e}")
            raise NetworkError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error sending heartbeat: {e}")
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send heartbeat: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Request failed: {e}")

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get device configuration from Overlord

        Returns:
            Dict containing device configuration:
                - device_id: Device identifier
                - role: Device role
                - branch: Git branch
                - segment: Deployment segment
                - update_enabled: Whether updates are enabled
                - version_lock: Locked version (if any)
                - maintenance_mode: Whether in maintenance mode
                - config: Additional configuration

        Raises:
            NetworkError: On network-related failures
            APIError: On other API errors
        """
        url = f"{self.api_url}/api/devices/{self.device_id}/config"

        logger.debug(f"Fetching configuration for device {self.device_id}")

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 404:
                raise APIError(f"Device {self.device_id} not found - needs registration")
            elif response.status_code >= 500:
                raise APIError(f"Server error: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            logger.debug(f"Configuration retrieved: {data}")
            return data

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout getting configuration: {e}")
            raise NetworkError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error getting configuration: {e}")
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get configuration: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Request failed: {e}")

    def report_deployment(
        self,
        commit_hash: str,
        status: str,
        error: Optional[str] = None,
        deploy_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Report deployment status to Overlord

        Args:
            commit_hash: Git commit hash being deployed
            status: Deployment status ('pending', 'success', 'failed', 'rolled_back')
            error: Error message if deployment failed
            deploy_metadata: Additional deployment metadata

        Returns:
            Dict containing deployment acknowledgement

        Raises:
            NetworkError: On network-related failures
            APIError: On other API errors
        """
        url = f"{self.api_url}/api/devices/{self.device_id}/deployment"

        payload = {
            "commit_hash": commit_hash,
            "status": status,
        }

        if error:
            payload["error"] = error
        if deploy_metadata:
            payload["deploy_metadata"] = deploy_metadata

        logger.info(f"Reporting deployment status: {status} for commit {commit_hash}")

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)

            if response.status_code == 404:
                raise APIError(f"Device {self.device_id} not found - needs registration")
            elif response.status_code >= 500:
                raise APIError(f"Server error: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            logger.info(f"Deployment reported successfully: {data}")
            return data

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout reporting deployment: {e}")
            raise NetworkError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error reporting deployment: {e}")
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report deployment: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Request failed: {e}")

    def close(self):
        """Close the API client session"""
        self.session.close()
        logger.debug("APIClient session closed")
