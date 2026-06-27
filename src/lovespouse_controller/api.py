from __future__ import annotations

import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from .models import VibrationCommand
from .playback import PlaybackService

LOGGER = logging.getLogger(__name__)
API_PATH_PATTERN = re.compile(r"^/API/(?P<command>\d+-\d+(?:\.\d+)?(?:ms|s))$")


class ApiServer:
    def __init__(self, host: str, port: int, playback: PlaybackService) -> None:
        self._host = host
        self._port = port
        self._playback = playback
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        handler = self._build_handler()
        self._server = ThreadingHTTPServer((self._host, self._port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="http-api-server",
            daemon=True,
        )
        self._thread.start()
        LOGGER.info("HTTP API listening on http://%s:%s", self._host, self._port)

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _build_handler(self):
        playback = self._playback

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                path = urlparse(self.path).path
                match = API_PATH_PATTERN.match(path)
                if not match:
                    self._json_response(
                        200,
                        {
                            "status": "ready",
                            "usage": "GET /API/{strength}-{duration}{unit}",
                            "example": "/API/5-1000ms",
                        },
                    )
                    return

                try:
                    command = VibrationCommand.parse(match.group("command"))
                    playback.pulse(command, source="http-api")
                except ValueError as exc:
                    self._json_response(400, {"error": str(exc)})
                    return
                except Exception as exc:
                    LOGGER.exception("API command failed")
                    self._json_response(500, {"error": str(exc)})
                    return

                self._json_response(
                    200,
                    {
                        "status": "ok",
                        "strength": command.strength,
                        "duration": command.original_duration,
                    },
                )

            def _json_response(self, status: int, payload: dict) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args) -> None:
                LOGGER.debug("HTTP %s", format % args)

        return RequestHandler
