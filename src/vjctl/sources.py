from __future__ import annotations

import math
import random

from .analyzer import AudioAnalyzer
from .events import SocialIncoming
from .music import MusicFrame


class SimulatedMusicSource:
    def __init__(self, bpm: float = 145.0, sample_rate: int = 16_000) -> None:
        self.bpm = bpm
        self.sample_rate = sample_rate
        self.sample_index = 0
        self.last_at: float | None = None
        self.analyzer = AudioAnalyzer()

    def poll(self, now: float) -> MusicFrame:
        duration = 1.0 / 60.0 if self.last_at is None else max(0.0, now - self.last_at)
        self.last_at = now
        count = max(1, round(min(0.1, duration) * self.sample_rate))
        start = self.sample_index
        self.sample_index += count
        samples = [self._sample((start + index) / self.sample_rate) for index in range(count)]
        return self.analyzer.read(samples, self.sample_rate)

    def _sample(self, t: float) -> float:
        beat = t * self.bpm / 60.0
        phase = beat % 1.0
        phrase = 0.5 + math.sin(beat * math.tau / 16.0) * 0.5
        step = int(beat * 4.0) % 16
        kick = max(0.0, 1.0 - phase * 9.0)
        offbeat = (beat + 0.5) % 1.0
        hat = max(0.0, 1.0 - offbeat * 15.0)
        bass_env = 0.16 + phrase * 0.18 + (0.22 if step in (0, 3, 7, 11) else 0.0)
        kick_wave = math.sin(math.tau * 54.0 * t) * kick * 0.78
        sub_wave = math.sin(math.tau * 108.0 * t) * bass_env
        mid_wave = math.sin(math.tau * (260.0 + step * 7.0) * t) * phrase * 0.12
        hat_wave = _noise(t) * hat * 0.32
        return max(-1.0, min(1.0, kick_wave + sub_wave + mid_wave + hat_wave))


def _noise(t: float) -> float:
    a = math.sin(math.tau * 1831.0 * t)
    b = math.sin(math.tau * 4217.0 * t + 1.7)
    c = math.sin(math.tau * 7099.0 * t + 0.3)
    return (a * b + c * 0.5) / 1.5


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
