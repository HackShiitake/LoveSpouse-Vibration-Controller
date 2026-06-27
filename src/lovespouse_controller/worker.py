from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass
from typing import Optional

from .bluetooth import ToyDriver
from .models import VibrationCommand

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueuedCommand:
    command: VibrationCommand
    source: str = "unknown"


class CommandWorker:
    def __init__(self, driver: ToyDriver) -> None:
        self._driver = driver
        self._queue: "queue.Queue[Optional[QueuedCommand]]" = queue.Queue()
        self._thread = threading.Thread(
            target=self._run,
            name="bluetooth-command-worker",
            daemon=True,
        )
        self._started = threading.Event()

    def start(self) -> None:
        if self._thread.is_alive():
            return
        self._thread.start()
        self._started.wait(timeout=2)

    def enqueue(self, command: VibrationCommand, source: str = "unknown") -> None:
        self._queue.put(QueuedCommand(command=command, source=source))

    def stop(self) -> None:
        self.enqueue(VibrationCommand(0, 0.05), source="shutdown")
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=3)

    def _run(self) -> None:
        self._started.set()
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                return

            command = item.command
            try:
                LOGGER.debug(
                    "sending command source=%s strength=%s duration=%.3fs",
                    item.source,
                    command.strength,
                    command.duration_seconds,
                )
                self._driver.send(command.strength, command.duration_seconds)
            except Exception:
                LOGGER.exception("command failed source=%s", item.source)
            finally:
                self._queue.task_done()
