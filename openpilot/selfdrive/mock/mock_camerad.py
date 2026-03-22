"""Mock camera server - simulates camera frames for standalone UI operation."""

import time
import numpy as np
import threading
from msgq.visionipc import VisionIpcServer, VisionStreamType
import cereal.messaging as messaging

# Camera dimensions (matching simulator)
W, H = 1928, 1208


def rgb_to_nv12(rgb):
    """Convert RGB image to NV12 (YUV420) format using BT.601 coefficients."""
    h, w = rgb.shape[:2]
    r = rgb[:, :, 0].astype(np.int32)
    g = rgb[:, :, 1].astype(np.int32)
    b = rgb[:, :, 2].astype(np.int32)

    # Y plane - BT.601 coefficients
    y = (((b * 13 + g * 65 + r * 33) + 64) >> 7) + 16
    y = np.clip(y, 0, 255).astype(np.uint8)

    # Subsample RGB for UV (2x2 box filter)
    r_sub = (r[0::2, 0::2] + r[0::2, 1::2] + r[1::2, 0::2] + r[1::2, 1::2] + 2) >> 2
    g_sub = (g[0::2, 0::2] + g[0::2, 1::2] + g[1::2, 0::2] + g[1::2, 1::2] + 2) >> 2
    b_sub = (b[0::2, 0::2] + b[0::2, 1::2] + b[1::2, 0::2] + b[1::2, 1::2] + 2) >> 2

    # U and V planes
    u = np.clip((b_sub * 56 - g_sub * 37 - r_sub * 19 + 0x8080) >> 8, 0, 255).astype(np.uint8)
    v = np.clip((r_sub * 56 - g_sub * 47 - b_sub * 9 + 0x8080) >> 8, 0, 255).astype(np.uint8)

    # Interleave UV for NV12 format
    uv = np.empty((h // 2, w), dtype=np.uint8)
    uv[:, 0::2] = u
    uv[:, 1::2] = v

    return np.concatenate([y.ravel(), uv.ravel()]).tobytes()


class MockCamerad:
    """Simulates camera frames and publishes via VisionIpc."""

    def __init__(self):
        # Camera dimensions
        self.width = W
        self.height = H

        # Create VisionIpc server
        self.server = VisionIpcServer("camerad")

        # Create buffers for road camera stream
        self.server.create_buffers(VisionStreamType.VISION_STREAM_ROAD, 4, self.width, self.height)

        # Create buffers for wide road camera stream
        self.server.create_buffers(VisionStreamType.VISION_STREAM_WIDE_ROAD, 4, self.width, self.height)

        # Start the listener
        self.server.start_listener()

        # Message publisher for camera state
        self.pm = messaging.PubMaster(['roadCameraState', 'wideRoadCameraState'])

        self._running = False
        self._start_time = time.monotonic()
        self._frame_id = 0

    def _generate_frame(self, t: float) -> np.ndarray:
        """Generate a simple road-like pattern as RGB."""
        # Create RGB image
        rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Sky (top portion) - blue gradient
        sky_height = int(self.height * 0.35)
        for y in range(sky_height):
            progress = y / sky_height
            rgb[y, :, 0] = int(100 + 50 * progress)  # R
            rgb[y, :, 1] = int(150 + 50 * progress)  # G
            rgb[y, :, 2] = int(200 + 55 * progress)  # B

        # Road (bottom portion) - dark gray with perspective
        road_start = sky_height
        rgb[road_start:, :, :] = 40  # Base road color (dark gray)

        # Add perspective lane lines
        center_x = self.width // 2
        for y in range(road_start, self.height):
            # Perspective effect - lines converge towards center
            progress = (y - road_start) / (self.height - road_start)
            spread = int(250 * (1 - progress * 0.7))

            # White color for lane lines
            intensity = int(150 + 100 * progress)

            # Left lane line
            left_x = center_x - spread
            if 0 <= left_x < self.width:
                for dx in range(-5, 6):
                    if 0 <= left_x + dx < self.width:
                        rgb[y, left_x + dx, :] = intensity

            # Right lane line
            right_x = center_x + spread
            if 0 <= right_x < self.width:
                for dx in range(-5, 6):
                    if 0 <= right_x + dx < self.width:
                        rgb[y, right_x + dx, :] = intensity

            # Center dashed line
            dash_phase = int(t * 30) % 8
            if dash_phase < 4:
                for dx in range(-2, 3):
                    if 0 <= center_x + dx < self.width:
                        rgb[y, center_x + dx, :] = intensity

        # Add some texture variation
        noise = np.random.randint(-10, 10, (self.height, self.width, 3), dtype=np.int16)
        rgb = np.clip(rgb.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        return rgb

    def _send_frame(self, yuv: bytes, frame_id: int, stream_type: VisionStreamType, pub_type: str):
        """Send a YUV frame to VisionIpc and publish camera state."""
        eof = int(frame_id * 0.05 * 1e9)  # 20 FPS timing
        self.server.send(stream_type, yuv, frame_id, eof, eof)

        # Publish camera state message
        msg = messaging.new_message(pub_type, valid=True)
        if pub_type == 'roadCameraState':
            msg.roadCameraState.frameId = frame_id
            msg.roadCameraState.timestampEof = eof
            msg.roadCameraState.transform = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        else:
            msg.wideRoadCameraState.frameId = frame_id
            msg.wideRoadCameraState.timestampEof = eof
            msg.wideRoadCameraState.transform = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

        self.pm.send(pub_type, msg)

    def run(self):
        """Run the camera simulation loop."""
        self._running = True
        self._start_time = time.monotonic()
        self._frame_id = 0

        print("Mock camera server started")
        print(f"  Resolution: {self.width}x{self.height}")

        while self._running:
            t = time.monotonic() - self._start_time

            # Generate frame
            rgb = self._generate_frame(t)
            yuv = rgb_to_nv12(rgb)

            # Send to road camera
            self._send_frame(yuv, self._frame_id, VisionStreamType.VISION_STREAM_ROAD, 'roadCameraState')

            # Also send to wide camera (same frame for simplicity)
            self._send_frame(yuv, self._frame_id, VisionStreamType.VISION_STREAM_WIDE_ROAD, 'wideRoadCameraState')

            self._frame_id += 1
            time.sleep(1 / 20)  # 20 FPS

    def stop(self):
        """Stop the camera simulation."""
        self._running = False

    def run_in_thread(self):
        """Run camera simulation in a background thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread


if __name__ == "__main__":
    import signal
    import sys

    camera = MockCamerad()

    def signal_handler(sig, frame):
        print("\nStopping...")
        camera.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    camera.run()