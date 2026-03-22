"""Mock model output publisher - simulates model predictions."""

import time
import math
import numpy as np
from typing import List, Optional

import cereal.messaging as messaging


class MockModeld:
    """Simulates model predictions and publishes to cereal messaging."""

    def __init__(self):
        self.pm = messaging.PubMaster([
            "modelV2",
            "liveCalibration",
            "driverStateV2",
        ])

        self._start_time = time.monotonic()
        self._num_points = 192  # Number of path points

        # Calibration state
        self._calib_valid = True
        self._rpy_calib = [0.0, 0.0, 0.0]  # Roll, pitch, yaw
        self._height = 0.0

    def publish_model_v2(self, lead_distance: Optional[float] = None):
        """Publish simulated model predictions."""
        t = time.monotonic() - self._start_time

        msg = messaging.new_message("modelV2")
        msg.valid = True

        # Generate path points
        x = np.arange(self._num_points) * 2.0  # Every 2 meters
        y = 2.0 * np.sin((t * 0.1) + x * 0.02)  # Gentle curve
        z = np.zeros(self._num_points)

        # Position
        msg.modelV2.position.x = [float(v) for v in x]
        msg.modelV2.position.y = [float(v) for v in y]
        msg.modelV2.position.z = [float(v) for v in z]
        msg.modelV2.position.xStd = [0.5] * self._num_points
        msg.modelV2.position.yStd = [0.3] * self._num_points
        msg.modelV2.position.zStd = [0.1] * self._num_points

        # Orientation (yaw rate)
        yaw_rate = float(0.01 * math.sin(t * 0.2))
        msg.modelV2.orientation.x = [0.0] * self._num_points
        msg.modelV2.orientation.y = [0.0] * self._num_points
        msg.modelV2.orientation.z = [yaw_rate] * self._num_points

        # Lane lines (4 lines: left-left, left, right, right-right)
        # Initialize lane lines list with 4 elements
        msg.modelV2.laneLines = [{}] * 4
        msg.modelV2.laneLineProbs = [0.0] * 4
        for i in range(4):
            lane = msg.modelV2.laneLines[i]
            offset = -4.5 + i * 1.5  # Spacing between lanes
            lane.x = [float(v) for v in x]
            lane.y = [float(v) for v in (offset + 0.3 * np.sin(t + x * 0.01))]
            lane.z = [float(v) for v in z]
            lane.t = [float(i * 0.1) for i in range(self._num_points)]
            msg.modelV2.laneLineProbs[i] = 0.9 if i in [1, 2] else 0.0  # Middle two lanes

        # Road edges
        # Initialize road edges list with 2 elements
        msg.modelV2.roadEdges = [{}] * 2
        msg.modelV2.roadEdgeStds = [0.0] * 2
        for i in range(2):
            edge = msg.modelV2.roadEdges[i]
            offset = -6.0 if i == 0 else 6.0  # Left and right edges
            edge.x = [float(v) for v in x]
            edge.y = [float(v) for v in (offset + 0.2 * np.sin(t * 0.5 + x * 0.005))]
            edge.z = [float(v) for v in z]
            edge.t = [float(i * 0.1) for i in range(self._num_points)]
            msg.modelV2.roadEdgeStds[i] = 0.1

        # Lead vehicle (simplified - no lead data for now)
        msg.modelV2.leadsV3 = []

        # Acceleration
        msg.modelV2.acceleration.x = [float(v) for v in (0.3 * np.sin(t + np.arange(self._num_points) * 0.1))]

        # Meta information
        msg.modelV2.frameId = int(t * 100)  # 100 Hz
        msg.modelV2.timestampEof = int(time.monotonic() * 1e9)

        self.pm.send("modelV2", msg)

    def publish_live_calibration(self):
        """Publish simulated live calibration."""
        t = time.monotonic() - self._start_time

        msg = messaging.new_message("liveCalibration")
        msg.valid = True

        # Simulate calibration slowly converging
        msg.liveCalibration.rpyCalib = self._rpy_calib
        msg.liveCalibration.height = [self._height]
        msg.liveCalibration.calStatus = 1  # CALIBRATED
        msg.liveCalibration.calCycle = 0
        msg.liveCalibration.validBlocks = 100

        # Wide camera euler (for wide camera mode)
        msg.liveCalibration.wideFromDeviceEuler = [0.0, 0.0, 0.0]

        self.pm.send("liveCalibration", msg)

    def publish_driver_state_v2(self):
        """Publish simulated driver state."""
        msg = messaging.new_message("driverStateV2")
        msg.valid = True

        # Driver state for left driver (looking forward)
        msg.driverStateV2.leftDriverData.faceOrientation = [0.0, 0.0, 0.0]
        msg.driverStateV2.leftDriverData.facePosition = [0.0, 0.0]
        msg.driverStateV2.leftDriverData.faceProb = 1.0
        msg.driverStateV2.leftDriverData.leftEyeProb = 0.95
        msg.driverStateV2.leftDriverData.rightEyeProb = 0.95

        self.pm.send("driverStateV2", msg)

    def update(self, lead_distance: Optional[float] = None):
        """Update and publish all model messages."""
        self.publish_model_v2(lead_distance)
        self.publish_live_calibration()
        self.publish_driver_state_v2()