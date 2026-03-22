"""Mock sensor publisher - simulates device state and sensor data."""

import time
from cereal import log, car
import cereal.messaging as messaging


class MockSensord:
    """Simulates device state and sensor data."""

    def __init__(self, device_type: str = "pc"):
        self.pm = messaging.PubMaster([
            "deviceState",
            "pandaStates",
            "liveParameters",
        ])

        self._start_time = time.monotonic()
        self._device_type = device_type
        self._started = True
        self._ignition = True

    def publish_device_state(self):
        """Publish simulated device state."""
        t = time.monotonic() - self._start_time

        msg = messaging.new_message("deviceState")
        msg.valid = True

        msg.deviceState.started = self._started
        msg.deviceState.deviceType = self._device_type
        msg.deviceState.thermalStatus = log.DeviceState.ThermalStatus.green
        msg.deviceState.lastAthenaPingTime = int(t * 1000)

        self.pm.send("deviceState", msg)

    def publish_panda_states(self):
        """Publish simulated panda states."""
        msg = messaging.new_message("pandaStates", 1)
        msg.valid = True

        panda = msg.pandaStates[0]
        panda.pandaType = log.PandaState.PandaType.uno
        panda.ignitionLine = self._ignition
        panda.ignitionCan = False
        panda.safetyModel = car.CarParams.SafetyModel.hondaNidec
        panda.harnessStatus = log.PandaState.HarnessStatus.normal
        panda.faultStatus = log.PandaState.FaultStatus.none
        panda.heartbeatLost = False
        panda.uptime = int(time.monotonic() - self._start_time)

        self.pm.send("pandaStates", msg)

    def publish_live_parameters(self):
        """Publish simulated live parameters."""
        msg = messaging.new_message("liveParameters")
        msg.valid = True

        msg.liveParameters.valid = True
        msg.liveParameters.steerRatio = 15.0

        self.pm.send("liveParameters", msg)

    def set_started(self, started: bool):
        """Set started state."""
        self._started = started

    def set_ignition(self, ignition: bool):
        """Set ignition state."""
        self._ignition = ignition

    def update(self):
        """Update and publish all sensor messages."""
        self.publish_device_state()
        self.publish_panda_states()
        self.publish_live_parameters()