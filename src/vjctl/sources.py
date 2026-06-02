from __future__ import annotations

import math
import random

from .events import SocialIncoming
from .music import MusicFrame


class SimulatedMusicSource:
    def __init__(self, bpm: float = 145.0) -> None:
        self.bpm = bpm
        self.pulse_index = -1

    def poll(self, now: float) -> MusicFrame:
        beat = now * self.bpm / 60.0
        phase = beat % 1.0
        pulse = int(beat * 4.0)
        phrase = 0.5 + math.sin(beat * math.tau / 16.0) * 0.5
        bass = max(0.0, 1.0 - phase * 6.8)
        hats = max(0.0, 1.0 - ((beat * 2.0 + 0.5) % 1.0) * 9.0)
        onset = 0.0
        change = 0.0
        if pulse != self.pulse_index:
            self.pulse_index = pulse
            step = pulse % 16
            if step in (0, 4, 8, 12):
                onset = 0.86
                change = 0.72 if step == 0 else 0.24
            elif step in (2, 6, 10, 14):
                onset = 0.42
                change = 0.16
        return MusicFrame(
            energy=0.14 + bass * 0.68 + hats * 0.18 + phrase * 0.12,
            bass=bass,
            brightness=0.10 + hats * 0.65,
            density=0.12 + phrase * 0.24 + bass * 0.12,
            onset=onset,
            change=change,
            confidence=0.86,
        )


class SimulatedSocialSource:
    def __init__(self, seed: int = 901507) -> None:
        self.rng = random.Random(seed)
        self.next_at = 0.0

    def poll(self, now: float, cooldown: float) -> list[SocialIncoming]:
        if self.next_at <= 0.0:
            self.next_at = now + self.rng.uniform(5.0, 9.0)
            return []
        if cooldown > 0.7 or now < self.next_at:
            return []

        names = ("null.void", "acid_marta", "909_fever", "redacted", "szum", "warehouse_lena")
        kind = "follow" if self.rng.random() < 0.28 else "like"
        self.next_at = now + self.rng.uniform(7.0, 15.0)
        return [SocialIncoming(self.rng.choice(names), kind)]
