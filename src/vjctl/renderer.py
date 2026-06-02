from __future__ import annotations

from .ansi import RESET, row_to_ansi
from .buffer import FrameBuffer
from .effect_renderers import EffectRenderers
from .model import VJModel
from .text_layer import TextLayer
from .wave_renderer import WaveRenderer


class Renderer:
    def __init__(self) -> None:
        self._previous_rows: list[str] = []
        self._text = TextLayer()
        self._effects = EffectRenderers(self._text)
        self._waves = WaveRenderer()

    def reset_diff(self) -> None:
        self._previous_rows = []

    def render(self, model: VJModel, width: int, height: int, now: float) -> FrameBuffer:
        buffer = FrameBuffer(width, height)
        beat_time = model.beat_time
        self._effects.background(buffer, model, beat_time)
        self._waves.render(buffer, model.waves, now)
        self._effects.effects(buffer, model, beat_time)
        self._text.hud(buffer, model, beat_time)
        self._text.social(buffer, model, beat_time)
        self._text.overlays(buffer, model, beat_time)
        self._text.prompt(buffer, model, beat_time)
        return buffer

    def flush(self, buffer: FrameBuffer) -> str:
        rows = [row_to_ansi(buffer.row(y)) for y in range(buffer.height)]
        if len(self._previous_rows) != len(rows):
            self._previous_rows = [""] * len(rows)
        output: list[str] = []
        for y, row in enumerate(rows):
            if self._previous_rows[y] == row:
                continue
            output.append(f"\x1b[{y + 1};1H{row}{RESET}")
            self._previous_rows[y] = row
        return "".join(output)
