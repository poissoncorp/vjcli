from __future__ import annotations

from .buffer import FrameBuffer
from .model import VJModel
from .noise import grain


class LsdMotifRenderer:
    def __init__(self) -> None:
        self._renderers = {
            "mist": self._mist,
            "pulse": self._pulse,
            "spark": self._spark,
            "ghost": self._ghost,
            "forge": self._forge,
            "strike": self._strike,
        }

    def render(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        if not model.lsd or model.cooldown > 0.92:
            return
        theme = model.visual_theme
        if theme.confidence < 0.10:
            return
        render = self._renderers.get(theme.motif)
        if render is None:
            return
        amount = _amount(model)
        if amount < 0.06:
            return
        render(buffer, model, beat_time, amount)

    def _mist(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        amount: float,
    ) -> None:
        theme = model.visual_theme
        character = theme.character
        salt = round(beat_time * (1.0 + character.pace * 3.0) * theme.speed_gain)
        step_x = max(9, round(18 - amount * 5))
        step_y = max(3, round(7 - amount * 2))
        threshold = 5 + amount * 14 + theme.haze * 10 + character.space * 10
        for y in range(3, buffer.height - 3, step_y):
            drift = (salt + y * 3) % step_x
            for x in range(-drift, buffer.width, step_x):
                value = grain(x, y, salt)
                if value % 100 > threshold:
                    continue
                yy = y + value // 17 % 3 - 1
                char = ":" if value % 5 == 0 else "."
                buffer.write_cell(x, yy, char, fg=theme.ghost, dim=True)

    def _pulse(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        amount: float,
    ) -> None:
        theme = model.visual_theme
        character = theme.character
        beat = max(model.beat_accent, character.impact * 0.72)
        pulse = min(1.0, amount + beat * 0.46 + character.weight * 0.18)
        salt = round(beat_time * (4 + pulse * 4) * theme.speed_gain)
        center = buffer.width // 2
        span = round(buffer.width * (0.10 + pulse * 0.26))
        rows = (
            buffer.height // 3,
            buffer.height // 2,
            buffer.height - buffer.height // 3,
        )
        for row in rows:
            drift = grain(row, salt, 13) % 7 - 3
            for x in range(center - span, center + span + 1, 2):
                value = grain(x, row, salt)
                if value % 100 > 42 + pulse * 36:
                    continue
                char = "=" if beat > 0.28 and value % 4 == 0 else "-"
                color = theme.accent if beat > 0.48 and value % 9 == 0 else theme.primary
                buffer.write_cell(x + drift, row, char, fg=color, bold=beat > 0.68)

    def _spark(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        amount: float,
    ) -> None:
        theme = model.visual_theme
        character = theme.character
        spark = min(1.0, amount + character.spark * 0.46 + character.grit * 0.18)
        salt = round(beat_time * (7 + spark * 8) * theme.speed_gain)
        step = max(3, round(10 - spark * 5))
        threshold = 4 + spark * 24
        for y in range(3, buffer.height - 3, 3):
            drift = grain(y, salt, 29) % step
            for x in range(drift, buffer.width, step):
                value = grain(x, y, salt)
                if value % 100 > threshold:
                    continue
                char = "/" if value % 2 == 0 else "\\"
                color = theme.accent if value % 5 == 0 else theme.ghost
                buffer.write_cell(x, y, char, fg=color, bold=spark > 0.72)
                if spark > 0.62 and x + 1 < buffer.width:
                    buffer.write_cell(x + 1, y, "-", fg=theme.primary, dim=value % 3 != 0)

    def _ghost(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        amount: float,
    ) -> None:
        theme = model.visual_theme
        character = theme.character
        ghost = min(1.0, amount + character.space * 0.32 + character.spark * 0.14)
        salt = round(beat_time * (1.4 + ghost * 3.0) * theme.speed_gain)
        columns = 4 + round(ghost * 8)
        span = max(5, buffer.width // max(1, columns + 1))
        for index in range(columns):
            x = span + index * span + grain(index, salt, 41) % max(1, span // 2)
            top = 2 + grain(index, salt, 43) % max(1, buffer.height // 3)
            length = round(buffer.height * (0.16 + ghost * 0.30))
            for y in range(top, min(buffer.height - 2, top + length), 2):
                value = grain(x, y, salt + index)
                if value % 100 > 38 + ghost * 32:
                    continue
                char = "|" if value % 4 == 0 else ":"
                color = theme.ash if value % 11 == 0 else theme.ghost
                buffer.write_cell(x, y, char, fg=color, dim=value % 11 != 0)

    def _forge(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        amount: float,
    ) -> None:
        theme = model.visual_theme
        character = theme.character
        weight = min(1.0, amount + character.weight * 0.54 + character.grit * 0.18)
        salt = round(beat_time * (2.5 + weight * 4.0) * theme.speed_gain)
        columns = 5 + round(weight * 10)
        span = max(5, buffer.width // columns)
        for index in range(columns):
            x = index * span + span // 2
            height = round(buffer.height * (0.08 + weight * 0.26))
            height += grain(index, salt, 53) % max(1, round(2 + weight * 5))
            for y in range(buffer.height - 3, max(2, buffer.height - height), -1):
                value = grain(x, y, salt + index)
                if value % 100 > 34 + weight * 38:
                    continue
                char = "|" if y % 2 else ":"
                color = theme.primary if value % 7 == 0 else theme.deep
                buffer.write_cell(x, y, char, fg=color, bold=value % 7 == 0)
                if weight > 0.58:
                    buffer.write_cell(x + 1, y, char, fg=theme.ghost, dim=True)

    def _strike(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        amount: float,
    ) -> None:
        theme = model.visual_theme
        character = theme.character
        hit = max(model.auto_hit, model.beat_accent * theme.kick_gain, character.impact)
        strike = min(1.0, amount + hit * 0.62 + character.grit * 0.22)
        if strike < 0.14:
            return
        salt = round(beat_time * (6 + strike * 9) * theme.speed_gain)
        center = buffer.width // 2
        count = 2 + round(strike * 5)
        for index in range(count):
            spread = max(7, round(buffer.width * (0.05 + strike * 0.05)))
            x0 = center + (index - count // 2) * spread
            lean = grain(index, salt, 67) % 11 - 5
            for y in range(2, buffer.height - 2):
                x = x0 + round((y - buffer.height / 2) * lean / 8)
                value = grain(x, y, salt + index)
                if value % 100 > 34 + strike * 40:
                    continue
                char = "/" if lean > 0 else "\\" if lean < 0 else "|"
                color = theme.accent if hit > 0.58 and index % 2 == 0 else theme.primary
                buffer.write_cell(x, y, char, fg=color, bold=strike > 0.72)
                if strike > 0.76:
                    buffer.write_cell(x + 1, y, char, fg=theme.deep, dim=True)


def _amount(model: VJModel) -> float:
    theme = model.visual_theme
    character = theme.character
    pressure = max(model.auto_pressure, model.auto_hit, character.impact * 0.26)
    amount = theme.confidence * 0.46 + pressure * 0.38 + model.beat_accent * 0.22
    amount *= 0.74 + theme.line_gain * 0.26
    return max(0.0, min(1.0, amount))
