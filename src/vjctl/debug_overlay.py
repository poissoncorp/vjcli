from __future__ import annotations

from .buffer import FrameBuffer
from .effects import EFFECTS
from .model import VJModel
from .palette import ASH, BLACK, RED, Color


class DebugOverlay:
    def render(self, buffer: FrameBuffer, model: VJModel, now: float) -> None:
        if not model.debug or buffer.width < 54 or buffer.height < 10:
            return
        width = buffer.width - 4
        for y, line in enumerate(_debug_lines(model, now)):
            if y >= buffer.height:
                return
            text = _clip(line, width)
            span = min(buffer.width, max(54, len(text) + 4))
            color, bold, dim = _style(line, y)
            buffer.write_text(0, y, " " * span, fg=ASH, bg=BLACK, dim=True)
            buffer.write_text(2, y, text, fg=color, bold=bold, dim=dim)


def _debug_lines(model: VJModel, now: float) -> list[str]:
    frame = model.music
    timing = model.timing
    mode = "LOCK" if timing.locked else timing.source.upper()
    return [
        f"DBG {model.status}",
        (
            f"AUDIO E{frame.energy:.2f} B{frame.bass:.2f} "
            f"H{frame.brightness:.2f} D{frame.density:.2f}"
        ),
        f"ONSET {frame.onset:.2f} CHANGE {frame.change:.2f} CONF {frame.confidence:.2f}",
        f"BEAT {frame.beat_bpm:05.1f} PH {frame.beat_phase:.2f} BC {frame.beat_confidence:.2f}",
        (
            f"CLOCK {mode} {timing.bpm:05.1f}>{timing.target_bpm:05.1f} "
            f"PH {timing.phase:.2f} TC {timing.confidence:.2f}"
        ),
        (
            f"MODEL A{model.effective_aggression:.2f} "
            f"D{model.effective_density:.2f} "
            f"B{model.beat_accent:.2f} WAVES {len(model.waves)}"
        ),
        (
            f"SCENE {model.auto_scene.upper()} T{model.auto_scene_age:.1f} "
            f"P{model.auto_pressure:.2f} S{model.auto_score:.2f} "
            f"H{model.auto_transition_strength:.2f} K{model.auto_hit:.2f}"
        ),
        f"LSD {_lsd(model)}",
        f"AUTO {_last_auto(model, now)}",
        f"FX {_active_effects(model)}",
    ]


def _style(line: str, index: int) -> tuple[Color, bool, bool]:
    if index == 0:
        return RED, True, False
    if line.startswith("SCENE ") and "LISTEN" not in line and "IDLE" not in line:
        return RED, False, False
    if line.startswith("AUTO ") and not line.endswith(" -"):
        return RED, False, False
    if line.startswith("LSD ") and " C" in line:
        return RED, False, False
    if line.startswith("FX ") and not line.endswith(" -"):
        return RED, True, False
    return ASH, False, True


def _lsd(model: VJModel) -> str:
    if not model.lsd:
        return "OFF"
    theme = model.visual_theme
    if theme.confidence <= 0.0:
        return "WAIT"
    return f"{theme.profile.upper()} C{theme.confidence:.2f}"


def _last_auto(model: VJModel, now: float) -> str:
    if model.last_auto_effect == "-":
        return "-"
    age = max(0.0, now - model.last_auto_effect_at)
    return f"{model.last_auto_effect} {age:.1f}s"


def _active_effects(model: VJModel) -> str:
    parts: list[str] = []
    for spec in EFFECTS:
        effect = model.effects.get(spec.name)
        if effect is None or not effect.active:
            continue
        parts.append(f"{spec.key}:{spec.label} C{effect.charge:.2f} R{effect.release:.2f}")
    return " ".join(parts) if parts else "-"


def _clip(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[:max(1, width)]
