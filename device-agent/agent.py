"""Metrica Fleet Device Agent

Manages device state, deployment updates, and health reporting.
"""

import sys
import time
import logging
import signal
from typing import Optional
from datetime import datetime

from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metrica-agent")


class DeviceAgent:
    """Main device agent class"""

    def __init__(self):
        self.running = False
        self.device_id = config.DEVICE_ID

    def start(self):
        """Start the agent"""
        logger.info(f"Starting Metrica Fleet Agent for device: {self.device_id}")

        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error("Configuration errors:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)

        self.running = True

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("Agent started successfully")
        self._run()

    def _run(self):
        """Main agent loop"""
        while self.running:
            try:
                # TODO: Implement polling logic
                logger.debug("Agent running...")
                time.sleep(config.POLL_INTERVAL)
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def stop(self):
        """Stop the agent"""
        logger.info("Stopping agent...")
        self.running = False


def main():
    """Entry point"""
    agent = DeviceAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
