from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from .models import Pattern, VibrationCommand

LOGGER = logging.getLogger(__name__)


class PatternRepository:
    def __init__(self, pattern_dir: Path) -> None:
        self._pattern_dir = pattern_dir

    def load(self) -> Dict[str, Pattern]:
        patterns: Dict[str, Pattern] = {}
        if not self._pattern_dir.is_dir():
            LOGGER.warning("pattern directory does not exist: %s", self._pattern_dir)
            return patterns

        for path in sorted(self._pattern_dir.glob("*.vibepattern")):
            try:
                pattern = self._read_pattern(path)
            except Exception:
                LOGGER.exception("failed to load pattern: %s", path)
                continue
            if pattern.commands:
                patterns[pattern.display_name] = pattern
        return patterns

    def _read_pattern(self, path: Path) -> Pattern:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            return Pattern.from_commands(path.stem, "", ())

        name = path.stem
        author = ""
        start_index = 0
        try:
            header = json.loads(lines[0])
            name = header.get("name", name)
            author = header.get("author", "")
            start_index = 1
        except json.JSONDecodeError:
            LOGGER.warning("pattern has no JSON header: %s", path)

        commands = []
        for line in lines[start_index:]:
            try:
                commands.append(VibrationCommand.parse(line))
            except ValueError:
                LOGGER.warning("skipping invalid pattern command '%s' in %s", line, path)
        return Pattern.from_commands(name, author, commands)
