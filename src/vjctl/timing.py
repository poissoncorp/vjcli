from __future__ import annotations

from dataclasses import dataclass

TIMING_FREE = "free"
TIMING_AUDIO = "audio"
TIMING_MANUAL = "manual"


@dataclass(frozen=True)
class TimingState:
    source: str = TIMING_FREE
    bpm: float = 145.0
    target_bpm: float = 145.0
    phase: float = 0.0
    beat_time: float = 0.0
    confidence: float = 0.0
    locked: bool = False
