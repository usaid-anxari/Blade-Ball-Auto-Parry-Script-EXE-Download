"""Utility helpers: logging, privilege checks, OS helpers."""

from __future__ import annotations

import ctypes
import logging
import os
import platform
import sys
from typing import Optional


def setup_logger(name: str = "blade_ball", log_file: str = "assistant.log",
                 level: str = "INFO") -> logging.Logger:
    """Create and return a configured logger with console + file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning("Could not attach file handler: %s", exc)

    return logger


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    if platform.system() != "Windows":
        return os.geteuid() == 0  # type: ignore[attr-defined]
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def ensure_admin_or_warn(logger: Optional[logging.Logger] = None) -> bool:
    """Warn (but do not crash) if the script is not running as admin."""
    if is_admin():
        return True
    if logger:
        logger.warning(
            "Administrator privileges are recommended for global hotkey "
            "capture. Some hotkeys may not be detected otherwise."
        )
    return False


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value into the [low, high] range."""
    return max(low, min(high, value))


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Division that never raises ZeroDivisionError."""
    return a / b if b != 0 else default
