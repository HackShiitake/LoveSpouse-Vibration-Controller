from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from .models import Pattern, VibrationCommand
from .worker import CommandWorker

LOGGER = logging.getLogger(__name__)
StatusCallback = Callable[[str], None]


class PlaybackService:
    def __init__(self, worker: CommandWorker, on_status: Optional[StatusCallback] = None) -> None:
        self._worker = worker
        self._on_status = on_status or (lambda status: None)
        self._continuous_stop = threading.Event()
        self._pattern_stop = threading.Event()
        self._continuous_thread: Optional[threading.Thread] = None
        self._pattern_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def set_status_callback(self, on_status: StatusCallback) -> None:
        self._on_status = on_status

    def pulse(self, command: VibrationCommand, source: str = "api") -> None:
        self._worker.enqueue(command, source=source)

    def start_continuous(self, strength: int) -> None:
        with self._lock:
            self.stop_continuous(send_stop=False)
            if strength <= 0:
                self.stop_all()
                return

            self._pattern_stop.set()
            self._continuous_stop.clear()
            self._continuous_thread = threading.Thread(
                target=self._continuous_loop,
                args=(strength,),
                name="continuous-playback",
                daemon=True,
            )
            self._continuous_thread.start()
            self._on_status(f"Running - Level {strength}")

    def stop_continuous(self, send_stop: bool = True) -> None:
        self._continuous_stop.set()
        thread = self._continuous_thread
        if thread and thread.is_alive():
            thread.join(timeout=1)
        self._continuous_thread = None
        if send_stop:
            self._worker.enqueue(VibrationCommand(0, 0.05), source="continuous-stop")

    def play_pattern(self, pattern: Pattern) -> None:
        with self._lock:
            self.stop_continuous(send_stop=False)
            self._pattern_stop.set()
            thread = self._pattern_thread
            if thread and thread.is_alive():
                thread.join(timeout=1)

            self._pattern_stop.clear()
            self._pattern_thread = threading.Thread(
                target=self._pattern_loop,
                args=(pattern,),
                name=f"pattern-{pattern.name}",
                daemon=True,
            )
            self._pattern_thread.start()
            self._on_status(f"Playing - {pattern.name}")

    def stop_all(self) -> None:
        self._pattern_stop.set()
        self.stop_continuous(send_stop=False)
        thread = self._pattern_thread
        if thread and thread.is_alive():
            thread.join(timeout=1)
        self._pattern_thread = None
        self._worker.enqueue(VibrationCommand(0, 0.05), source="stop-all")
        self._on_status("Stopped")

    def _continuous_loop(self, strength: int) -> None:
        while not self._continuous_stop.is_set():
            self._worker.enqueue(VibrationCommand(strength, 0.1), source="continuous")
            time.sleep(0.1)

    def _pattern_loop(self, pattern: Pattern) -> None:
        try:
            while not self._pattern_stop.is_set():
                for command in pattern.commands:
                    if self._pattern_stop.is_set():
                        break
                    self._worker.enqueue(command, source=f"pattern:{pattern.name}")
                    time.sleep(command.duration_seconds)
        finally:
            self._worker.enqueue(VibrationCommand(0, 0.05), source="pattern-stop")
            self._on_status("Ready")
