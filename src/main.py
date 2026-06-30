"""Entry point for the Blade Ball Auto Parry educational demo.

Wires up the ScreenScanner, AutoParryBot and FarmManager, and registers
global hotkeys via the `keyboard` library for start/stop/panic control.
"""

from __future__ import annotations

import threading
import time

import keyboard

from bot import AutoParryBot
from config import DEFAULT_CONFIG as CFG
from farm_manager import FarmManager
from screen_scanner import ScreenScanner
from utils import ensure_admin_or_warn, setup_logger


def main() -> None:
    logger = setup_logger("main", CFG.log_file, CFG.log_level)
    ensure_admin_or_warn(logger)
    logger.info("Blade Ball Auto Parry educational demo – starting up.")

    scanner = ScreenScanner(CFG)
    bot = AutoParryBot(CFG, scanner)
    farm = FarmManager(CFG)

    stop_flag = threading.Event()

    def worker() -> None:
        """Background loop running bot ticks + farm ticks."""
        frame_dt = 1.0 / max(CFG.scan_fps, 1)
        while not stop_flag.is_set():
            bot.tick()
            farm.farm_tick()
            time.sleep(frame_dt)

    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()

    # ---- Hotkey handlers ----
    def on_start() -> None:
        logger.info("Hotkey '%s' pressed -> START.", CFG.start_hotkey)
        bot.start()
        farm.start_farm()

    def on_stop() -> None:
        logger.info("Hotkey '%s' pressed -> STOP.", CFG.stop_hotkey)
        bot.stop()
        farm.stop_farm()

    def on_panic() -> None:
        logger.warning("PANIC hotkey '%s' pressed -> exiting.", CFG.panic_hotkey)
        bot.stop()
        farm.stop_farm()
        stop_flag.set()

    keyboard.add_hotkey(CFG.start_hotkey, on_start)
    keyboard.add_hotkey(CFG.stop_hotkey, on_stop)
    keyboard.add_hotkey(CFG.panic_hotkey, on_panic)

    logger.info("Hotkeys: start=%s stop=%s panic=%s",
                CFG.start_hotkey, CFG.stop_hotkey, CFG.panic_hotkey)
    logger.info("Press the panic hotkey to exit cleanly.")

    try:
        while not stop_flag.is_set():
            time.sleep(0.25)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received.")
    finally:
        stop_flag.set()
        bot.stop()
        farm.stop_farm()
        scanner.close()
        keyboard.unhook_all()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
