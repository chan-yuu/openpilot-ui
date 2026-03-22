"""Mock vehicle data publisher - simulates car state and related messages."""

import time
import math
import cereal.messaging as messaging


class MockCard:
    """Simulates vehicle state and publishes to cereal messaging."""

    def __init__(self):
        self.pm = messaging.PubMaster([
            "carState",
        ])

        # Simulation state
        self._v_ego = 20.0  # m/s
        self._steering_angle = 0.0
        self._v_cruise = 30.0  # m/s
        self._start_time = time.monotonic()

    def publish_car_state(self):
        """Publish simulated car state."""
        t = time.monotonic() - self._start_time

        # Simulate varying speed
        self._v_ego = 20.0 + 5.0 * math.sin(t * 0.3)
        self._v_ego = max(0, self._v_ego)

        # Simulate gentle steering
        self._steering_angle = 5.0 * math.sin(t * 0.2)

        msg = messaging.new_message("carState")
        msg.valid = True

        # Speed
        msg.carState.vEgo = self._v_ego
        msg.carState.vEgoRaw = self._v_ego
        msg.carState.vEgoCluster = self._v_ego

        # Cruise control
        msg.carState.vCruise = self._v_cruise
        msg.carState.vCruiseCluster = self._v_cruise
        msg.carState.cruiseState.enabled = True
        msg.carState.cruiseState.speed = self._v_cruise
        msg.carState.cruiseState.available = True

        # Steering
        msg.carState.steeringAngleDeg = self._steering_angle
        msg.carState.steeringPressed = False
        msg.carState.steeringTorque = 0.5 * math.sin(t * 0.2)

        # Pedals
        msg.carState.brakePressed = False
        msg.carState.gasPressed = True

        # Blinkers
        msg.carState.leftBlinker = False
        msg.carState.rightBlinker = False

        # Gear (Drive = 3)
        msg.carState.gearShifter = 3

        self.pm.send("carState", msg)

    def update(self, enabled: bool = False, experimental: bool = False):
        """Update and publish all car messages."""
        self.publish_car_state()