"""Screen scanner module – OpenCV-powered detection of the ball, player
position and parry triggers. Educational demonstration only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import mss
import numpy as np

from config import Config
from utils import setup_logger


@dataclass
class BallState:
    """Snapshot of the detected ball at a given moment."""
    found: bool
    position: Tuple[int, int]        # (x, y) in screen coords
    velocity: Tuple[float, float]    # (vx, vy) px/frame
    radius: int


class ScreenScanner:
    """Reads the screen and detects the ball trajectory."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("scanner", config.log_file, config.log_level)
        self._sct = mss.mss()
        self._prev_pos: Optional[Tuple[int, int]] = None
        self._prev_time: Optional[float] = None

    def grab_frame(self) -> np.ndarray:
        """Capture the configured screen region as an BGR ndarray."""
        left, top, w, h = self.config.scan_region
        shot = self._sct.grab({"left": left, "top": top, "width": w, "height": h})
        frame = np.array(shot)[:, :, :3]
        return frame

    def detect_ball(self, frame: np.ndarray) -> Optional[BallState]:
        """Detect the ball via HSV color masking + contour analysis."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array(self.config.ball_color_lower)
        upper = np.array(self.config.ball_color_upper)
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return BallState(False, (0, 0), (0.0, 0.0), 0)

        # Pick the largest circular contour
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area < 25:  # noise threshold
            return BallState(False, (0, 0), (0.0, 0.0), 0)

        (x, y), radius = cv2.minEnclosingCircle(c)
        pos = (int(x), int(y))
        velocity = self._compute_velocity(pos)
        return BallState(True, pos, velocity, int(radius))

    def _compute_velocity(self, pos: Tuple[int, int]) -> Tuple[float, float]:
        """Estimate per-frame velocity (px/frame) from previous position."""
        now = time.perf_counter()
        if self._prev_pos is None or self._prev_time is None:
            self._prev_pos, self._prev_time = pos, now
            return (0.0, 0.0)
        dt = max(now - self._prev_time, 1e-6)
        vx = (pos[0] - self._prev_pos[0]) / dt
        vy = (pos[1] - self._prev_pos[1]) / dt
        self._prev_pos, self._prev_time = pos, now
        return (vx, vy)

    def estimate_parry_trigger(self, state: BallState,
                               player_pos: Tuple[int, int]) -> bool:
        """Return True if the ball is approaching the player fast enough
        to justify a parry trigger (educational heuristic)."""
        if not state.found:
            return False
        dx = player_pos[0] - state.position[0]
        dy = player_pos[1] - state.position[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 1.0:
            return True
        speed = (state.velocity[0] ** 2 + state.velocity[1] ** 2) ** 0.5
        # approach_speed = component of velocity pointing toward player
        approach = (state.velocity[0] * dx + state.velocity[1] * dy) / dist
        return approach > 0 and speed / dist > self.config.reaction_sensitivity

    def close(self) -> None:
        """Release screen-capture resources."""
        try:
            self._sct.close()
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.debug("Scanner close error: %s", exc)
