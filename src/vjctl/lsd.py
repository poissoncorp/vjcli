from __future__ import annotations

from dataclasses import dataclass, field

from .music import MusicFrame
from .palette import ASH, DEEP_RED, RED, Color
from .timing import TimingState


@dataclass(frozen=True)
class LsdTheme:
    profile: str
    confidence: float
    primary: Color
    accent: Color
    ghost: Color
    deep: Color
    ash: Color
    line_gain: float = 1.0
    speed_gain: float = 1.0
    kick_gain: float = 1.0
    haze: float = 0.0
    margin: float = 0.0


DEFAULT_THEME = LsdTheme(
    profile="red",
    confidence=0.0,
    margin=0.0,
    primary=RED,
    accent=ASH,
    ghost=ASH,
    deep=DEEP_RED,
    ash=ASH,
)


PROFILES = {
    "velvet": LsdTheme(
        profile="velvet",
        confidence=0.0,
        margin=0.0,
        primary=(255, 120, 180),
        accent=(255, 196, 110),
        ghost=(190, 150, 230),
        deep=(70, 12, 62),
        ash=(235, 220, 226),
        line_gain=0.62,
        speed_gain=0.62,
        kick_gain=0.82,
        haze=0.45,
    ),
    "house": LsdTheme(
        profile="house",
        confidence=0.0,
        margin=0.0,
        primary=(255, 96, 155),
        accent=(255, 178, 86),
        ghost=(120, 224, 205),
        deep=(84, 16, 54),
        ash=(232, 226, 214),
        line_gain=0.82,
        speed_gain=0.78,
        kick_gain=1.08,
        haze=0.28,
    ),
    "acid": LsdTheme(
        profile="acid",
        confidence=0.0,
        margin=0.0,
        primary=(196, 255, 52),
        accent=(255, 238, 62),
        ghost=(68, 255, 188),
        deep=(42, 74, 8),
        ash=(225, 240, 210),
        line_gain=1.06,
        speed_gain=1.18,
        kick_gain=1.02,
        haze=0.16,
    ),
    "spectral": LsdTheme(
        profile="spectral",
        confidence=0.0,
        margin=0.0,
        primary=(124, 236, 255),
        accent=(220, 236, 255),
        ghost=(186, 138, 255),
        deep=(8, 38, 62),
        ash=(224, 236, 245),
        line_gain=0.68,
        speed_gain=0.70,
        kick_gain=0.74,
        haze=0.56,
    ),
    "industrial": LsdTheme(
        profile="industrial",
        confidence=0.0,
        margin=0.0,
        primary=(255, 48, 62),
        accent=(180, 198, 210),
        ghost=(255, 120, 86),
        deep=(104, 10, 18),
        ash=(212, 220, 228),
        line_gain=1.16,
        speed_gain=1.04,
        kick_gain=1.24,
        haze=0.10,
    ),
    "hard": LsdTheme(
        profile="hard",
        confidence=0.0,
        margin=0.0,
        primary=(255, 32, 96),
        accent=(255, 236, 236),
        ghost=(255, 150, 46),
        deep=(126, 6, 34),
        ash=(242, 230, 232),
        line_gain=1.34,
        speed_gain=1.24,
        kick_gain=1.45,
        haze=0.04,
    ),
}

SWITCH_MARGIN = 0.065


@dataclass
class LsdDirector:
    scores: dict[str, float] = field(default_factory=lambda: {name: 0.0 for name in PROFILES})
    theme: LsdTheme = DEFAULT_THEME

    def update(self, frame: MusicFrame, timing: TimingState) -> LsdTheme:
        if frame.confidence < 0.08:
            for name in self.scores:
                self.scores[name] = _follow(self.scores[name], 0.0, 0.06)
            self.theme = _with_confidence(DEFAULT_THEME, 0.0)
            return self.theme
        targets = _scores(frame, timing)
        for name, target in targets.items():
            self.scores[name] = _follow(self.scores.get(name, 0.0), target, 0.10)
        name = _select_profile(self.scores, self.theme)
        margin = _margin(self.scores, name)
        confidence = _confidence(self.scores[name], margin, frame.confidence)
        self.theme = _with_confidence(PROFILES[name], confidence, margin)
        return self.theme


def _scores(frame: MusicFrame, timing: TimingState) -> dict[str, float]:
    tempo = _tempo_amount(frame.beat_bpm or timing.target_bpm)
    calm = 1.0 - frame.drive
    grit = _clamp(frame.density * 0.50 + frame.change * 0.36 + frame.brightness * 0.24)
    kick = _clamp(frame.bass * 0.72 + frame.onset * 0.34)
    airy = _clamp(frame.brightness * 0.70 + calm * 0.32)
    steady = max(timing.confidence, frame.beat_confidence)
    return {
        "velvet": _clamp(calm * 0.62 + airy * 0.32 + (1.0 - tempo) * 0.22),
        "house": _clamp(steady * 0.38 + kick * 0.38 + calm * 0.16 + tempo * 0.18),
        "acid": _clamp(frame.brightness * 0.54 + frame.change * 0.24 + tempo * 0.18),
        "spectral": _clamp(airy * 0.62 + (1.0 - frame.bass) * 0.24 + calm * 0.18),
        "industrial": _clamp(grit * 0.52 + frame.mass * 0.28 + (1.0 - airy) * 0.20),
        "hard": _clamp(frame.drive * 0.46 + kick * 0.34 + tempo * 0.28 + grit * 0.16),
    }


def _tempo_amount(bpm: float) -> float:
    return _clamp((float(bpm) - 96.0) / 72.0)


def _select_profile(scores: dict[str, float], theme: LsdTheme) -> str:
    leader = max(scores, key=lambda item: scores[item])
    current = theme.profile
    if current not in scores or current == leader:
        return leader
    if theme.confidence <= 0.12:
        return leader
    if scores[leader] - scores[current] >= SWITCH_MARGIN:
        return leader
    return current


def _margin(scores: dict[str, float], name: str) -> float:
    others = [score for item, score in scores.items() if item != name]
    if not others:
        return scores[name]
    return scores[name] - max(others)


def _confidence(score: float, margin: float, frame_confidence: float) -> float:
    certainty = 0.56 + max(0.0, margin) * 1.8
    return _clamp(score * frame_confidence * certainty)


def _with_confidence(theme: LsdTheme, confidence: float, margin: float = 0.0) -> LsdTheme:
    return LsdTheme(
        profile=theme.profile,
        confidence=_clamp(confidence),
        margin=margin,
        primary=theme.primary,
        accent=theme.accent,
        ghost=theme.ghost,
        deep=theme.deep,
        ash=theme.ash,
        line_gain=theme.line_gain,
        speed_gain=theme.speed_gain,
        kick_gain=theme.kick_gain,
        haze=theme.haze,
    )


def _follow(current: float, target: float, amount: float) -> float:
    return current + (target - current) * amount


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
