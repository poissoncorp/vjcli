from __future__ import annotations

import math

from .buffer import FrameBuffer
from .model import VJModel
from .noise import grain


class SignalRenderer:
    def render(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        if model.visual_mode != "string":
            return
        if buffer.width < 40 or buffer.height < 12:
            return
        theme = model.visual_theme
        frame = model.music
        tension = min(1.0, frame.drive * 0.34 + model.auto_pressure * 0.42)
        tension += model.beat_accent * 0.24 + model.auto_hit * 0.34
        tension = min(1.0, tension)
        center = buffer.height // 2
        span = max(2, round(buffer.height * (0.06 + tension * 0.10)))
        lanes = 1 + round(tension * 3)
        salt = round(beat_time * (4 + tension * 8) * theme.speed_gain)
        for lane in range(lanes):
            offset = (lane - lanes // 2) * max(2, span)
            y0 = center + offset
            self._line(buffer, model, y0, tension, lane, salt)
        if model.auto_hit > 0.12:
            self._splinters(buffer, model, center, tension, salt)

    def _line(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        y0: int,
        tension: float,
        lane: int,
        salt: int,
    ) -> None:
        theme = model.visual_theme
        frame = model.music
        width = max(1, buffer.width - 1)
        wave = 2.0 + frame.brightness * 5.0 + model.lsd_theme.motion * 3.0
        amp = max(1, round(buffer.height * (0.03 + tension * 0.12)))
        phase = model.beat_time * (1.8 + frame.density * 4.2) + lane * 0.7
        previous_y = y0
        for x in range(buffer.width):
            t = x / width
            wobble = math.sin(t * math.tau * wave + phase)
            wobble += math.sin(t * math.tau * (wave * 0.42 + 1.0) - phase * 0.7) * 0.48
            wobble += (grain(x, lane, salt) % 100 / 100.0 - 0.5) * tension * 1.4
            y = y0 + round(wobble * amp)
            if not (1 <= y < buffer.height - 1):
                previous_y = y
                continue
            char = self._char(y - previous_y, tension)
            color = theme.primary if grain(x, y, salt) % 100 < 82 else theme.accent
            buffer.write_cell(x, y, char, fg=color, bold=tension > 0.72, dim=tension < 0.34)
            if tension > 0.48 and grain(x, y, salt + 13) % 100 < 16 + tension * 18:
                buffer.write_cell(x, y + 1, ".", fg=theme.deep, dim=True)
            previous_y = y

    def _splinters(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        center: int,
        tension: float,
        salt: int,
    ) -> None:
        theme = model.visual_theme
        amount = min(1.0, model.auto_hit + tension * 0.35)
        count = 4 + round(amount * 9)
        for index in range(count):
            x = grain(index, salt, 401) % buffer.width
            height = 2 + grain(index, salt, 409) % max(2, round(buffer.height * amount * 0.28))
            direction = -1 if grain(index, salt, 419) % 2 else 1
            for step in range(height):
                y = center + direction * step
                if not (1 <= y < buffer.height - 1):
                    continue
                char = "|" if amount > 0.58 else ":"
                color = theme.accent if index % 3 == 0 else theme.primary
                buffer.write_cell(x + step % 2, y, char, fg=color, bold=amount > 0.74)

    def _char(self, delta: int, tension: float) -> str:
        if abs(delta) > 1:
            return "/" if delta < 0 else "\\"
        if tension > 0.58:
            return "="
        return "-"
