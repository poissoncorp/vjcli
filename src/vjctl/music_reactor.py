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
    scene: str = "idle"
    pressure: float = 0.0
    trigger_score: float = 0.0
    status: str | None = None


@dataclass
class MusicReactor:
    tuning: MusicTuning = field(default_factory=MusicTuning)
    last_onset_at: float = -999.0
    last_effect_at: float = -999.0
    last_frame_at: float = -999.0
    frames_seen: int = 0
    pressure: float = 0.0

    def react(
        self,
        frame: MusicFrame,
        now: float,
        aggression: float,
        density: float,
    ) -> MusicReaction:
        dt = self._frame_dt(now)
        if frame.confidence < self.tuning.confidence_threshold:
            self.frames_seen = 0
            self.pressure = _follow(self.pressure, 0.0, _attack(dt, 0.8))
            return MusicReaction(
                _follow(aggression, DEFAULT_AGGRESSION, 0.05),
                _follow(density, DEFAULT_DENSITY, 0.05),
                scene="idle",
                pressure=self.pressure,
            )

        self.frames_seen += 1
        self._update_pressure(frame, dt)
        scene = _scene(frame, self.pressure)
        score = _trigger_score(frame, self.pressure)
        next_aggression = _clamp(
            max(DEFAULT_AGGRESSION, DEFAULT_AGGRESSION + frame.drive * 0.62 + self.pressure * 0.28)
        )
        next_density = _clamp(
            max(DEFAULT_DENSITY, DEFAULT_DENSITY + frame.mass * 0.50 + self.pressure * 0.20)
        )
        effect_key = self._effect_key(frame, now, scene, score) if self.frames_seen > 1 else None
        if frame.onset < self.tuning.onset_threshold:
            return MusicReaction(
                next_aggression,
                next_density,
                effect_key=effect_key,
                scene=scene,
                pressure=self.pressure,
                trigger_score=score,
            )
        if now - self.last_onset_at < self.tuning.onset_debounce:
            return MusicReaction(
                next_aggression,
                next_density,
                effect_key=effect_key,
                scene=scene,
                pressure=self.pressure,
                trigger_score=score,
            )

        strength = _clamp(
            max(0.34, frame.onset * 0.82 + frame.bass * 0.28 + frame.change * 0.18)
        )
        self.last_onset_at = now
        return MusicReaction(
            next_aggression,
            next_density,
            wave_strength=strength,
            effect_key=effect_key,
            scene=scene,
            pressure=self.pressure,
            trigger_score=score,
            status=f"MUSIC {scene.upper()}",
        )

    def _frame_dt(self, now: float) -> float:
        if self.last_frame_at < 0.0:
            self.last_frame_at = now
            return 1.0 / 60.0
        dt = max(0.0, min(1.0, now - self.last_frame_at))
        self.last_frame_at = now
        return dt

    def _update_pressure(self, frame: MusicFrame, dt: float) -> None:
        target = _clamp(
            frame.drive * 0.42 + frame.mass * 0.30 + frame.change * 0.22 + frame.onset * 0.16
        )
        speed = 7.0 if target > self.pressure else 1.2
        self.pressure = _follow(self.pressure, target, _attack(dt, speed))

    def _effect_key(self, frame: MusicFrame, now: float, scene: str, score: float) -> str | None:
        if now - self.last_effect_at < self.tuning.effect_debounce:
            return None
        if score < self.tuning.effect_threshold:
            return None
        self.last_effect_at = now
        if scene == "chaos" and frame.drive > 0.78 and frame.mass > 0.58:
            return "1"
        if scene == "rupture" and self.pressure > 0.62:
            return "2"
        if scene == "rupture":
            return "9"
        if scene == "chaos":
            return "8"
        if scene == "fault":
            return "7"
        if scene == "weight":
            return "5"
        if scene == "drive":
            return "3"
        return "4"


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _attack(dt: float, speed: float) -> float:
    return max(0.0, min(1.0, dt * speed))


def _scene(frame: MusicFrame, pressure: float) -> str:
    if frame.change > 0.72 and frame.onset > 0.62:
        return "rupture"
    if pressure > 0.72 or frame.drive > 0.86:
        return "chaos"
    if frame.mass > 0.58:
        return "weight"
    if frame.brightness > 0.56 and frame.change > 0.34:
        return "fault"
    if frame.drive > 0.42 or pressure > 0.38:
        return "drive"
    return "listen"


def _trigger_score(frame: MusicFrame, pressure: float) -> float:
    return _clamp(
        max(
            frame.onset,
            frame.change * 0.94,
            frame.drive * 0.58 + pressure * 0.28 + frame.change * 0.18,
        )
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
