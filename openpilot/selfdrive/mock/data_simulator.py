"""Data simulator - orchestrates all mock data publishers for standalone UI operation."""

import time
import math
import argparse
import threading
import signal
import sys
from typing import Optional

from openpilot.selfdrive.mock.mock_card import MockCard
from openpilot.selfdrive.mock.mock_modeld import MockModeld
from openpilot.selfdrive.mock.mock_selfdrive import MockSelfdrive
from openpilot.selfdrive.mock.mock_sensord import MockSensord

# Camera server is optional (requires VisionIpc)
try:
    from openpilot.selfdrive.mock.mock_camerad import MockCamerad
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False


class DataSimulator:
    """Orchestrates all mock data publishers for standalone UI operation."""

    def __init__(self, mode: str = "demo", camera_enabled: bool = True):
        """
        Initialize data simulator.

        Args:
            mode: Simulation mode ("demo", "camera", "vehicle")
            camera_enabled: Whether to simulate camera frames
        """
        self.mode = mode
        self.camera_enabled = camera_enabled and CAMERA_AVAILABLE

        # Initialize mock publishers
        self.mock_card = MockCard()
        self.mock_modeld = MockModeld()
        self.mock_selfdrive = MockSelfdrive()
        self.mock_sensord = MockSensord()

        # Camera server (optional)
        self.mock_camerad = None
        if self.camera_enabled:
            try:
                self.mock_camerad = MockCamerad()
            except Exception as e:
                print(f"Warning: Could not initialize camera server: {e}")
                self.mock_camerad = None

        # Simulation state
        self._running = False
        self._start_time = time.monotonic()
        self._engaged = False
        self._experimental_mode = False
        self._lead_distance: Optional[float] = 50.0  # Lead vehicle distance

        # Frame rate
        self._update_rate = 20  # Hz
        self._camera_thread = None

    def set_engaged(self, engaged: bool):
        """Set engagement state."""
        self._engaged = engaged
        self.mock_selfdrive.set_enabled(engaged)

    def toggle_engaged(self):
        """Toggle engagement state."""
        self._engaged = not self._engaged
        self.mock_selfdrive.set_enabled(self._engaged)
        print(f"Engagement: {'ENGAGED' if self._engaged else 'DISENGAGED'}")

    def set_experimental_mode(self, experimental: bool):
        """Set experimental mode."""
        self._experimental_mode = experimental
        self.mock_selfdrive.set_experimental_mode(experimental)

    def toggle_experimental(self):
        """Toggle experimental mode."""
        self._experimental_mode = not self._experimental_mode
        self.mock_selfdrive.set_experimental_mode(self._experimental_mode)
        print(f"Experimental mode: {'ON' if self._experimental_mode else 'OFF'}")

    def set_lead_distance(self, distance: Optional[float]):
        """Set lead vehicle distance."""
        self._lead_distance = distance

    def update(self):
        """Update all mock data and publish messages."""
        t = time.monotonic() - self._start_time

        # Simulate varying lead distance
        if self._lead_distance is not None:
            # Lead vehicle oscillates between 40-70m
            self._lead_distance = 55.0 + 15.0 * math.sin(t * 0.2)

        # Update all publishers
        self.mock_card.update(enabled=self._engaged, experimental=self._experimental_mode)
        self.mock_modeld.update(lead_distance=self._lead_distance)
        self.mock_selfdrive.update(lead_distance=self._lead_distance)
        self.mock_sensord.update()

    def run(self):
        """Run the data simulation loop."""
        self._running = True
        self._start_time = time.monotonic()

        # Start camera server in separate thread
        if self.mock_camerad:
            self._camera_thread = self.mock_camerad.run_in_thread()

        print("Data simulator started")
        print("  Press Ctrl+C to stop")

        frame_time = 1.0 / self._update_rate

        while self._running:
            start = time.monotonic()

            self.update()

            elapsed = time.monotonic() - start
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)

    def stop(self):
        """Stop the simulation."""
        self._running = False
        if self.mock_camerad:
            self.mock_camerad.stop()

    def run_in_thread(self):
        """Run simulation in a background thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread


def main():
    parser = argparse.ArgumentParser(description="Data simulator for standalone UI")
    parser.add_argument("--mode", choices=["demo", "camera", "vehicle"], default="demo",
                        help="Simulation mode")
    parser.add_argument("--rate", type=int, default=20,
                        help="Update rate in Hz")
    parser.add_argument("--engaged", action="store_true",
                        help="Start in engaged state")

    args = parser.parse_args()

    simulator = DataSimulator(mode=args.mode)
    simulator._update_rate = args.rate
    simulator.set_engaged(args.engaged)

    def signal_handler(sig, frame):
        print("\nStopping...")
        simulator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    simulator.run()


if __name__ == "__main__":
    main()