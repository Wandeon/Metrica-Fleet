"""Metrica Fleet Device Agent

Manages device state, deployment updates, and health reporting.
Includes automatic error recovery with safe mode fallback.
"""

import sys
import time
import logging
import signal
import socket
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from config import config
from api_client import APIClient, NetworkError, APIError
from metrics import SystemMetrics
from safe_mode import SafeMode

# Configure logging
log_level = getattr(logging, config.DEVICE_ID and "INFO" or "DEBUG", logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metrica-agent")


class DeviceAgent:
    """Main device agent class with integrated error recovery"""

    # Failure thresholds
    MAX_REGISTRATION_FAILURES = 3
    MAX_HEARTBEAT_FAILURES = 5

    def __init__(self):
        self.running = False
        self.device_id = config.DEVICE_ID

        # Initialize components
        self.api_client: Optional[APIClient] = None
        self.metrics: Optional[SystemMetrics] = None
        self.safe_mode: Optional[SafeMode] = None

        # Failure counters
        self.registration_failures = 0
        self.consecutive_heartbeat_failures = 0

        # State tracking
        self.registered = False
        self.last_config: Optional[Dict[str, Any]] = None

    def start(self):
        """Start the agent with full lifecycle"""
        logger.info(f"Starting Metrica Fleet Agent for device: {self.device_id}")
        logger.info(f"Agent Version: 1.0.0")
        logger.info(f"Configuration: role={config.DEVICE_ROLE}, branch={config.DEVICE_BRANCH}")

        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error("Configuration errors:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)

        # Initialize components
        try:
            self._initialize_components()
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            sys.exit(1)

        # Check if safe mode is already active from previous crash
        if self.safe_mode and config.SAFE_MODE_ENABLED:
            if self.safe_mode.is_active():
                safe_status = self.safe_mode.get_status()
                logger.warning(f"Safe mode is already active!")
                logger.warning(f"Reason: {safe_status.get('reason')}")
                logger.warning(f"Activated at: {safe_status.get('activated_at')}")
                logger.info("Entering safe mode operation...")
                self._run_safe_mode()
                return

        self.running = True

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Attempt device registration
        if not self._register_device():
            logger.error("Failed to register device after maximum retries")
            self._activate_safe_mode("Registration failed after multiple attempts")
            self._run_safe_mode()
            return

        logger.info("Agent started successfully, entering main loop")
        self._run()

    def _initialize_components(self):
        """Initialize all agent components"""
        logger.info("Initializing agent components...")

        # Initialize API client
        self.api_client = APIClient(
            api_url=config.API_URL,
            device_id=config.DEVICE_ID,
            api_key=config.API_KEY
        )
        logger.info(f"API client initialized: {config.API_URL}")

        # Initialize metrics collector
        self.metrics = SystemMetrics()
        logger.info("Metrics collector initialized")

        # Initialize safe mode manager
        if config.SAFE_MODE_ENABLED:
            safe_mode_path = Path(__file__).parent / "safe_mode"
            if safe_mode_path.exists():
                self.safe_mode = SafeMode(
                    safe_mode_path=safe_mode_path,
                    state_file=config.DATA_DIR / "safe-mode.lock"
                )
                logger.info(f"Safe mode initialized: {safe_mode_path}")
            else:
                logger.warning(f"Safe mode directory not found: {safe_mode_path}")
                self.safe_mode = None
        else:
            logger.info("Safe mode disabled in configuration")
            self.safe_mode = None

    def _register_device(self) -> bool:
        """Register device with Overlord, with retry logic

        Returns:
            True if registration succeeded, False if max retries exceeded
        """
        hostname = socket.gethostname()

        while self.registration_failures < self.MAX_REGISTRATION_FAILURES:
            try:
                logger.info(f"Attempting device registration (attempt {self.registration_failures + 1}/{self.MAX_REGISTRATION_FAILURES})...")

                # Collect network info for registration
                system_info = self.metrics.collect()

                result = self.api_client.register_device(
                    hostname=hostname,
                    role=config.DEVICE_ROLE,
                    branch=config.DEVICE_BRANCH,
                    ip_address=system_info.get("ip_address"),
                    mac_address=system_info.get("mac_address"),
                    agent_version="1.0.0"
                )

                logger.info(f"Device registered successfully: {result.get('message', 'OK')}")
                self.registered = True
                self.registration_failures = 0  # Reset counter on success
                return True

            except NetworkError as e:
                self.registration_failures += 1
                logger.error(f"Network error during registration: {e}")
                if self.registration_failures < self.MAX_REGISTRATION_FAILURES:
                    wait_time = min(5 * self.registration_failures, 30)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except APIError as e:
                self.registration_failures += 1
                logger.error(f"API error during registration: {e}")
                if self.registration_failures < self.MAX_REGISTRATION_FAILURES:
                    wait_time = min(5 * self.registration_failures, 30)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except Exception as e:
                self.registration_failures += 1
                logger.error(f"Unexpected error during registration: {e}", exc_info=True)
                if self.registration_failures < self.MAX_REGISTRATION_FAILURES:
                    wait_time = min(5 * self.registration_failures, 30)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        return False

    def _run(self):
        """Main agent loop with heartbeat and configuration polling"""
        last_heartbeat = 0
        last_config_check = 0

        logger.info(f"Main loop started (heartbeat={config.HEARTBEAT_INTERVAL}s, poll={config.POLL_INTERVAL}s)")

        while self.running:
            try:
                current_time = time.time()

                # Send heartbeat
                if current_time - last_heartbeat >= config.HEARTBEAT_INTERVAL:
                    if self._send_heartbeat():
                        last_heartbeat = current_time
                        # Reset failure counter on success
                        self.consecutive_heartbeat_failures = 0
                    else:
                        self.consecutive_heartbeat_failures += 1
                        logger.warning(f"Heartbeat failure count: {self.consecutive_heartbeat_failures}/{self.MAX_HEARTBEAT_FAILURES}")

                        if self.consecutive_heartbeat_failures >= self.MAX_HEARTBEAT_FAILURES:
                            logger.error("Maximum consecutive heartbeat failures reached")
                            self._activate_safe_mode(
                                reason="Heartbeat failures exceeded threshold",
                                error_details={"consecutive_failures": self.consecutive_heartbeat_failures}
                            )
                            self._run_safe_mode()
                            return

                # Check for configuration updates
                if current_time - last_config_check >= config.POLL_INTERVAL:
                    self._check_configuration()
                    last_config_check = current_time

                # Short sleep to prevent busy loop
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                self.running = False
                break

            except Exception as e:
                logger.error(f"Critical error in main loop: {e}", exc_info=True)
                self._activate_safe_mode(
                    reason="Critical error in main loop",
                    error_details={"error": str(e), "type": type(e).__name__}
                )
                self._run_safe_mode()
                return

    def _send_heartbeat(self) -> bool:
        """Send heartbeat with system metrics to Overlord

        Returns:
            True if heartbeat sent successfully, False otherwise
        """
        try:
            # Collect system metrics
            system_metrics = self.metrics.collect()
            docker_metrics = self.metrics.collect_docker_metrics()

            # Send heartbeat with all metrics
            result = self.api_client.send_heartbeat(
                status="running",
                uptime_seconds=system_metrics.get("uptime_seconds"),
                cpu_percent=system_metrics.get("cpu_percent"),
                memory_percent=system_metrics.get("memory_percent"),
                disk_percent=system_metrics.get("disk_percent"),
                temperature=system_metrics.get("temperature_celsius"),
                containers_running=docker_metrics.get("containers_running"),
                containers_failed=docker_metrics.get("containers_failed")
            )

            logger.debug(f"Heartbeat sent successfully")
            return True

        except NetworkError as e:
            logger.error(f"Network error sending heartbeat: {e}")
            return False

        except APIError as e:
            logger.error(f"API error sending heartbeat: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending heartbeat: {e}", exc_info=True)
            return False

    def _check_configuration(self):
        """Check for configuration updates from Overlord"""
        try:
            config_data = self.api_client.get_configuration()

            # Check if configuration changed
            if self.last_config is None:
                logger.info(f"Initial configuration received: branch={config_data.get('branch')}, segment={config_data.get('segment')}")
                self.last_config = config_data
            else:
                changes = []

                if config_data.get("branch") != self.last_config.get("branch"):
                    changes.append(f"branch: {self.last_config.get('branch')} -> {config_data.get('branch')}")

                if config_data.get("segment") != self.last_config.get("segment"):
                    changes.append(f"segment: {self.last_config.get('segment')} -> {config_data.get('segment')}")

                if config_data.get("update_enabled") != self.last_config.get("update_enabled"):
                    changes.append(f"update_enabled: {self.last_config.get('update_enabled')} -> {config_data.get('update_enabled')}")

                if config_data.get("maintenance_mode") != self.last_config.get("maintenance_mode"):
                    changes.append(f"maintenance_mode: {self.last_config.get('maintenance_mode')} -> {config_data.get('maintenance_mode')}")

                if changes:
                    logger.info(f"Configuration changed: {', '.join(changes)}")
                    self.last_config = config_data
                    # TODO: Apply configuration updates (future task)
                else:
                    logger.debug("No configuration changes detected")

        except NetworkError as e:
            logger.debug(f"Network error checking configuration: {e}")

        except APIError as e:
            logger.warning(f"API error checking configuration: {e}")

        except Exception as e:
            logger.error(f"Unexpected error checking configuration: {e}", exc_info=True)

    def _activate_safe_mode(self, reason: str, error_details: Optional[Dict[str, Any]] = None):
        """Activate safe mode due to critical error

        Args:
            reason: Human-readable reason for activation
            error_details: Optional dictionary with error details
        """
        if not self.safe_mode or not config.SAFE_MODE_ENABLED:
            logger.error(f"Cannot activate safe mode (disabled or unavailable): {reason}")
            return

        logger.critical(f"Activating safe mode: {reason}")

        try:
            success = self.safe_mode.activate(reason=reason, error_details=error_details)
            if success:
                logger.info("Safe mode activated successfully")
            else:
                logger.error("Failed to activate safe mode")
        except Exception as e:
            logger.error(f"Error activating safe mode: {e}", exc_info=True)

    def _run_safe_mode(self):
        """Run in safe mode - minimal operation with status heartbeats"""
        logger.warning("Running in SAFE MODE - limited functionality")
        logger.info("Device will send status heartbeats only")

        self.running = True
        last_heartbeat = 0

        while self.running:
            try:
                current_time = time.time()

                # Send safe mode status heartbeats
                if current_time - last_heartbeat >= config.HEARTBEAT_INTERVAL:
                    try:
                        safe_status = self.safe_mode.get_status() if self.safe_mode else {}

                        self.api_client.send_heartbeat(
                            status="safe_mode",
                            uptime_seconds=int(current_time - last_heartbeat)
                        )
                        logger.debug("Safe mode heartbeat sent")
                        last_heartbeat = current_time

                    except Exception as e:
                        logger.error(f"Failed to send safe mode heartbeat: {e}")

                # Check for remote deactivation command (TODO: implement via config)
                # For now, safe mode requires manual intervention

                time.sleep(5)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt in safe mode")
                self.running = False
                break

            except Exception as e:
                logger.error(f"Error in safe mode loop: {e}", exc_info=True)
                time.sleep(10)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def stop(self):
        """Stop the agent cleanly"""
        logger.info("Stopping agent...")
        self.running = False

        if self.api_client:
            try:
                self.api_client.close()
            except Exception as e:
                logger.error(f"Error closing API client: {e}")


def main():
    """Entry point"""
    agent = DeviceAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, stopping...")
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Agent shutdown complete")


if __name__ == "__main__":
    main()
