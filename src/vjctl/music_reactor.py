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
    effect_threshold: float = 0.74
    effect_debounce: float = 0.58


@dataclass(frozen=True)
class MusicReaction:
    aggression: float
    density: float
    wave_strength: float | None = None
    effect_key: str | None = None
    status: str | None = None


@dataclass
class MusicReactor:
    tuning: MusicTuning = field(default_factory=MusicTuning)
    last_onset_at: float = -999.0
    last_effect_at: float = -999.0
    frames_seen: int = 0

    def react(
        self,
        frame: MusicFrame,
        now: float,
        aggression: float,
        density: float,
    ) -> MusicReaction:
        if frame.confidence < self.tuning.confidence_threshold:
            self.frames_seen = 0
            return MusicReaction(
                _follow(aggression, DEFAULT_AGGRESSION, 0.05),
                _follow(density, DEFAULT_DENSITY, 0.05),
            )

        self.frames_seen += 1
        next_aggression = _clamp(
            max(DEFAULT_AGGRESSION, DEFAULT_AGGRESSION + frame.drive * 0.84)
        )
        next_density = _clamp(max(DEFAULT_DENSITY, DEFAULT_DENSITY + frame.mass * 0.62))
        effect_key = self._effect_key(frame, now) if self.frames_seen > 1 else None
        if frame.onset < self.tuning.onset_threshold:
            return MusicReaction(next_aggression, next_density, effect_key=effect_key)
        if now - self.last_onset_at < self.tuning.onset_debounce:
            return MusicReaction(next_aggression, next_density, effect_key=effect_key)

        strength = _clamp(
            max(0.34, frame.onset * 0.82 + frame.bass * 0.28 + frame.change * 0.18)
        )
        self.last_onset_at = now
        return MusicReaction(
            next_aggression,
            next_density,
            wave_strength=strength,
            effect_key=effect_key,
            status="MUSIC ONSET",
        )

    def _effect_key(self, frame: MusicFrame, now: float) -> str | None:
        if now - self.last_effect_at < self.tuning.effect_debounce:
            return None
        score = max(frame.onset, frame.change * 0.94, frame.drive * 0.78 + frame.change * 0.2)
        if score < self.tuning.effect_threshold:
            return None
        self.last_effect_at = now
        if frame.drive > 0.86 and frame.mass > 0.70 and frame.onset > 0.68:
            return "1"
        if frame.change > 0.82 and frame.energy > 0.56:
            return "9"
        if frame.onset > 0.84 and frame.change > 0.58:
            return "2"
        if frame.bass > 0.70 and frame.onset > 0.60:
            return "8"
        if frame.brightness > 0.62 and frame.change > 0.42:
            return "7"
        if frame.density > 0.66 and frame.bass > 0.42:
            return "5"
        if frame.density > 0.56:
            return "3"
        if frame.brightness > 0.50:
            return "6"
        return "4"


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
