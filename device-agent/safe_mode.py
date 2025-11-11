"""Safe mode management for device agent

Safe mode provides a minimal status page when the main application fails,
ensuring the device remains accessible and its status is visible.
"""

import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SafeMode:
    """Manage safe mode activation and status"""

    def __init__(self, safe_mode_path: Path, state_file: Optional[Path] = None):
        """Initialize safe mode manager

        Args:
            safe_mode_path: Path to safe mode docker-compose directory
            state_file: Path to state file (defaults to /tmp/metrica-safe-mode.lock)
        """
        self.safe_mode_path = safe_mode_path
        self.compose_file = safe_mode_path / "docker-compose.yml"
        self.state_file = state_file or Path("/tmp/metrica-safe-mode.lock")

        if not self.compose_file.exists():
            raise FileNotFoundError(f"Safe mode docker-compose.yml not found at {self.compose_file}")

    def activate(self, reason: str, error_details: Optional[Dict[str, Any]] = None) -> bool:
        """Activate safe mode

        Args:
            reason: Human-readable reason for safe mode activation
            error_details: Optional dictionary with error details

        Returns:
            True if safe mode was activated successfully
        """
        logger.warning(f"Activating safe mode: {reason}")

        try:
            # Create state file with activation details
            state = {
                "activated_at": datetime.now().isoformat(),
                "reason": reason,
                "error_details": error_details or {},
                "active": True
            }

            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Safe mode state written to {self.state_file}")

            # Write status.json for the web interface
            status_file = self.safe_mode_path / "status-page" / "status.json"
            try:
                from config import config
                state["device_id"] = config.DEVICE_ID
            except Exception:
                pass

            with open(status_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Status page data written to {status_file}")

            # Stop main application first
            logger.info("Stopping main application...")
            try:
                subprocess.run(
                    ["docker", "compose", "down"],
                    cwd="/opt/metrica-fleet",
                    capture_output=True,
                    timeout=60,
                    check=False  # Don't fail if no containers running
                )
            except Exception as e:
                logger.warning(f"Could not stop main application: {e}")

            # Start safe mode services
            logger.info("Starting safe mode services...")
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.safe_mode_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info("Safe mode activated successfully")
                logger.info(f"Status page available at http://localhost:8888")
                return True
            else:
                logger.error(f"Failed to activate safe mode: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error activating safe mode: {e}", exc_info=True)
            return False

    def deactivate(self) -> bool:
        """Deactivate safe mode and clean up state

        Returns:
            True if safe mode was deactivated successfully
        """
        logger.info("Deactivating safe mode...")

        try:
            # Stop safe mode services
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.safe_mode_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"Failed to stop safe mode services: {result.stderr}")
                return False

            # Remove state file
            if self.state_file.exists():
                self.state_file.unlink()
                logger.info(f"Removed state file: {self.state_file}")

            # Remove status.json
            status_file = self.safe_mode_path / "status-page" / "status.json"
            if status_file.exists():
                status_file.unlink()
                logger.info(f"Removed status file: {status_file}")

            logger.info("Safe mode deactivated successfully")
            return True

        except Exception as e:
            logger.error(f"Error deactivating safe mode: {e}", exc_info=True)
            return False

    def is_active(self) -> bool:
        """Check if safe mode is currently active

        Returns:
            True if safe mode is active (based on state file and running containers)
        """
        # Check state file first
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                if not state.get("active", False):
                    return False
        except Exception as e:
            logger.warning(f"Could not read state file: {e}")
            return False

        # Verify containers are actually running
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=safe-mode", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "safe-mode" in result.stdout
        except Exception as e:
            logger.warning(f"Could not check Docker containers: {e}")
            # If we can't check Docker, rely on state file
            return True

    def get_status(self) -> Dict[str, Any]:
        """Get current safe mode status

        Returns:
            Dictionary with safe mode status information
        """
        if not self.is_active():
            return {
                "active": False,
                "reason": None,
                "activated_at": None,
                "error_details": None
            }

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                return {
                    "active": True,
                    "reason": state.get("reason", "Unknown"),
                    "activated_at": state.get("activated_at"),
                    "error_details": state.get("error_details", {})
                }
        except Exception as e:
            logger.error(f"Error reading safe mode state: {e}")
            return {
                "active": True,
                "reason": "Unknown (state file corrupted)",
                "activated_at": None,
                "error_details": {"error": str(e)}
            }
