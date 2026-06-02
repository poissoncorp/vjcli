from __future__ import annotations

from .buffer import FrameBuffer
from .model import VJModel
from .noise import grain
from .palette import BLACK, DEEP_RED, RED, Color
from .text_art import choose_art

PIXEL = "█"


class PlainText:
    def render(
        self,
        buffer: FrameBuffer,
        text: str,
        x: int,
        y: int,
        color: Color,
        minor: bool = False,
    ) -> None:
        buffer.write_text(x, y, text, fg=color, bold=not minor, dim=minor)


class ArtText:
    def render_text(
        self,
        buffer: FrameBuffer,
        text: str,
        color: Color,
        model: VJModel,
        beat_time: float,
        mode: str = "hero",
    ) -> None:
        lines = choose_art(text, max(8, buffer.width - 8), max(5, buffer.height - 6))
        width = max(len(line) for line in lines)
        x = max(0, (buffer.width - width) // 2)
        y = max(2, (buffer.height - len(lines)) // 2)
        self.render_lines(buffer, lines, x, y, color, model, beat_time, mode)

    def render_lines(
        self,
        buffer: FrameBuffer,
        lines: list[str],
        x: int,
        y: int,
        color: Color,
        model: VJModel,
        beat_time: float,
        mode: str = "hero",
        knockout: bool = True,
    ) -> None:
        theme = model.visual_theme
        chroma = _effect_amount(model, "chroma")
        overdrive = _effect_amount(model, "overdrive")
        collapse = _effect_amount(model, "collapse")
        music_fault = _music_fault(model)
        intensity = _text_intensity(mode)
        damage = 0.01 + model.effective_density * 0.04 + chroma * 0.12
        damage = min(0.24, damage + overdrive * 0.15 + collapse * 0.08 + music_fault * 0.11)
        split = 0.08 + chroma * 0.76 + overdrive * 0.24 + collapse * 0.2 + music_fault * 0.34
        damage *= intensity
        split = min(1.0, split) * intensity
        salt = round(beat_time * (4 + split * 10))
        if knockout:
            _knockout(buffer, lines, x, y)
        left_x = x - 1 - round(split * 3)
        _pixel_layer(buffer, lines, left_x, y, theme.deep, salt + 3, split * 0.42, True)
        _pixel_layer(
            buffer,
            lines,
            x + 1 + round(split * 4),
            y,
            theme.primary,
            salt + 7,
            split * 0.55,
            True,
        )
        _pixel_layer(buffer, lines, x + 1, y - 1, theme.ghost, salt + 11, split * 0.28, True)
        _pixel_layer(buffer, lines, x, y, color, salt, damage, False, theme.primary, theme.deep)


class TextLayer:
    def __init__(self) -> None:
        self._plain = PlainText()
        self._art = ArtText()

    def social(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        for event in model.socials:
            text = f"{event.nick} {'FOLLOW' if event.kind == 'follow' else '<3'}".upper()
            text = _clip(text, max(18, min(buffer.width // 3, 44)))
            width = len(text)
            x = round(buffer.width * event.x) - width // 2
            y = round(buffer.height * event.y)
            top = 4 if buffer.height >= 18 else 0
            bottom = max(top, buffer.height - 2)
            x = max(0, min(buffer.width - width, x))
            y = max(top, min(bottom, y))
            theme = model.visual_theme
            color = theme.primary if event.kind == "follow" else theme.ash
            self._plain.render(buffer, text, x, y, color, True)

    def overlays(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        if not model.overlays:
            return
        overlay = model.overlays[-1]
        theme = model.visual_theme
        color = theme.ash if overlay.kind == "system" else theme.primary
        if overlay.kind == "system":
            text = _clip(overlay.text, max(8, buffer.width - 8))
            x = max(0, (buffer.width - len(text)) // 2)
            y = max(2, buffer.height // 2)
            self._plain.render(buffer, text, x, y, color)
            return
        self._art.render_text(buffer, overlay.text, color, model, beat_time)

    def prompt(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        if not model.prompt:
            return
        text = _clip(model.prompt, max(8, buffer.width - 8))
        x = max(0, (buffer.width - len(text)) // 2)
        y = min(buffer.height - 3, max(2, buffer.height // 2 + 2))
        theme = model.visual_theme
        color = theme.primary if model.prompt.startswith("/") else theme.ash
        self._plain.render(buffer, text, x, y, color)

    def hud(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        if buffer.width < 82 or buffer.height < 20:
            return
        timing = model.timing
        theme = model.visual_theme
        mode = "LOCK" if timing.locked else timing.source.upper()
        bpm = round(timing.bpm)
        self._plain.render(
            buffer,
            f"{mode} {bpm}",
            buffer.width - len(f"{mode} {bpm}") - 2,
            0,
            theme.primary,
            True,
        )
        if model.prompt or model.overlays or model.socials or buffer.height < 28:
            return
        aggr = round(model.effective_aggression * 100)
        dens = round(model.effective_density * 100)
        meters = f"A{aggr:02d} D{dens:02d}"
        self._plain.render(
            buffer,
            meters,
            buffer.width - len(meters) - 2,
            3,
            theme.primary,
            True,
        )

    def write_lines(
        self,
        buffer: FrameBuffer,
        lines: list[str],
        x: int,
        y: int,
        color: Color,
        model: VJModel,
        beat_time: float,
        mode: str = "hero",
        knockout: bool = True,
    ) -> None:
        self._art.render_lines(buffer, lines, x, y, color, model, beat_time, mode, knockout)


def _knockout(buffer: FrameBuffer, lines: list[str], x: int, y: int) -> None:
    for row_index, line in enumerate(lines):
        for col_index, char in enumerate(line):
            if char == " ":
                continue
            for yy in range(y + row_index - 1, y + row_index + 2):
                for xx in range(x + col_index - 1, x + col_index + 2):
                    buffer.write_cell(xx, yy, " ", fg=BLACK, bg=BLACK)


def _pixel_layer(
    buffer: FrameBuffer,
    lines: list[str],
    x: int,
    y: int,
    color: Color,
    salt: int,
    amount: float,
    ghost: bool,
    edge_primary: Color = RED,
    edge_deep: Color = DEEP_RED,
) -> None:
    if ghost and amount <= 0.02:
        return
    for row_index, line in enumerate(lines):
        shear = _row_shear(row_index, salt, amount * (1.25 if ghost else 0.45))
        for col_index, char in enumerate(line):
            if char == " ":
                continue
            xx = x + col_index + shear
            yy = y + row_index
            cell_grain = grain(xx, yy, salt)
            if ghost:
                if cell_grain % 100 > 7 + amount * 48:
                    continue
                buffer.write_cell(xx, yy, _art_char(char), fg=color, dim=True)
                continue
            if cell_grain % 100 < amount * 5:
                continue
            buffer.write_cell(xx, yy, _art_char(char), fg=color, bold=True)
            if cell_grain % 100 < 4 + amount * 22:
                slip = cell_grain % 7 - 3
                if slip != 0:
                    edge = edge_primary if slip > 0 else edge_deep
                    buffer.write_cell(xx + slip, yy, _art_char(char), fg=edge, dim=True)


def _art_char(char: str) -> str:
    return PIXEL if char == "#" else char


def _effect_amount(model: VJModel, effect_id: str) -> float:
    effect = model.effects.get(effect_id)
    if effect is None:
        return 0.0
    return max(effect.charge, effect.release)


def _music_fault(model: VJModel) -> float:
    frame = model.music
    if frame.confidence < 0.08:
        return 0.0
    return min(1.0, frame.brightness * 0.52 + frame.change * 0.5 + frame.onset * 0.18)


def _row_shear(row: int, salt: int, amount: float) -> int:
    if amount <= 0.04:
        return 0
    row_grain = grain(row, salt, 901507)
    if row_grain % 100 > 18 + amount * 34:
        return 0
    return (row_grain % max(1, round(2 + amount * 8))) - round(1 + amount * 4)


def _text_intensity(mode: str) -> float:
    if mode == "minor":
        return 0.22
    if mode == "prompt":
        return 0.58
    return 1.0


def _clip(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[:max(1, width)]
