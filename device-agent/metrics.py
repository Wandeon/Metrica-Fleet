"""System and Docker metrics collection"""

import psutil
import logging
import socket
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import docker
    import docker.errors
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collect system and application metrics"""

    def __init__(self, temperature_path: str = "/sys/class/thermal/thermal_zone0/temp"):
        """Initialize metrics collector

        Args:
            temperature_path: Path to temperature sensor file (Raspberry Pi specific)
        """
        self.temperature_path = temperature_path
        self.docker_client = None

        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
                # Test connection
                self.docker_client.ping()
            except docker.errors.DockerException as e:
                logger.warning(f"Docker client unavailable: {e}")
                self.docker_client = None
            except Exception as e:
                logger.warning(f"Failed to initialize Docker client: {e}")
                self.docker_client = None
        else:
            logger.info("Docker library not available")

    def collect(self) -> Dict[str, Any]:
        """Collect all system metrics

        Returns:
            Dictionary with system metrics:
            - uptime_seconds: System uptime in seconds
            - cpu_percent: CPU usage percentage (0-100)
            - memory_percent: Memory usage percentage (0-100)
            - disk_percent: Disk usage percentage (0-100)
            - temperature_celsius: CPU temperature or None if unavailable
            - ip_address: Primary IP address or None
            - mac_address: Primary MAC address or None
        """
        ip_address, mac_address = self._get_network_info()

        return {
            "uptime_seconds": self._get_uptime(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "temperature_celsius": self._get_temperature(),
            "ip_address": ip_address,
            "mac_address": mac_address,
        }

    def collect_docker_metrics(self) -> Dict[str, Any]:
        """Collect Docker container metrics

        Returns:
            Dictionary with Docker metrics:
            - containers_running: Count of running containers
            - containers_failed: Count of failed/exited containers
            - container_list: List of container details
        """
        if not self.docker_client:
            logger.debug("Docker client not available, returning empty metrics")
            return {
                "containers_running": 0,
                "containers_failed": 0,
                "container_list": []
            }

        try:
            containers = self.docker_client.containers.list(all=True)

            running_containers = [c for c in containers if c.status == "running"]
            failed_containers = [c for c in containers if c.status != "running"]

            container_list = []
            for container in containers:
                # Get image tag safely
                image_tag = "unknown"
                if container.image.tags:
                    image_tag = container.image.tags[0]

                container_list.append({
                    "name": container.name,
                    "status": container.status,
                    "image": image_tag
                })

            return {
                "containers_running": len(running_containers),
                "containers_failed": len(failed_containers),
                "container_list": container_list
            }

        except Exception as e:
            logger.error(f"Failed to collect Docker metrics: {e}")
            return {
                "containers_running": 0,
                "containers_failed": 0,
                "container_list": []
            }

    def _get_uptime(self) -> int:
        """Get system uptime in seconds

        Tries /proc/uptime first (Linux), falls back to psutil.boot_time

        Returns:
            System uptime in seconds
        """
        try:
            # Try reading from /proc/uptime (Linux)
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                return int(uptime_seconds)
        except (FileNotFoundError, IOError, ValueError):
            # Fallback to psutil
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                return int(uptime_seconds)
            except Exception as e:
                logger.error(f"Failed to get uptime: {e}")
                return 0

    def _get_temperature(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi specific)

        Reads from /sys/class/thermal/thermal_zone0/temp
        Temperature is in millidegrees Celsius, converted to degrees

        Returns:
            Temperature in Celsius or None if not available
        """
        try:
            with open(self.temperature_path, 'r') as f:
                # Temperature is in millidegrees, convert to degrees
                temp_millidegrees = float(f.read().strip())
                temp_celsius = temp_millidegrees / 1000.0
                return round(temp_celsius, 1)
        except FileNotFoundError:
            logger.debug(f"Temperature file not found: {self.temperature_path}")
            return None
        except (IOError, ValueError) as e:
            logger.warning(f"Failed to read temperature: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading temperature: {e}")
            return None

    def _get_network_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Get primary network interface IP and MAC address

        Prefers non-loopback interfaces (eth0, wlan0, etc.) over loopback (lo)

        Returns:
            Tuple of (ip_address, mac_address) or (None, None) if unavailable
        """
        try:
            net_if_addrs = psutil.net_if_addrs()

            # Preferred interface names (non-loopback)
            preferred_interfaces = ['eth0', 'wlan0', 'en0', 'wlan1', 'eth1']

            # Try preferred interfaces first
            for interface_name in preferred_interfaces:
                if interface_name in net_if_addrs:
                    ip_addr, mac_addr = self._extract_addresses(net_if_addrs[interface_name])
                    if ip_addr:
                        return ip_addr, mac_addr

            # Try any non-loopback interface
            for interface_name, addresses in net_if_addrs.items():
                if interface_name != 'lo' and not interface_name.startswith('docker'):
                    ip_addr, mac_addr = self._extract_addresses(addresses)
                    if ip_addr:
                        return ip_addr, mac_addr

            # Fallback to loopback if nothing else available
            if 'lo' in net_if_addrs:
                ip_addr, mac_addr = self._extract_addresses(net_if_addrs['lo'])
                return ip_addr, mac_addr

            return None, None

        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return None, None

    def _extract_addresses(self, addresses: list) -> Tuple[Optional[str], Optional[str]]:
        """Extract IP and MAC addresses from psutil address list

        Args:
            addresses: List of psutil.snic address objects

        Returns:
            Tuple of (ip_address, mac_address)
        """
        ip_addr = None
        mac_addr = None

        for addr in addresses:
            # AF_INET = 2 (IPv4)
            if addr.family == socket.AF_INET:
                ip_addr = addr.address
            # AF_PACKET = 17 (Linux MAC address) or AF_LINK = 18 (macOS)
            elif addr.family in (17, 18):
                mac_addr = addr.address

        return ip_addr, mac_addr
