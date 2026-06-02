from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Protocol


@dataclass(frozen=True)
class MusicFrame:
    energy: float = 0.0
    bass: float = 0.0
    brightness: float = 0.0
    density: float = 0.0
    onset: float = 0.0
    change: float = 0.0
    confidence: float = 0.0
    beat_interval: float = 0.0
    beat_phase: float = 0.0
    beat_confidence: float = 0.0

    def __post_init__(self) -> None:
        for field in fields(self):
            value = float(getattr(self, field.name))
            if field.name == "beat_interval":
                object.__setattr__(self, field.name, max(0.0, value))
            else:
                object.__setattr__(self, field.name, _clamp(value))

    @property
    def drive(self) -> float:
        return max(self.energy, self.onset * 0.86, self.bass * 0.62)

    @property
    def mass(self) -> float:
        return max(self.density, self.bass * 0.78)

    @property
    def beat_bpm(self) -> float:
        if self.beat_interval <= 0.0:
            return 0.0
        return 60.0 / self.beat_interval


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class MusicSource(Protocol):
    def poll(self, now: float) -> MusicFrame | None:
        ...
