"""Mock selfdrive state publisher - simulates autonomous driving state."""

import time
import math
from typing import Optional
from cereal import log
import cereal.messaging as messaging


class MockSelfdrive:
    """Simulates selfdrive state and publishes to cereal messaging."""

    def __init__(self):
        self.pm = messaging.PubMaster([
            "selfdriveState",
            "radarState",
            "longitudinalPlan",
        ])

        self._start_time = time.monotonic()
        self._enabled = False
        self._experimental_mode = False
        self._personality = log.LongitudinalPersonality.standard

    def publish_selfdrive_state(self):
        """Publish simulated selfdrive state."""
        msg = messaging.new_message("selfdriveState")
        msg.valid = True

        # State
        if self._enabled:
            state = log.SelfdriveState.OpenpilotState.enabled
        else:
            state = log.SelfdriveState.OpenpilotState.disabled
        msg.selfdriveState.state = state
        msg.selfdriveState.enabled = self._enabled
        msg.selfdriveState.active = self._enabled
        msg.selfdriveState.experimentalMode = self._experimental_mode
        msg.selfdriveState.personality = self._personality

        # No alerts
        msg.selfdriveState.alertText1 = ""
        msg.selfdriveState.alertText2 = ""
        msg.selfdriveState.alertSize = log.SelfdriveState.AlertSize.none
        msg.selfdriveState.alertStatus = log.SelfdriveState.AlertStatus.normal

        self.pm.send("selfdriveState", msg)

    def publish_radar_state(self, lead_distance: Optional[float] = None):
        """Publish simulated radar state."""
        t = time.monotonic() - self._start_time

        msg = messaging.new_message("radarState")
        msg.valid = True

        if lead_distance is not None:
            # Lead one
            msg.radarState.leadOne.status = True
            msg.radarState.leadOne.dRel = lead_distance
            msg.radarState.leadOne.yRel = 0.5 * math.sin(t)
            msg.radarState.leadOne.vRel = -2.0 + math.sin(t * 0.5)
            msg.radarState.leadOne.aRel = 0.0
            msg.radarState.leadOne.vLat = 0.0
            msg.radarState.leadOne.vLead = 18.0
            msg.radarState.leadOne.vLeadK = 18.0
            msg.radarState.leadOne.aLeadK = 0.0
            msg.radarState.leadOne.aLeadTau = 1.5
            msg.radarState.leadOne.modelProb = 0.9
            msg.radarState.leadOne.radar = True

        self.pm.send("radarState", msg)

    def publish_longitudinal_plan(self):
        """Publish simulated longitudinal plan."""
        msg = messaging.new_message("longitudinalPlan")
        msg.valid = True

        msg.longitudinalPlan.allowThrottle = True
        msg.longitudinalPlan.fcw = False
        msg.longitudinalPlan.hasLead = True

        self.pm.send("longitudinalPlan", msg)

    def set_enabled(self, enabled: bool):
        """Set engagement state."""
        self._enabled = enabled

    def toggle_enabled(self):
        """Toggle engagement state."""
        self._enabled = not self._enabled

    def set_experimental_mode(self, experimental: bool):
        """Set experimental mode."""
        self._experimental_mode = experimental

    def toggle_experimental(self):
        """Toggle experimental mode."""
        self._experimental_mode = not self._experimental_mode

    def update(self, lead_distance: Optional[float] = None):
        """Update and publish all selfdrive messages."""
        self.publish_selfdrive_state()
        self.publish_radar_state(lead_distance)
        self.publish_longitudinal_plan()