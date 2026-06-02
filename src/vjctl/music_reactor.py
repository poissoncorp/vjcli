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
class MusicMood:
    profile: str
    confidence: float
    impact: float
    weight: float
    grit: float
    spark: float
    space: float
    motion: float


@dataclass(frozen=True)
class MusicTuning:
    confidence_threshold: float = 0.08
    onset_threshold: float = 0.64
    onset_debounce: float = 0.18
    effect_threshold: float = 0.82
    effect_debounce: float = 0.78


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
        mood: MusicMood | None = None,
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
        response = _tempo_response(frame)
        self._update_pressure(frame, dt, response)
        scene = self._stabilized_scene(_scene(frame, self.pressure, response, mood), frame, now)
        scene_age = self._set_scene(scene, now)
        scene_entered = scene_age == 0.0
        score = _trigger_score(frame, self.pressure, response)
        transition_strength = (
            _transition_strength(frame, scene, self.pressure, response)
            if scene_entered and self.frames_seen > 1
            else None
        )
        next_aggression = _clamp(
            max(
                DEFAULT_AGGRESSION,
                DEFAULT_AGGRESSION
                + frame.drive * (0.34 + response * 0.28)
                + self.pressure * (0.14 + response * 0.14),
            )
        )
        next_density = _clamp(
            max(
                DEFAULT_DENSITY,
                DEFAULT_DENSITY
                + frame.mass * (0.30 + response * 0.20)
                + self.pressure * (0.10 + response * 0.10),
            )
        )
        effect_key = (
            self._effect_key(
                frame,
                now,
                scene,
                scene_age,
                scene_entered,
                score,
                mood,
                response,
            )
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
        onset_debounce = self.tuning.onset_debounce + (1.0 - response) * 0.18
        if now - self.last_onset_at < onset_debounce:
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

        strength = _wave_strength(frame, response)
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

    def _update_pressure(self, frame: MusicFrame, dt: float, response: float) -> None:
        target = _clamp(
            frame.drive * 0.32
            + frame.mass * 0.22
            + frame.change * 0.18
            + frame.onset * 0.10
        )
        target *= 0.56 + response * 0.44
        speed = (3.4 + response * 3.6) if target > self.pressure else 1.2
        self.pressure = _follow(self.pressure, target, _attack(dt, speed))

    def _effect_key(
        self,
        frame: MusicFrame,
        now: float,
        scene: str,
        scene_age: float,
        scene_entered: bool,
        score: float,
        mood: MusicMood | None,
        response: float,
    ) -> str | None:
        debounce = self.tuning.effect_debounce + (1.0 - response) * 0.46
        if mood is not None:
            debounce *= _mood_debounce_scale(mood)
        if scene_entered:
            debounce *= 0.62
        if now - self.last_effect_at < debounce:
            return None
        threshold = self.tuning.effect_threshold + (1.0 - response) * 0.18
        if mood is not None:
            threshold += _mood_threshold_shift(mood, scene)
        if scene_entered or scene_age < 0.35:
            threshold = max(0.0, threshold - 0.05 * response)
        if score < threshold:
            return None
        self.last_effect_at = now
        key = _candidate_key(frame, scene, scene_age, self.pressure, mood)
        key = self._avoid_repeat(key, scene, mood)
        self._remember_effect(key)
        return key

    def _avoid_repeat(self, key: str, scene: str, mood: MusicMood | None) -> str:
        if key != self.last_effect_key or self.effect_repeat < 1:
            return key
        return _alternate_key(scene, key, mood)

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
    mood: MusicMood | None,
) -> str:
    if mood is not None:
        key = _mood_key(scene, pressure, mood)
        if key is not None:
            return key
    if scene == "chaos" and frame.drive > 0.78 and frame.mass > 0.58:
        return "1"
    if scene == "rupture" and pressure > 0.68 and scene_age < 0.90:
        return "2"
    if mood is not None:
        key = PROFILE_EFFECTS.get(mood.profile, {}).get(scene)
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


def _mood_key(scene: str, pressure: float, mood: MusicMood) -> str | None:
    if _mood_certainty(mood) < 0.20:
        return None
    if mood.motion > 0.40 and mood.impact > 0.46:
        return "8" if mood.weight > 0.50 or pressure > 0.52 else "7"
    if mood.space > 0.68 and mood.impact < 0.36:
        return "6" if scene in ("drive", "fault") else "5"
    if mood.spark > 0.70 and scene in ("drive", "fault", "weight"):
        return "7"
    if mood.grit > 0.68 and scene in ("rupture", "chaos"):
        return "2" if mood.impact > 0.56 else "9"
    if mood.weight > 0.70 and scene in ("weight", "chaos"):
        return "8"
    if mood.impact > 0.76 and scene in ("listen", "drive"):
        return "4"
    return None


def _alternate_key(scene: str, key: str, mood: MusicMood | None) -> str:
    if mood is not None:
        key = PROFILE_ALTERNATES.get(mood.profile, {}).get(key, key)
        return key
    alternatives = {
        "drive": {"3": "4", "4": "6"},
        "fault": {"7": "6", "6": "4"},
        "weight": {"5": "8", "8": "3"},
        "rupture": {"9": "2", "2": "9", "1": "9"},
        "chaos": {"1": "8", "8": "9", "9": "2"},
    }
    return alternatives.get(scene, {}).get(key, key)


def _mood_debounce_scale(mood: MusicMood) -> float:
    certainty = _mood_certainty(mood)
    scale = 1.0
    scale -= mood.motion * certainty * 0.16
    scale -= max(mood.impact, mood.grit) * certainty * 0.08
    scale += mood.space * max(0.0, 1.0 - mood.impact) * certainty * 0.18
    return max(0.72, min(1.18, scale))


def _mood_threshold_shift(mood: MusicMood, scene: str) -> float:
    certainty = _mood_certainty(mood)
    shift = 0.0
    shift -= mood.motion * certainty * 0.08
    shift -= mood.impact * certainty * 0.04
    if scene in ("drive", "fault"):
        shift -= mood.spark * certainty * 0.04
    if scene in ("weight", "rupture", "chaos"):
        shift -= max(mood.weight, mood.grit) * certainty * 0.04
    shift += mood.space * max(0.0, 1.0 - mood.impact) * certainty * 0.08
    return max(-0.14, min(0.10, shift))


def _mood_certainty(mood: MusicMood) -> float:
    return _clamp((mood.confidence - 0.14) / 0.34)


def _transition_strength(
    frame: MusicFrame,
    scene: str,
    pressure: float,
    response: float,
) -> float | None:
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
    strength = base + pressure * 0.16 + frame.change * 0.10 + frame.bass * 0.06
    strength *= 0.58 + response * 0.42
    return _clamp(strength)


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _attack(dt: float, speed: float) -> float:
    return max(0.0, min(1.0, dt * speed))


def _scene(
    frame: MusicFrame,
    pressure: float,
    response: float,
    mood: MusicMood | None = None,
) -> str:
    restraint = 1.0 - response
    rupture_change = 0.72 + restraint * 0.14
    rupture_onset = 0.62 + restraint * 0.10
    chaos_pressure = 0.72 + restraint * 0.14
    chaos_drive = 0.86 + restraint * 0.08
    weight_mass = 0.58 + restraint * 0.08
    drive_amount = 0.42 + restraint * 0.10
    drive_pressure = 0.38 + restraint * 0.10
    scene = "listen"
    if frame.change > rupture_change and frame.onset > rupture_onset:
        scene = "rupture"
    elif pressure > chaos_pressure or frame.drive > chaos_drive:
        scene = "chaos"
    elif frame.mass > weight_mass:
        scene = "weight"
    elif frame.brightness > 0.56 and frame.change > 0.34:
        scene = "fault"
    elif frame.drive > drive_amount or pressure > drive_pressure:
        scene = "drive"
    return _mood_scene(scene, frame, pressure, mood)


def _mood_scene(
    scene: str,
    frame: MusicFrame,
    pressure: float,
    mood: MusicMood | None,
) -> str:
    if mood is None or _mood_certainty(mood) < 0.20:
        return scene
    if mood.motion > 0.48 and mood.impact > 0.52:
        return "rupture" if pressure < 0.74 else "chaos"
    if mood.space > 0.72 and mood.impact < 0.40 and pressure < 0.54:
        return "fault" if mood.spark > 0.56 else "listen"
    if mood.spark > 0.72 and frame.change > 0.24 and scene in ("listen", "drive", "weight"):
        return "fault"
    if mood.weight > 0.70 and scene in ("listen", "drive", "fault"):
        return "weight"
    if mood.grit > 0.72 and pressure > 0.48 and scene in ("drive", "fault", "weight"):
        return "rupture"
    return scene


def _scene_breaks_hold(scene: str, frame: MusicFrame, pressure: float) -> bool:
    if scene == "rupture":
        return True
    if scene == "chaos":
        return pressure > 0.78 or frame.drive > 0.88
    return False


def _trigger_score(frame: MusicFrame, pressure: float, response: float) -> float:
    return _clamp(
        max(
            frame.onset * (0.58 + response * 0.42),
            frame.change * (0.52 + response * 0.42),
            frame.drive * (0.42 + response * 0.16)
            + pressure * (0.18 + response * 0.10)
            + frame.change * (0.10 + response * 0.08),
        )
    )


def _wave_strength(frame: MusicFrame, response: float) -> float:
    raw = frame.onset * 0.66 + frame.bass * 0.22 + frame.change * 0.12
    floor = 0.24 + response * 0.10
    return _clamp(max(floor, raw * (0.56 + response * 0.44)))


def _tempo_response(frame: MusicFrame) -> float:
    bpm = frame.beat_bpm
    if frame.beat_confidence < 0.18 or bpm <= 0.0:
        return 0.78
    return 0.56 + _clamp((bpm - 104.0) / 52.0) * 0.44


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
