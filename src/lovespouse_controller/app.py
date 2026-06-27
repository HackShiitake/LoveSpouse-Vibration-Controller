from __future__ import annotations

import logging

from .api import ApiServer
from .bluetooth import BluetoothLeToyDriver, DryRunToyDriver
from .config import AppConfig
from .gui import ControllerWindow
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
        patterns = PatternRepository(self._config.pattern_dir).load()
        window = ControllerWindow(self._playback, patterns)
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
