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

PROFILE_EFFECT_DECKS = {
    "velvet": {
        "listen": ("4",),
        "drive": ("6", "4"),
        "fault": ("6", "7"),
        "weight": ("5", "6"),
        "rupture": ("9", "8"),
        "chaos": ("8", "9"),
    },
    "house": {
        "listen": ("4",),
        "drive": ("3", "4"),
        "fault": ("6", "7"),
        "weight": ("5", "3"),
        "rupture": ("4", "8", "9"),
        "chaos": ("8", "4", "9"),
    },
    "acid": {
        "listen": ("7",),
        "drive": ("7", "6"),
        "fault": ("7", "6", "9"),
        "weight": ("7", "5"),
        "rupture": ("9", "7", "1"),
        "chaos": ("1", "8", "7"),
    },
    "spectral": {
        "listen": ("4",),
        "drive": ("6", "4"),
        "fault": ("7", "6"),
        "weight": ("5", "6"),
        "rupture": ("9", "8"),
        "chaos": ("8", "9"),
    },
    "industrial": {
        "listen": ("6",),
        "drive": ("6", "7"),
        "fault": ("7", "8"),
        "weight": ("8", "5"),
        "rupture": ("2", "8", "9"),
        "chaos": ("8", "1", "2"),
    },
    "hard": {
        "listen": ("3",),
        "drive": ("3", "1"),
        "fault": ("7", "1"),
        "weight": ("8", "2"),
        "rupture": ("2", "8", "1"),
        "chaos": ("1", "8", "9"),
    },
}


@dataclass(frozen=True)
class ProfileBias:
    pressure: float = 1.0
    aggression: float = 1.0
    density: float = 1.0
    threshold: float = 0.0
    debounce: float = 1.0
    wave: float = 1.0
    transition: float = 1.0


PROFILE_BIASES = {
    "velvet": ProfileBias(
        pressure=0.72,
        aggression=0.78,
        density=0.86,
        threshold=0.10,
        debounce=1.22,
        wave=0.82,
        transition=0.72,
    ),
    "house": ProfileBias(
        pressure=0.92,
        aggression=0.90,
        density=0.92,
        threshold=0.02,
        debounce=1.08,
        wave=0.96,
        transition=0.86,
    ),
    "acid": ProfileBias(
        pressure=1.02,
        aggression=1.04,
        density=1.04,
        threshold=-0.03,
        debounce=0.92,
        wave=0.98,
        transition=0.98,
    ),
    "spectral": ProfileBias(
        pressure=0.68,
        aggression=0.74,
        density=0.80,
        threshold=0.12,
        debounce=1.28,
        wave=0.76,
        transition=0.68,
    ),
    "industrial": ProfileBias(
        pressure=1.12,
        aggression=1.10,
        density=1.14,
        threshold=-0.05,
        debounce=0.86,
        wave=1.08,
        transition=1.10,
    ),
    "hard": ProfileBias(
        pressure=1.22,
        aggression=1.18,
        density=1.18,
        threshold=-0.07,
        debounce=0.80,
        wave=1.14,
        transition=1.18,
    ),
}
DEFAULT_PROFILE_BIAS = ProfileBias()


@dataclass(frozen=True)
class MusicMood:
    profile: str
    confidence: float
    certainty: float
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
    phase: str = "rest"
    contrast: float = 0.0
    lift: float = 0.0
    status: str | None = None


@dataclass(frozen=True)
class MusicDynamics:
    contrast: float = 0.0
    lift: float = 0.0
    phase: str = "warmup"


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
    baseline_drive: float = 0.0
    baseline_mass: float = 0.0
    baseline_change: float = 0.0
    dynamics_ready: bool = False
    last_contrast: float = 0.0
    last_phase: str = "warmup"

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
            self.dynamics_ready = False
            self.last_contrast = 0.0
            self.last_phase = "warmup"
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
        dynamics = self._update_dynamics(frame, dt)
        self._update_pressure(frame, dt, response, mood, dynamics)
        scene = self._stabilized_scene(
            _scene(frame, self.pressure, response, mood, dynamics),
            frame,
            now,
        )
        scene_age = self._set_scene(scene, now)
        scene_entered = scene_age == 0.0
        score = _trigger_score(frame, self.pressure, response, dynamics)
        transition_strength = (
            _transition_strength(frame, scene, self.pressure, response, mood, dynamics)
            if scene_entered and self.frames_seen > 1
            else None
        )
        dynamic_weight = 0.72 + dynamics.contrast * 0.42
        aggression_lift = (
            frame.drive * dynamic_weight * (0.34 + response * 0.28)
            + self.pressure * (0.14 + response * 0.14)
        )
        density_lift = (
            frame.mass * dynamic_weight * (0.30 + response * 0.20)
            + self.pressure * (0.10 + response * 0.10)
        )
        next_aggression = _clamp(
            max(
                DEFAULT_AGGRESSION,
                DEFAULT_AGGRESSION + aggression_lift * _mood_scale(mood, "aggression"),
            )
        )
        next_density = _clamp(
            max(
                DEFAULT_DENSITY,
                DEFAULT_DENSITY + density_lift * _mood_scale(mood, "density"),
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
                phase=dynamics.phase,
                contrast=dynamics.contrast,
                lift=dynamics.lift,
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
                phase=dynamics.phase,
                contrast=dynamics.contrast,
                lift=dynamics.lift,
            )

        strength = _wave_strength(frame, response, mood, dynamics)
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
            phase=dynamics.phase,
            contrast=dynamics.contrast,
            lift=dynamics.lift,
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

    def _update_pressure(
        self,
        frame: MusicFrame,
        dt: float,
        response: float,
        mood: MusicMood | None,
        dynamics: MusicDynamics,
    ) -> None:
        target = _clamp(
            frame.drive * 0.32
            + frame.mass * 0.22
            + frame.change * 0.18
            + frame.onset * 0.10
        )
        target *= 0.56 + response * 0.44
        target *= 0.78 + dynamics.contrast * 0.44
        target *= _mood_scale(mood, "pressure")
        speed = (3.4 + response * 3.6) if target > self.pressure else 1.2
        self.pressure = _follow(self.pressure, target, _attack(dt, speed))

    def _update_dynamics(self, frame: MusicFrame, dt: float) -> MusicDynamics:
        if not self.dynamics_ready:
            self.baseline_drive = frame.drive
            self.baseline_mass = frame.mass
            self.baseline_change = frame.change
            self.dynamics_ready = True
            return MusicDynamics()
        drive_lift = _lift(frame.drive, self.baseline_drive)
        mass_lift = _lift(frame.mass, self.baseline_mass)
        change_lift = _lift(frame.change, self.baseline_change)
        lift = _clamp(drive_lift * 0.52 + mass_lift * 0.22 + change_lift * 0.26)
        contrast = _clamp(
            max(
                lift,
                drive_lift * 0.46 + frame.onset * 0.18,
                change_lift * 0.64 + frame.onset * 0.12,
            )
        )
        self.baseline_drive = _baseline(self.baseline_drive, frame.drive, dt)
        self.baseline_mass = _baseline(self.baseline_mass, frame.mass, dt)
        self.baseline_change = _baseline(self.baseline_change, frame.change, dt)
        phase = _phase(frame, contrast, lift, self.pressure, self.last_contrast, self.last_phase)
        self.last_contrast = contrast
        self.last_phase = phase
        return MusicDynamics(contrast, lift, phase)

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
            debounce *= _mood_scale(mood, "debounce")
        if scene_entered:
            debounce *= 0.62
        if now - self.last_effect_at < debounce:
            return None
        threshold = self.tuning.effect_threshold + (1.0 - response) * 0.18
        if mood is not None:
            threshold += _mood_threshold_shift(mood, scene)
            threshold += _mood_add(mood, "threshold")
        threshold += _phase_threshold_shift(self.last_phase)
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
            if key == self.last_effect_key and _profile_deck(scene, mood):
                return _alternate_key(scene, key, mood)
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
        key = _profile_key(scene, scene_age, pressure, mood)
        if key is not None:
            return key
    if scene == "chaos" and frame.drive > 0.78 and frame.mass > 0.58:
        return "1"
    if scene == "rupture" and pressure > 0.68 and scene_age < 0.90:
        return "2"
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


def _profile_key(
    scene: str,
    scene_age: float,
    pressure: float,
    mood: MusicMood,
) -> str | None:
    if _mood_certainty(mood) < 0.18:
        return None
    deck = _profile_deck(scene, mood)
    if not deck:
        return None
    intensity = _clamp(
        pressure * 0.46
        + mood.impact * 0.18
        + mood.grit * 0.14
        + mood.motion * 0.10
        + min(1.0, scene_age / 1.4) * 0.18
    )
    if scene in ("listen", "drive") and mood.space > 0.64 and mood.impact < 0.42:
        intensity *= 0.52
    index = min(len(deck) - 1, int(intensity * len(deck)))
    return deck[index]


def _alternate_key(scene: str, key: str, mood: MusicMood | None) -> str:
    if mood is not None:
        deck = _profile_deck(scene, mood)
        if deck:
            if key not in deck:
                return deck[0]
            index = deck.index(key)
            return deck[(index + 1) % len(deck)]
    alternatives = {
        "drive": {"3": "4", "4": "6"},
        "fault": {"7": "6", "6": "4"},
        "weight": {"5": "8", "8": "3"},
        "rupture": {"9": "2", "2": "9", "1": "9"},
        "chaos": {"1": "8", "8": "9", "9": "2"},
    }
    return alternatives.get(scene, {}).get(key, key)


def _profile_deck(scene: str, mood: MusicMood | None) -> tuple[str, ...]:
    if mood is None:
        return ()
    return PROFILE_EFFECT_DECKS.get(mood.profile, {}).get(scene, ())


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
    return _clamp(mood.certainty)


def _mood_scale(mood: MusicMood | None, field: str) -> float:
    if mood is None:
        return 1.0
    target = getattr(PROFILE_BIASES.get(mood.profile, DEFAULT_PROFILE_BIAS), field)
    return _blend(1.0, target, _mood_certainty(mood))


def _mood_add(mood: MusicMood, field: str) -> float:
    target = getattr(PROFILE_BIASES.get(mood.profile, DEFAULT_PROFILE_BIAS), field)
    return target * _mood_certainty(mood)


def _transition_strength(
    frame: MusicFrame,
    scene: str,
    pressure: float,
    response: float,
    mood: MusicMood | None,
    dynamics: MusicDynamics,
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
    strength *= 0.72 + dynamics.contrast * 0.42
    strength *= _phase_hit_scale(dynamics.phase)
    strength *= _mood_scale(mood, "transition")
    return _clamp(strength)


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _attack(dt: float, speed: float) -> float:
    return max(0.0, min(1.0, dt * speed))


def _blend(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _baseline(current: float, target: float, dt: float) -> float:
    speed = 0.34 if target > current else 1.10
    return _follow(current, target, _attack(dt, speed))


def _lift(current: float, baseline: float) -> float:
    return _clamp((current - baseline) / max(0.18, 1.0 - baseline))


def _phase(
    frame: MusicFrame,
    contrast: float,
    lift: float,
    pressure: float,
    previous_contrast: float,
    previous_phase: str,
) -> str:
    if contrast > 0.58 and (frame.onset > 0.50 or frame.change > 0.50):
        return "hit"
    if lift > 0.30 or (contrast > 0.26 and contrast >= previous_contrast):
        return "rise"
    if previous_phase in ("hit", "rise") and contrast < previous_contrast * 0.55:
        return "release"
    if pressure > 0.34 or frame.mass > 0.58:
        return "hold"
    return "rest"


def _phase_threshold_shift(phase: str) -> float:
    return {
        "hit": -0.08,
        "rise": 0.03,
        "hold": 0.04,
        "release": 0.11,
        "warmup": 0.18,
    }.get(phase, 0.02)


def _phase_hit_scale(phase: str) -> float:
    return {
        "hit": 1.16,
        "rise": 0.94,
        "hold": 0.86,
        "release": 0.72,
        "warmup": 0.62,
    }.get(phase, 0.82)


def _scene(
    frame: MusicFrame,
    pressure: float,
    response: float,
    mood: MusicMood | None = None,
    dynamics: MusicDynamics = MusicDynamics(),
) -> str:
    restraint = 1.0 - response
    if dynamics.phase == "warmup":
        scene = "drive" if frame.drive > 0.55 or pressure > 0.38 else "listen"
        return _mood_scene(scene, frame, pressure, mood)
    context = 1.0 - dynamics.contrast
    rupture_change = 0.72 + restraint * 0.14 + context * 0.08
    rupture_onset = 0.62 + restraint * 0.10 + context * 0.06
    chaos_pressure = 0.72 + restraint * 0.14 + context * 0.06
    chaos_drive = 0.86 + restraint * 0.08 + context * 0.04
    weight_mass = 0.58 + restraint * 0.08 + context * 0.03
    drive_amount = 0.42 + restraint * 0.10 + context * 0.04
    drive_pressure = 0.38 + restraint * 0.10 + context * 0.03
    if dynamics.phase == "hit":
        rupture_change -= 0.08
        rupture_onset -= 0.06
        chaos_pressure -= 0.04
    elif dynamics.phase == "release":
        rupture_change += 0.08
        rupture_onset += 0.08
        chaos_pressure += 0.08
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


def _trigger_score(
    frame: MusicFrame,
    pressure: float,
    response: float,
    dynamics: MusicDynamics,
) -> float:
    score = _clamp(
        max(
            frame.onset * (0.58 + response * 0.42),
            frame.change * (0.52 + response * 0.42),
            frame.drive * (0.42 + response * 0.16)
            + pressure * (0.18 + response * 0.10)
            + frame.change * (0.10 + response * 0.08),
        )
    )
    score *= 0.62 + dynamics.contrast * 0.54
    score += dynamics.lift * 0.18
    score *= _phase_hit_scale(dynamics.phase)
    return _clamp(score)


def _wave_strength(
    frame: MusicFrame,
    response: float,
    mood: MusicMood | None,
    dynamics: MusicDynamics,
) -> float:
    raw = frame.onset * 0.66 + frame.bass * 0.22 + frame.change * 0.12
    floor = 0.24 + response * 0.10
    strength = max(floor, raw * (0.56 + response * 0.44))
    strength *= 0.70 + dynamics.contrast * 0.50
    strength *= _phase_hit_scale(dynamics.phase)
    return _clamp(strength * _mood_scale(mood, "wave"))


def _tempo_response(frame: MusicFrame) -> float:
    bpm = frame.beat_bpm
    if frame.beat_confidence < 0.18 or bpm <= 0.0:
        return 0.78
    return 0.56 + _clamp((bpm - 104.0) / 52.0) * 0.44


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
