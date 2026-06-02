from __future__ import annotations

import math
from collections.abc import Sequence

from .music import MusicFrame


class AudioAnalyzer:
    def __init__(self) -> None:
        self.level = 0.08
        self.energy = 0.0
        self.bass = 0.0
        self.brightness = 0.0

    def read(self, samples: Sequence[float], sample_rate: int) -> MusicFrame:
        if not samples or sample_rate <= 0:
            return MusicFrame()
        samples = self._normalize(samples)
        energy = _clamp(_rms(samples) * 1.9)
        bass = _clamp(_band(samples, sample_rate, (46.0, 58.0, 73.0, 92.0, 116.0)) * 1.35)
        middle = _clamp(_band(samples, sample_rate, (180.0, 260.0, 390.0, 620.0)) * 1.45)
        high = _clamp(_band(samples, sample_rate, (1200.0, 2400.0, 4200.0)) * 2.2)
        brightness = _clamp(high / max(0.01, bass + middle + high))
        density = _clamp(middle * 0.64 + high * 0.22 + energy * 0.18)
        energy_rise = max(0.0, energy - self.energy)
        bass_rise = max(0.0, bass - self.bass)
        color_shift = abs(brightness - self.brightness)
        onset = _clamp(max(energy_rise * 4.2, bass_rise * 3.4))
        change = _clamp(energy_rise * 2.2 + bass_rise * 1.4 + color_shift * 0.72)
        confidence = _clamp(energy * 1.7 + max(bass, middle, high) * 0.6)
        self.energy = _follow(self.energy, energy, 0.34)
        self.bass = _follow(self.bass, bass, 0.38)
        self.brightness = _follow(self.brightness, brightness, 0.28)
        return MusicFrame(
            energy=energy,
            bass=bass,
            brightness=brightness,
            density=density,
            onset=onset,
            change=change,
            confidence=confidence,
        )

    def _normalize(self, samples: Sequence[float]) -> list[float]:
        peak = max(abs(sample) for sample in samples)
        target = max(0.08, peak)
        amount = 0.72 if target > self.level else 0.28
        self.level = _follow(self.level, target, amount)
        gain = min(9.5, 0.76 / max(0.08, self.level))
        return [_clip_sample(sample * gain) for sample in samples]


def _rms(samples: Sequence[float]) -> float:
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def _band(samples: Sequence[float], sample_rate: int, frequencies: tuple[float, ...]) -> float:
    total = sum(_tone(samples, sample_rate, frequency) for frequency in frequencies)
    return total / len(frequencies)


def _tone(samples: Sequence[float], sample_rate: int, frequency: float) -> float:
    if frequency <= 0.0 or frequency >= sample_rate * 0.5:
        return 0.0
    coeff = 2.0 * math.cos(math.tau * frequency / sample_rate)
    prev = 0.0
    prev2 = 0.0
    for sample in samples:
        current = sample + coeff * prev - prev2
        prev2 = prev
        prev = current
    power = prev2 * prev2 + prev * prev - coeff * prev * prev2
    return _clamp(math.sqrt(max(0.0, power)) * 2.0 / len(samples))


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _clip_sample(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
