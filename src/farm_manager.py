"""FarmManager – educational demo for token farming, ability management
and macro recording/playback using keyboard + pyautogui.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

import keyboard
import pyautogui

from config import Config
from utils import setup_logger


class FarmManager:
    """Coordinates token farming, ability cooldowns and macro playback."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger("farm", config.log_file, config.log_level)
        self._abilities: Dict[str, float] = {
            name: 0.0 for name in config.ability_cooldowns
        }
        self._tokens: int = 0
        self._running: bool = False

    # ---- token farming ----
    def start_farm(self) -> None:
        """Begin the educational "infinite tokens" loop."""
        if self._running:
            return
        self._running = True
        self.logger.info("Farm loop started (target=%d).",
                         self.config.token_target)

    def stop_farm(self) -> None:
        self._running = False
        self.logger.info("Farm loop stopped. Tokens collected: %d", self._tokens)

    def farm_tick(self) -> None:
        """One iteration of the farming loop – call periodically."""
        if not self._running:
            return
        # Educational stub: simulate a token pickup action.
        try:
            pyautogui.press("e")
            self._tokens += 1
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Farm tick failed: %s", exc)
        self._use_abilities_if_ready()
        time.sleep(self.config.farm_loop_delay_ms / 1000.0)

    # ---- ability management ----
    def _use_abilities_if_ready(self) -> None:
        now = time.perf_counter() * 1000.0
        for name, ready_at in list(self._abilities.items()):
            if now >= ready_at:
                try:
                    pyautogui.press(name[0])  # crude key mapping
                    cd = self.config.ability_cooldowns.get(name, 0)
                    self._abilities[name] = now + cd
                    self.logger.debug("Ability '%s' fired (cd=%dms).", name, cd)
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.error("Ability '%s' failed: %s", name, exc)

    @property
    def tokens(self) -> int:
        return self._tokens

    # ---- macro recorder ----
    def record_macro(self, stop_key: str = "esc") -> List[dict]:
        """Record keyboard events until `stop_key` is pressed."""
        events: List[dict] = []
        self.logger.info("Recording macro (press %s to stop).", stop_key)

        def _on_event(event: keyboard.KeyboardEvent) -> None:
            events.append({
                "time": time.perf_counter(),
                "name": event.name,
                "event_type": event.event_type,
            })

        hook = keyboard.hook(_on_event, suppress=False)
        keyboard.wait(stop_key)
        keyboard.unhook(hook)
        self.logger.info("Macro recorded: %d events.", len(events))
        return events

    def save_macro(self, events: List[dict],
                   path: str | None = None) -> Path:
        """Persist a recorded macro to JSON."""
        path = path or self.config.macro_record_path
        p = Path(path)
        p.write_text(json.dumps(events, indent=2), encoding="utf-8")
        self.logger.info("Macro saved to %s.", p)
        return p

    def load_macro(self, path: str | None = None) -> List[dict]:
        """Load a previously saved macro."""
        path = path or self.config.macro_record_path
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.logger.info("Macro loaded from %s (%d events).", path, len(data))
        return data

    def playback_macro(self, events: List[dict]) -> None:
        """Replay a recorded macro at the configured playback speed."""
        if not events:
            return
        speed = max(self.config.macro_playback_speed, 0.01)
        t0 = events[0]["time"]
        self.logger.info("Playing back macro (%d events, %.2fx).",
                         len(events), speed)
        for ev in events:
            delay = (ev["time"] - t0) / speed
            time.sleep(max(delay, 0))
            try:
                if ev["event_type"] == keyboard.KEY_DOWN:
                    pyautogui.keyDown(ev["name"])
                else:
                    pyautogui.keyUp(ev["name"])
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Playback error on %s: %s", ev["name"], exc)
        self.logger.info("Macro playback finished.")
