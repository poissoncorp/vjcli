from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MusicFrame:
    energy: float = 0.0
    bass: float = 0.0
    brightness: float = 0.0
    density: float = 0.0
    onset: float = 0.0
    change: float = 0.0
    confidence: float = 0.0

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _clamp(getattr(self, name)))

    @property
    def drive(self) -> float:
        return max(self.energy, self.onset * 0.86, self.bass * 0.62)

    @property
    def mass(self) -> float:
        return max(self.density, self.bass * 0.78)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
