from __future__ import annotations

import random
from dataclasses import dataclass, field

from .clock import TempoClock
from .effects import EFFECTS, EFFECT_BY_KEY
from .events import SocialIncoming
from .music import MusicFrame

DEFAULT_AGGRESSION = 0.10
DEFAULT_DENSITY = 0.10


@dataclass(frozen=True)
class MusicTuning:
    confidence_threshold: float = 0.08
    onset_threshold: float = 0.58
    onset_debounce: float = 0.12


@dataclass
class Overlay:
    text: str
    created_at: float
    expires_at: float
    kind: str = "text"


@dataclass
class SocialEvent:
    nick: str
    kind: str
    x: float
    y: float
    expires_at: float


@dataclass
class Wave:
    born_at: float
    strength: float
    aggression: float
    density: float
    lifetime: float


@dataclass
class HoldEffect:
    name: str
    held_until_beat: float = 0.0
    charge: float = 0.0
    release: float = 0.0

    @property
    def active(self) -> bool:
        return self.charge > 0.01 or self.release > 0.01

    def trigger(self, beat_time: float, hold_beats: float, release: float) -> None:
        self.held_until_beat = max(self.held_until_beat, beat_time + hold_beats)
        self.charge = max(self.charge, 0.18)
        self.release = max(self.release, release)

    def update(self, beat_dt: float, beat_time: float) -> None:
        if self.held_until_beat > 0.0 and beat_time <= self.held_until_beat:
            self.charge = min(1.0, self.charge + beat_dt * 1.9)
            self.release = max(0.0, self.release - beat_dt * 1.3)
            return
        if self.held_until_beat > 0.0:
            self.release = max(self.release, self.charge)
            self.held_until_beat = 0.0
        self.charge = max(0.0, self.charge - beat_dt * 3.2)
        self.release = max(0.0, self.release - beat_dt * 1.0)


@dataclass
class VJModel:
    clock: TempoClock = field(default_factory=TempoClock)
    aggression: float = DEFAULT_AGGRESSION
    density: float = DEFAULT_DENSITY
    prompt: str = ""
    overlays: list[Overlay] = field(default_factory=list)
    socials: list[SocialEvent] = field(default_factory=list)
    waves: list[Wave] = field(default_factory=list)
    music: MusicFrame = field(default_factory=MusicFrame)
    music_tuning: MusicTuning = field(default_factory=MusicTuning)
    effects: dict[str, HoldEffect] = field(
        default_factory=lambda: {effect.name: HoldEffect(effect.name) for effect in EFFECTS}
    )
    cooldown: float = 0.0
    status: str = "vjctl realm"
    rng: random.Random = field(default_factory=lambda: random.Random(901507))
    last_music_onset_at: float = -999.0

    def update(self, dt: float, now: float) -> bool:
        beat = self.clock.update(dt)
        beat_time = self.beat_time
        beat_dt = max(0.0, dt * (self.clock.bpm / 60.0))
        if beat:
            self._spawn_wave(now, self.effective_aggression)

        for effect in self.effects.values():
            effect.update(beat_dt, beat_time)

        if self.cooldown > 0.0:
            self.cooldown = min(1.0, self.cooldown + dt / 9.0)
            if self.cooldown >= 1.0:
                self.clear_effects()
        self._expire(now)
        return beat

    @property
    def effective_aggression(self) -> float:
        return max(0.0, min(1.0, self.aggression * (1.0 - self.cooldown)))

    @property
    def effective_density(self) -> float:
        return max(0.0, min(1.0, self.density * (1.0 - self.cooldown)))

    @property
    def beat_time(self) -> float:
        return self.clock.beat_time

    def text_input(self, char: str) -> None:
        if char == "\b":
            self.prompt = self.prompt[:-1]
            return
        if len(self.prompt) >= 96:
            return
        self.prompt += char

    def submit_prompt(self, now: float) -> None:
        text = self.prompt.strip()
        self.prompt = ""
        if not text:
            return
        if text.startswith("/"):
            self.run_command(text, now)
            return
        duration = max(3.0, min(11.0, 2.2 + len(text) * 0.11))
        self.overlays.append(Overlay(text.upper(), now, now + duration))
        self.status = f"TEXT {duration:.1f}s"

    def run_command(self, command: str, now: float) -> None:
        parts = command.strip().split()
        name = parts[0].lower() if parts else ""
        args = parts[1:]
        handler = {
            "/aggr": self._command_aggr,
            "/dens": self._command_density,
            "/density": self._command_density,
            "/cooldown": self._command_cooldown,
        }.get(name)
        if handler is not None:
            handler(args)
            return
        self.status = f"UNKNOWN {name}"
        self.overlays.append(Overlay(f"UNKNOWN {name}", now, now + 3.0, "system"))

    def apply_event(self, event: SocialIncoming, now: float) -> None:
        self.socials.append(
            SocialEvent(
                nick=event.nick,
                kind=event.kind,
                x=self.rng.uniform(0.08, 0.84),
                y=self.rng.uniform(0.14, 0.82),
                expires_at=now + self.rng.uniform(2.4, 4.8),
            )
        )

    def apply_music(self, frame: MusicFrame, now: float) -> None:
        self.music = frame
        self.clock.suggest_bpm(frame.beat_bpm, frame.beat_confidence)
        if frame.confidence < self.music_tuning.confidence_threshold:
            self.aggression = _follow(self.aggression, DEFAULT_AGGRESSION, 0.05)
            self.density = _follow(self.density, DEFAULT_DENSITY, 0.05)
            return
        self.aggression = _clamp(max(DEFAULT_AGGRESSION, DEFAULT_AGGRESSION + frame.drive * 0.84))
        self.density = _clamp(max(DEFAULT_DENSITY, DEFAULT_DENSITY + frame.mass * 0.62))
        if frame.onset < self.music_tuning.onset_threshold:
            return
        if now - self.last_music_onset_at < self.music_tuning.onset_debounce:
            return
        strength = _clamp(max(0.34, frame.onset * 0.82 + frame.bass * 0.28 + frame.change * 0.18))
        self._spawn_wave(now, strength)
        self.last_music_onset_at = now
        self.status = "MUSIC ONSET"

    def hold(self, key_id: str, now: float = 0.0) -> None:
        spec = EFFECT_BY_KEY.get(key_id)
        if spec is None:
            return
        if spec.name == "pause":
            self.free_roam()
            return
        if spec.cooldown > 0.0:
            self.cooldown = max(self.cooldown, spec.cooldown)
            self.status = spec.label
            return
        beat_time = self.beat_time
        effect = self.effects.get(spec.name)
        if effect is None:
            return
        effect.trigger(beat_time, spec.hold_beats, spec.release)
        for pulse in spec.pulses:
            self._spawn_wave(now, max(0.4, spec.release, spec.level / 10.0), pulse)
        self.status = spec.label

    def tap(self, now: float) -> None:
        candidate = self.clock.tap(now)
        self._spawn_wave(now, max(0.32, self.effective_aggression))
        if candidate is None:
            self.status = "FREE TAP"
        else:
            self.status = f"LOCK {candidate:05.1f}"

    def slider(self, amount: float) -> None:
        self.clock.slider(amount)
        self.status = f"BPM {self.clock.target_bpm:05.1f}"

    def jog(self, amount: float) -> None:
        self.clock.jog(amount)
        self.status = "JOG +" if amount > 0 else "JOG -"

    def clear_effects(self) -> None:
        for effect in self.effects.values():
            effect.charge = 0.0
            effect.release = 0.0
            effect.held_until_beat = 0.0

    def free_roam(self) -> None:
        self.clear_effects()
        self.cooldown = 0.0
        self.clock.free_roam()
        self.status = "FREE ROAM"

    def _command_aggr(self, args: list[str]) -> None:
        if not args:
            self.status = f"AGGR {self.aggression:.2f}"
            return
        value = args[0].lower()
        if value == "up":
            self.aggression = min(1.0, self.aggression + 0.08)
        elif value == "down":
            self.aggression = max(0.0, self.aggression - 0.08)
        else:
            try:
                self.aggression = max(0.0, min(1.0, float(value)))
            except ValueError:
                self.status = "AGGR ?"
                return
        self.cooldown = 0.0
        self.status = f"AGGR {self.aggression:.2f}"

    def _command_density(self, args: list[str]) -> None:
        if not args:
            self.status = f"DENS {self.density:.2f}"
            return
        value = args[0].lower()
        if value == "up":
            self.density = min(1.0, self.density + 0.08)
        elif value == "down":
            self.density = max(0.0, self.density - 0.08)
        else:
            try:
                self.density = max(0.0, min(1.0, float(value)))
            except ValueError:
                self.status = "DENS ?"
                return
        self.cooldown = 0.0
        self.status = f"DENS {self.density:.2f}"

    def _command_cooldown(self, args: list[str]) -> None:
        self.cooldown = max(self.cooldown, 0.01)
        self.status = "COOLDOWN"

    def _expire(self, now: float) -> None:
        self.overlays = [item for item in self.overlays if item.expires_at > now]
        self.socials = [item for item in self.socials if item.expires_at > now]
        self.waves = [item for item in self.waves if now - item.born_at < item.lifetime]

    def _spawn_wave(self, now: float, strength: float, offset_beats: float = 0.0) -> None:
        aggression = self.effective_aggression
        density = self.effective_density
        beat_seconds = 60.0 / max(1.0, self.clock.bpm)
        lifetime_beats = max(0.82, 3.0 - aggression * 1.55)
        born_at = now + offset_beats * beat_seconds
        lifetime = lifetime_beats * beat_seconds
        self.waves.append(Wave(born_at, strength, aggression, density, lifetime))


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
