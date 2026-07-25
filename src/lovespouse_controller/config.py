from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 4545
    pattern_dir: Path = default_project_root() / "pattern"
    dry_run: bool = False
    log_level: str = "INFO"
    theme: str = "light"
    headless: bool = False

    @classmethod
    def from_args(cls) -> "AppConfig":
        # Imported here to avoid pulling tkinter into non-GUI code paths.
        from .theme import THEMES

        parser = argparse.ArgumentParser(
            prog="lovespouse-controller",
            description="Desktop GUI and local HTTP API for Bluetooth LE vibration control.",
        )
        parser.add_argument("--host", default=cls.host, help="HTTP API bind host.")
        parser.add_argument("--port", type=int, default=cls.port, help="HTTP API port.")
        parser.add_argument(
            "--pattern-dir",
            type=Path,
            default=cls.pattern_dir,
            help="Directory containing .vibepattern files.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log Bluetooth commands instead of advertising them.",
        )
        parser.add_argument(
            "--log-level",
            default=cls.log_level,
            choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            help="Application log level.",
        )
        parser.add_argument(
            "--theme",
            default=cls.theme,
            choices=tuple(THEMES),
            help="UI color theme.",
        )
        parser.add_argument(
            "--headless",
            action="store_true",
            help="Run the HTTP API and BLE backend without the GUI (for use as a sidecar).",
        )
        args = parser.parse_args()
        return cls(
            host=args.host,
            port=args.port,
            pattern_dir=args.pattern_dir,
            dry_run=args.dry_run,
            log_level=args.log_level,
            theme=args.theme,
            headless=args.headless,
        )
