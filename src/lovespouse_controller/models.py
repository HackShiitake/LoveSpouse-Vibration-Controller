from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Tuple


COMMAND_PATTERN = re.compile(r"^(?P<strength>\d+)-(?P<duration>\d+(?:\.\d+)?)(?P<unit>ms|s|m|h)$")

_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


@dataclass(frozen=True)
class VibrationCommand:
    strength: int
    duration_seconds: float
    original_duration: str = ""

    def __post_init__(self) -> None:
        clamped_strength = max(0, min(9, int(self.strength)))
        if clamped_strength != self.strength:
            object.__setattr__(self, "strength", clamped_strength)
        if self.duration_seconds < 0:
            raise ValueError("duration must be greater than or equal to 0")

    @classmethod
    def parse(cls, text: str) -> "VibrationCommand":
        match = COMMAND_PATTERN.match(text.strip())
        if not match:
            raise ValueError("expected command format '<strength>-<duration><ms|s>'")

        value = float(match.group("duration"))
        unit = match.group("unit")
        seconds = value * _UNIT_SECONDS[unit]
        return cls(
            strength=int(match.group("strength")),
            duration_seconds=seconds,
            original_duration=f"{match.group('duration')}{unit}",
        )


@dataclass(frozen=True)
class Pattern:
    name: str
    author: str
    commands: Tuple[VibrationCommand, ...]

    @property
    def display_name(self) -> str:
        return f"{self.name} by {self.author}" if self.author else self.name

    @classmethod
    def from_commands(
        cls, name: str, author: str, commands: Iterable[VibrationCommand]
    ) -> "Pattern":
        return cls(name=name, author=author, commands=tuple(commands))
