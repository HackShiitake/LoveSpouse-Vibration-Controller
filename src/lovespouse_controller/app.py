from __future__ import annotations

import logging
import signal
import threading

from .api import ApiServer
from .bluetooth import BluetoothLeToyDriver, DryRunToyDriver
from .config import AppConfig
from .patterns import PatternRepository
from .playback import PlaybackService
from .worker import CommandWorker

LOGGER = logging.getLogger(__name__)


class Application:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        driver = DryRunToyDriver() if config.dry_run else BluetoothLeToyDriver()
        self._worker = CommandWorker(driver)
        self._playback = PlaybackService(self._worker)
        self._api = ApiServer(config.host, config.port, self._playback)

    def run(self) -> None:
        if self._config.headless:
            self.run_headless()
            return
        self.run_gui()

    def run_headless(self) -> None:
        """Run the API + BLE backend with no GUI, blocking until terminated.

        Used when the controller is launched as a sidecar by another app (e.g.
        the Minecraft mod). Exits cleanly on Ctrl+C or a termination signal,
        sending a stop command on the way out.
        """

        stop_event = threading.Event()

        def _handle_signal(_signum, _frame):
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handle_signal)
            except (ValueError, OSError):
                pass  # not on the main thread / unsupported platform

        self._worker.start()
        self._api.start()
        LOGGER.info("headless mode ready; waiting for API commands")
        try:
            stop_event.wait()
        finally:
            LOGGER.info("shutting down")
            self._api.stop()
            self._playback.stop_all()
            self._worker.stop()

    def run_gui(self) -> None:
        # Imported lazily so headless/sidecar builds don't need tkinter.
        from .gui import ControllerWindow
        from .theme import THEMES

        repository = PatternRepository(self._config.pattern_dir)
        patterns = repository.load()
        window = ControllerWindow(
            self._playback,
            patterns,
            theme=THEMES[self._config.theme],
            reload_patterns=repository.load,
        )
        self._playback.set_status_callback(window.set_status)

        self._worker.start()
        self._api.start()
        try:
            window.run()
        finally:
            LOGGER.info("shutting down")
            self._api.stop()
            self._playback.stop_all()
            self._worker.stop()
