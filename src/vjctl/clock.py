from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TempoClock:
    bpm: float = 145.0
    target_bpm: float = 145.0
    phase: float = 0.0
    beat_index: int = 0
    locked: bool = False
    lock_rate: float = 2.8
    _tap_group: list[float] = field(default_factory=list)
    _last_tap: float | None = None

    @property
    def beat_time(self) -> float:
        return self.beat_index + self.phase

    def update(self, dt: float) -> bool:
        dt = max(0.0, dt)
        if self.bpm != self.target_bpm:
            blend = min(1.0, dt * self.lock_rate)
            self.bpm += (self.target_bpm - self.bpm) * blend
            if abs(self.bpm - self.target_bpm) < 0.01:
                self.bpm = self.target_bpm

        previous = self.phase
        self.phase = (self.phase + dt * (self.bpm / 60.0)) % 1.0
        if self.phase < previous:
            self.beat_index += 1
            return self.locked
        return False

    def tap(self, now: float) -> float | None:
        if self._last_tap is not None and now - self._last_tap > 2.0:
            self._tap_group.clear()
        self._last_tap = now
        self._tap_group.append(now)
        if len(self._tap_group) < 4:
            return None

        taps = self._tap_group[-4:]
        intervals = [b - a for a, b in zip(taps, taps[1:]) if b > a]
        self._tap_group.clear()
        if len(intervals) != 3 or not _steady(intervals):
            return None
        avg = sum(intervals) / len(intervals)
        if avg <= 0:
            return None
        candidate = _clamp_bpm(60.0 / avg)
        self.target_bpm = candidate
        self.locked = True
        if self.phase > 0.0:
            self.beat_index += 1
        self.phase = 0.0
        return candidate

    def slider(self, amount: float) -> None:
        self.target_bpm = _clamp_bpm(self.target_bpm + amount)

    def suggest_bpm(self, bpm: float, confidence: float) -> None:
        if self.locked or bpm <= 0.0 or confidence < 0.68:
            return
        target = _clamp_bpm(bpm)
        amount = min(0.18, max(0.04, confidence * 0.14))
        self.target_bpm += (target - self.target_bpm) * amount

    def jog(self, amount: float) -> None:
        self.phase += amount
        while self.phase >= 1.0:
            self.phase -= 1.0
            self.beat_index += 1
        while self.phase < 0.0:
            self.phase += 1.0
            self.beat_index -= 1

    def free_roam(self) -> None:
        self.locked = False
        self.phase = 0.0
        self.beat_index = 0
        self._tap_group.clear()
        self._last_tap = None


def _clamp_bpm(value: float) -> float:
    return max(40.0, min(220.0, float(value)))


def _steady(intervals: list[float]) -> bool:
    avg = sum(intervals) / len(intervals)
    if avg <= 0:
        return False
    return max(abs(interval - avg) for interval in intervals) <= avg * 0.22
