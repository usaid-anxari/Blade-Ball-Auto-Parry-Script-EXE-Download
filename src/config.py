"""Configuration module for the Blade Ball Auto Parry educational demo.

All timings, hotkeys and detection sensitivities are exposed here so the
user can tweak the behavior without touching the core logic.
"""

from dataclasses import dataclass, field


@dataclass
class Config:
    """Central configuration container."""

    # ---- Hotkeys (uses keyboard library notation) ----
    start_hotkey: str = "f6"
    stop_hotkey: str = "f7"
    panic_hotkey: str = "f8"  # immediately halts everything

    # ---- Parry timing (milliseconds) ----
    parry_delay_ms: int = 0          # 0ms = instant deflection (educational)
    parry_cooldown_ms: int = 120     # minimum gap between parry triggers
    reaction_sensitivity: float = 0.65  # OpenCV match threshold (0..1)

    # ---- Screen scanner ----
    scan_region: tuple = (0, 0, 1920, 1080)  # left, top, width, height
    scan_fps: int = 60
    ball_color_lower: tuple = (0, 180, 180)   # HSV lower bound
    ball_color_upper: tuple = (25, 255, 255)  # HSV upper bound

    # ---- Farm manager ----
    farm_loop_delay_ms: int = 500
    token_target: int = 999999     # educational "infinite" target
    ability_cooldowns: dict = field(
        default_factory=lambda: {"dash": 8000, "shield": 12000}
    )

    # ---- Macro recorder ----
    macro_record_path: str = "macro.json"
    macro_playback_speed: float = 1.0  # 1.0 = real-time

    # ---- Logging ----
    log_file: str = "blade_ball_assistant.log"
    log_level: str = "INFO"


# Singleton-style default config
DEFAULT_CONFIG = Config()
