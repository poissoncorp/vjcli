from __future__ import annotations

from dataclasses import dataclass, field

from .music import MusicFrame

DEFAULT_AGGRESSION = 0.10
DEFAULT_DENSITY = 0.10

SCENE_HOLD = {
    "drive": 0.34,
    "fault": 0.30,
    "weight": 0.38,
    "rupture": 0.28,
    "chaos": 0.42,
}

PROFILE_EFFECTS = {
    "velvet": {
        "listen": "4",
        "drive": "6",
        "fault": "6",
        "weight": "5",
        "rupture": "9",
        "chaos": "8",
    },
    "house": {
        "listen": "4",
        "drive": "3",
        "fault": "6",
        "weight": "5",
        "rupture": "4",
        "chaos": "8",
    },
    "acid": {
        "listen": "7",
        "drive": "6",
        "fault": "7",
        "weight": "7",
        "rupture": "9",
        "chaos": "1",
    },
    "spectral": {
        "listen": "4",
        "drive": "6",
        "fault": "7",
        "weight": "5",
        "rupture": "9",
        "chaos": "8",
    },
    "industrial": {
        "listen": "6",
        "drive": "6",
        "fault": "7",
        "weight": "8",
        "rupture": "2",
        "chaos": "1",
    },
    "hard": {
        "listen": "3",
        "drive": "1",
        "fault": "7",
        "weight": "8",
        "rupture": "2",
        "chaos": "1",
    },
}

PROFILE_ALTERNATES = {
    "velvet": {"6": "4", "4": "5", "5": "6", "8": "9", "9": "8"},
    "house": {"3": "4", "4": "5", "5": "3", "6": "4", "8": "5"},
    "acid": {"7": "6", "6": "7", "9": "7", "1": "8"},
    "spectral": {"4": "6", "6": "7", "7": "4", "5": "8", "9": "8"},
    "industrial": {"6": "7", "7": "8", "8": "2", "2": "9", "1": "8"},
    "hard": {"1": "8", "8": "2", "2": "9", "9": "1", "7": "1"},
}


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
    transition_strength: float | None = None
    effect_key: str | None = None
    scene: str = "idle"
    scene_age: float = 0.0
    pressure: float = 0.0
    trigger_score: float = 0.0
    status: str | None = None


@dataclass
class MusicReactor:
    tuning: MusicTuning = field(default_factory=MusicTuning)
    last_onset_at: float = -999.0
    last_effect_at: float = -999.0
    last_frame_at: float = -999.0
    scene_started_at: float = -999.0
    last_scene: str = "idle"
    last_effect_key: str | None = None
    effect_repeat: int = 0
    frames_seen: int = 0
    pressure: float = 0.0

    def react(
        self,
        frame: MusicFrame,
        now: float,
        aggression: float,
        density: float,
        profile: str | None = None,
    ) -> MusicReaction:
        dt = self._frame_dt(now)
        if frame.confidence < self.tuning.confidence_threshold:
            self.frames_seen = 0
            self.pressure = _follow(self.pressure, 0.0, _attack(dt, 0.8))
            return MusicReaction(
                _follow(aggression, DEFAULT_AGGRESSION, 0.05),
                _follow(density, DEFAULT_DENSITY, 0.05),
                scene="idle",
                scene_age=self._set_scene("idle", now),
                pressure=self.pressure,
            )

        self.frames_seen += 1
        self._update_pressure(frame, dt)
        scene = self._stabilized_scene(_scene(frame, self.pressure), frame, now)
        scene_age = self._set_scene(scene, now)
        scene_entered = scene_age == 0.0
        score = _trigger_score(frame, self.pressure)
        transition_strength = (
            _transition_strength(frame, scene, self.pressure)
            if scene_entered and self.frames_seen > 1
            else None
        )
        next_aggression = _clamp(
            max(
                DEFAULT_AGGRESSION,
                DEFAULT_AGGRESSION + frame.drive * 0.62 + self.pressure * 0.28,
            )
        )
        next_density = _clamp(
            max(
                DEFAULT_DENSITY,
                DEFAULT_DENSITY + frame.mass * 0.50 + self.pressure * 0.20,
            )
        )
        effect_key = (
            self._effect_key(frame, now, scene, scene_age, scene_entered, score, profile)
            if self.frames_seen > 1
            else None
        )
        if frame.onset < self.tuning.onset_threshold:
            return MusicReaction(
                next_aggression,
                next_density,
                effect_key=effect_key,
                transition_strength=transition_strength,
                scene=scene,
                scene_age=scene_age,
                pressure=self.pressure,
                trigger_score=score,
            )
        if now - self.last_onset_at < self.tuning.onset_debounce:
            return MusicReaction(
                next_aggression,
                next_density,
                effect_key=effect_key,
                transition_strength=transition_strength,
                scene=scene,
                scene_age=scene_age,
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
            transition_strength=transition_strength,
            effect_key=effect_key,
            scene=scene,
            scene_age=scene_age,
            pressure=self.pressure,
            trigger_score=score,
            status=f"MUSIC {scene.upper()}",
        )

    def _set_scene(self, scene: str, now: float) -> float:
        if scene != self.last_scene:
            self.last_scene = scene
            self.scene_started_at = now
            return 0.0
        if self.scene_started_at < 0.0:
            self.scene_started_at = now
        return max(0.0, now - self.scene_started_at)

    def _stabilized_scene(self, scene: str, frame: MusicFrame, now: float) -> str:
        current = self.last_scene
        if scene == current or current in ("idle", "listen"):
            return scene
        if _scene_breaks_hold(scene, frame, self.pressure):
            return scene
        if self.scene_started_at < 0.0:
            return scene
        age = max(0.0, now - self.scene_started_at)
        if age >= SCENE_HOLD.get(current, 0.0):
            return scene
        return current

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

    def _effect_key(
        self,
        frame: MusicFrame,
        now: float,
        scene: str,
        scene_age: float,
        scene_entered: bool,
        score: float,
        profile: str | None,
    ) -> str | None:
        debounce = self.tuning.effect_debounce
        if scene_entered:
            debounce *= 0.45
        if now - self.last_effect_at < debounce:
            return None
        threshold = self.tuning.effect_threshold
        if scene_entered or scene_age < 0.35:
            threshold = max(0.0, threshold - 0.08)
        if score < threshold:
            return None
        self.last_effect_at = now
        key = _candidate_key(frame, scene, scene_age, self.pressure, profile)
        key = self._avoid_repeat(key, scene, profile)
        self._remember_effect(key)
        return key

    def _avoid_repeat(self, key: str, scene: str, profile: str | None) -> str:
        if key != self.last_effect_key or self.effect_repeat < 1:
            return key
        return _alternate_key(scene, key, profile)

    def _remember_effect(self, key: str) -> None:
        if key == self.last_effect_key:
            self.effect_repeat += 1
            return
        self.last_effect_key = key
        self.effect_repeat = 0


def _candidate_key(
    frame: MusicFrame,
    scene: str,
    scene_age: float,
    pressure: float,
    profile: str | None,
) -> str:
    if scene == "chaos" and frame.drive > 0.78 and frame.mass > 0.58:
        return "1"
    if scene == "rupture" and pressure > 0.68 and scene_age < 0.90:
        return "2"
    if profile is not None:
        key = PROFILE_EFFECTS.get(profile, {}).get(scene)
        if key is not None:
            return key
    if scene == "rupture" and pressure > 0.62:
        return "1"
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


def _alternate_key(scene: str, key: str, profile: str | None) -> str:
    if profile is not None:
        key = PROFILE_ALTERNATES.get(profile, {}).get(key, key)
        return key
    alternatives = {
        "drive": {"3": "4", "4": "6"},
        "fault": {"7": "6", "6": "4"},
        "weight": {"5": "8", "8": "3"},
        "rupture": {"9": "2", "2": "9", "1": "9"},
        "chaos": {"1": "8", "8": "9", "9": "2"},
    }
    return alternatives.get(scene, {}).get(key, key)


def _transition_strength(frame: MusicFrame, scene: str, pressure: float) -> float | None:
    if scene in ("idle", "listen"):
        return None
    base = {
        "drive": 0.36,
        "fault": 0.42,
        "weight": 0.50,
        "rupture": 0.72,
        "chaos": 0.88,
    }.get(scene)
    if base is None:
        return None
    strength = base + pressure * 0.20 + frame.change * 0.14 + frame.bass * 0.08
    return _clamp(strength)


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


def _scene_breaks_hold(scene: str, frame: MusicFrame, pressure: float) -> bool:
    if scene == "rupture":
        return True
    if scene == "chaos":
        return pressure > 0.78 or frame.drive > 0.88
    return False


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
