from __future__ import annotations

from dataclasses import dataclass, field

from .music import MusicFrame

DEFAULT_AGGRESSION = 0.10
DEFAULT_DENSITY = 0.10


@dataclass(frozen=True)
class MusicTuning:
    confidence_threshold: float = 0.08
    onset_threshold: float = 0.58
    onset_debounce: float = 0.12


@dataclass(frozen=True)
class MusicReaction:
    aggression: float
    density: float
    wave_strength: float | None = None
    status: str | None = None


@dataclass
class MusicReactor:
    tuning: MusicTuning = field(default_factory=MusicTuning)
    last_onset_at: float = -999.0

    def react(
        self,
        frame: MusicFrame,
        now: float,
        aggression: float,
        density: float,
    ) -> MusicReaction:
        if frame.confidence < self.tuning.confidence_threshold:
            return MusicReaction(
                _follow(aggression, DEFAULT_AGGRESSION, 0.05),
                _follow(density, DEFAULT_DENSITY, 0.05),
            )

        next_aggression = _clamp(
            max(DEFAULT_AGGRESSION, DEFAULT_AGGRESSION + frame.drive * 0.84)
        )
        next_density = _clamp(max(DEFAULT_DENSITY, DEFAULT_DENSITY + frame.mass * 0.62))
        if frame.onset < self.tuning.onset_threshold:
            return MusicReaction(next_aggression, next_density)
        if now - self.last_onset_at < self.tuning.onset_debounce:
            return MusicReaction(next_aggression, next_density)

        strength = _clamp(
            max(0.34, frame.onset * 0.82 + frame.bass * 0.28 + frame.change * 0.18)
        )
        self.last_onset_at = now
        return MusicReaction(next_aggression, next_density, strength, "MUSIC ONSET")


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
