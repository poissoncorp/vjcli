from __future__ import annotations

from dataclasses import dataclass

from .music_reactor import DEFAULT_SENSITIVITY, MusicTuning


DEFAULT_PERFORMANCE_PRESET = "club"
CUSTOM_PERFORMANCE_PRESET = "custom"


@dataclass(frozen=True)
class PerformancePreset:
    name: str
    label: str
    tuning: MusicTuning
    visual_mode: str = "waves"


PERFORMANCE_PRESETS = {
    "minimal": PerformancePreset(
        name="minimal",
        label="MINIMAL",
        tuning=MusicTuning(
            sensitivity=0.10,
            confidence_threshold=0.12,
            onset_threshold=0.76,
            onset_debounce=0.34,
            effect_threshold=0.94,
            effect_debounce=1.18,
        ),
    ),
    "club": PerformancePreset(
        name="club",
        label="CLUB",
        tuning=MusicTuning(sensitivity=DEFAULT_SENSITIVITY),
    ),
    "hard": PerformancePreset(
        name="hard",
        label="HARD",
        tuning=MusicTuning(
            sensitivity=0.58,
            confidence_threshold=0.06,
            onset_threshold=0.54,
            onset_debounce=0.14,
            effect_threshold=0.76,
            effect_debounce=0.62,
        ),
    ),
    "scope": PerformancePreset(
        name="scope",
        label="SCOPE",
        tuning=MusicTuning(
            sensitivity=0.34,
            confidence_threshold=0.08,
            onset_threshold=0.62,
            onset_debounce=0.18,
            effect_threshold=0.84,
            effect_debounce=0.82,
        ),
        visual_mode="string",
    ),
}


def performance_preset(name: str) -> PerformancePreset | None:
    return PERFORMANCE_PRESETS.get(name.lower())
