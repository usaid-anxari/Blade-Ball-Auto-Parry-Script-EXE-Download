"""AutoParryBot – core deflection / auto-win logic.

Educational demo: shows how screen analysis + timing logic can be combined
to produce an "instant parry" reaction (0ms configured delay).
"""

from __future__ import annotations

import time
from typing import Optional

import pyautogui

from config import Config
from screen_scanner import BallState, ScreenScanner
from utils import clamp, setup_logger


class AutoParryBot:
    """High-level bot that orchestrates scanning + parry triggering."""

    def __init__(self, config: Config, scanner: ScreenScanner,
                 player_pos: tuple = (960, 540)):
        self.config = config
        self.scanner = scanner
        self.player_pos = player_pos
        self.logger = setup_logger("bot", config.log_file, config.log_level)

        self._running = False
        self._last_parry_ts: float = 0.0
        self._deflect_count: int = 0
        self._auto_win_enabled: bool = False

    # ---- public API ----
    def start(self) -> None:
        """Begin the scan/parry loop."""
        if self._running:
            self.logger.warning("Bot already running.")
            return
        self._running = True
        self.logger.info("AutoParryBot started.")

    def stop(self) -> None:
        """Stop the scan/parry loop."""
        self._running = False
        self.logger.info("AutoParryBot stopped. Deflects: %d", self._deflect_count)

    def is_running(self) -> bool:
        return self._running

    def enable_auto_win(self, enabled: bool) -> None:
        self._auto_win_enabled = enabled
        self.logger.info("Auto-win %s.", "enabled" if enabled else "disabled")

    def tick(self) -> Optional[BallState]:
        """Single iteration – call this from the main loop at scan_fps."""
        if not self._running:
            return None
        try:
            frame = self.scanner.grab_frame()
            state = self.scanner.detect_ball(frame)
            if state.found and self.scanner.estimate_parry_trigger(
                state, self.player_pos
            ):
                self._maybe_parry()
            if self._auto_win_enabled:
                self._auto_win_step(state)
            return state
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Tick error: %s", exc)
            return None

    # ---- internals ----
    def _maybe_parry(self) -> bool:
        """Trigger a parry if cooldown has elapsed. Returns True if fired."""
        now = time.perf_counter() * 1000.0
        if now - self._last_parry_ts < self.config.parry_cooldown_ms:
            return False

        # Educational: simulate a 0ms deflection by sleeping the configured
        # delay (which is 0 by default) then pressing the parry key.
        if self.config.parry_delay_ms > 0:
            time.sleep(self.config.parry_delay_ms / 1000.0)

        try:
            pyautogui.press("f")  # in-game parry key (configurable)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Parry input failed: %s", exc)
            return False

        self._last_parry_ts = now
        self._deflect_count += 1
        self.logger.debug("Parry fired (#%d).", self._deflect_count)
        return True

    def _auto_win_step(self, state: BallState) -> None:
        """Educational placeholder for auto-win sequencing."""
        if not state.found:
            return
        # Reposition logic / ability triggering could live here.
        # Intentionally minimal – do not use to violate ToS.
        pass

    def stats(self) -> dict:
        """Return a small statistics dict (for UI / logs)."""
        return {
            "running": self._running,
            "deflects": self._deflect_count,
            "auto_win": self._auto_win_enabled,
        }
