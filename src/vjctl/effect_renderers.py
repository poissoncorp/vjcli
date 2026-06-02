from __future__ import annotations

import math

from .buffer import FrameBuffer
from .effects import EFFECT_RENDER_ORDER
from .model import VJModel
from .noise import grain
from .palette import ASH, BLACK, DEEP_RED, RED
from .text_art import choose_art
from .text_layer import TextLayer
from .wave_renderer import draw_shockwave


class EffectRenderers:
    def __init__(self, text: TextLayer) -> None:
        self._text = text
        self._renderers = {
            "overdrive": self._overdrive,
            "pressure": self._pressure,
            "blackout": self._blackout,
            "smear": self._smear,
            "tunnel": self._tunnel,
            "impact": self._impact,
            "chroma": self._chroma,
            "quake": self._quake,
            "collapse": self._collapse,
        }

    def background(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        aggr = max(model.effective_aggression, model.music.energy * 0.62)
        density = max(model.effective_density, model.music.density * 0.74)
        if model.cooldown > 0.92:
            return
        spacing = max(6, round(18 - aggr * 7 - density * 3))
        drift = int(beat_time * (3 + aggr * 9 + model.music.brightness * 5)) % spacing
        for y in range(2, buffer.height - 2, spacing):
            for x in range(-drift, buffer.width, 19):
                char = "-" if (x + y) % 3 else "."
                buffer.write_cell(x, y, char, fg=DEEP_RED, dim=True)
        for x in range(0, buffer.width, 16):
            if (x // 16 + int(beat_time)) % 3 != 1:
                buffer.write_text(x, buffer.height - 2, ".__", fg=DEEP_RED, dim=True)

    def effects(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        for spec in EFFECT_RENDER_ORDER:
            effect = model.effects.get(spec.name)
            render = self._renderers.get(spec.render)
            if effect is None or render is None:
                continue
            render(buffer, model, effect.charge, effect.release, beat_time)

    def _pressure(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        if charge <= 0.01 and release <= 0.01:
            return
        cx = buffer.width // 2
        cy = buffer.height // 2
        amount = min(1.0, charge + release)
        width = round(amount * buffer.width * 0.42)
        for offset in range(-5, 6):
            y = cy + offset
            if not (0 <= y < buffer.height):
                continue
            char = "=" if abs(offset) < 2 else "-"
            step = 1 if abs(offset) < 2 else 2
            for x in range(cx - width, cx + width + 1, step):
                if grain(x, y, round(beat_time * 4)) % 100 < 12 and abs(offset) > 2:
                    continue
                buffer.write_cell(x, y, char, fg=RED, bold=abs(offset) < 3)

    def _overdrive(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        amount = max(charge, release)
        if amount <= 0.01:
            return
        salt = round(beat_time * 8)
        for y in range(2, buffer.height - 2):
            if grain(y, salt, 1) % 100 > 34 + amount * 48:
                continue
            for x in range(0, buffer.width, 2):
                cell_grain = grain(x, y, salt)
                if cell_grain % 100 > 22 + amount * 44:
                    continue
                char = "=" if cell_grain % 5 == 0 else "#" if cell_grain % 19 == 0 else "-"
                color = RED if cell_grain % 7 == 0 else DEEP_RED
                buffer.write_cell(x, y, char, fg=color, bold=cell_grain % 13 == 0)
        for offset in range(-4, 5):
            y = buffer.height // 2 + offset * 2
            if 0 <= y < buffer.height:
                buffer.write_text(0, y, "=" * buffer.width, fg=RED, bold=abs(offset) < 2)

    def _blackout(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        if charge <= 0.01 and release <= 0.01:
            return
        gate = min(0.92, charge * 0.78)
        if release > 0.2:
            gate *= 0.4
        for y in range(buffer.height):
            for x in range(buffer.width):
                if ((x + y) % 11) / 11.0 < gate:
                    buffer.write_cell(x, y, " ", fg=BLACK)
        if release > 0.1:
            y = buffer.height // 2
            buffer.write_text(0, y, "=" * buffer.width, fg=RED, bold=True)

    def _smear(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        if charge <= 0.01 and release <= 0.01:
            return
        amount = max(charge, release)
        step = max(2, round(9 - amount * 6))
        for y in range(3, buffer.height - 3, step):
            start = int(beat_time * 8 + y * 3) % max(1, buffer.width)
            length = round(buffer.width * (0.2 + amount * 0.42))
            for x in range(start, min(buffer.width, start + length)):
                if x % 2 == 0 or amount > 0.72:
                    char = "_" if x % 3 else "-"
                    color = RED if amount > 0.72 else DEEP_RED
                    buffer.write_cell(x, y, char, fg=color, dim=amount < 0.7)

    def _tunnel(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        if charge <= 0.01 and release <= 0.01:
            return
        cx = buffer.width // 2
        cy = buffer.height // 2
        amount = min(1.0, charge + release)
        rings = 3 + round(amount * 8)
        for i in range(rings):
            w = round((i + 1) * buffer.width / (rings + 3))
            h = round((i + 1) * buffer.height / (rings + 4))
            char = "=" if amount > 0.72 and i < 3 else ":" if i % 2 else "."
            color = RED if amount > 0.55 and i < 4 else DEEP_RED
            x_step = 2 if amount > 0.7 else 3
            y_step = 1 if amount > 0.7 else 2
            for x in range(cx - w // 2, cx + w // 2 + 1, x_step):
                buffer.write_cell(x, cy - h // 2, char, fg=color)
                buffer.write_cell(x, cy + h // 2, char, fg=color)
            for y in range(cy - h // 2, cy + h // 2 + 1, y_step):
                buffer.write_cell(cx - w // 2, y, char, fg=color)
                buffer.write_cell(cx + w // 2, y, char, fg=color)

    def _impact(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        if release <= 0.02:
            return
        height = min(9, max(5, buffer.height - 4))
        lines = choose_art("DROP IMPACT", max(8, buffer.width - 8), height)
        width = max(len(line) for line in lines)
        x = max(0, (buffer.width - width) // 2)
        y = max(2, (buffer.height - len(lines)) // 2)
        self._text.write_lines(buffer, lines, x, y, RED, model, beat_time)
        if release <= 0.55:
            return
        buffer.write_text(0, max(0, y - 2), "-" * buffer.width, fg=RED, bold=True)
        bottom_y = min(buffer.height - 1, y + len(lines) + 1)
        buffer.write_text(0, bottom_y, "-" * buffer.width, fg=RED, bold=True)
        for offset in range(-5, 6):
            yy = y + len(lines) // 2 + offset
            if 0 <= yy < buffer.height and offset % 2 == 0:
                buffer.write_text(0, yy, "=" * buffer.width, fg=DEEP_RED, dim=abs(offset) > 2)

    def _chroma(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        music = model.music
        music_amount = 0.0
        if music.confidence >= 0.08:
            music_amount = min(1.0, music.brightness * 0.42 + music.change * 0.36)
        amount = max(charge, release, music_amount)
        if amount <= 0.01:
            return
        salt = round(beat_time * 8)
        for y in range(2, buffer.height - 2):
            if grain(y, salt, 7) % 100 > 20 + amount * 40:
                continue
            shift = -2 + grain(y, salt, 11) % 5
            for x in range(0, buffer.width, 4):
                if grain(x, y, salt) % 100 < 28 + amount * 36:
                    char = "-" if x % 8 else "="
                    color = ASH if shift > 0 else RED
                    buffer.write_cell(x + shift, y, char, fg=color)

    def _quake(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        amount = max(charge, release)
        if amount <= 0.01:
            return
        cx = buffer.width // 2
        cy = buffer.height // 2
        radius = math.hypot(buffer.width / 2, buffer.height * 1.25) * (0.35 + amount * 0.75)
        salt = round(beat_time * 4)
        draw_shockwave(buffer, cx, cy, radius, 9, amount, 1.0, salt)
        draw_shockwave(buffer, cx, cy, radius * 0.72, 6, amount * 0.84, 1.0, salt + 3)

    def _collapse(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        charge: float,
        release: float,
        beat_time: float,
    ) -> None:
        amount = max(charge, release)
        if amount <= 0.01:
            return
        cx = buffer.width // 2
        width = round(buffer.width * (0.08 + amount * 0.18))
        salt = round(beat_time * 4)
        for x in range(cx - width, cx + width + 1):
            for y in range(1, buffer.height - 1):
                if grain(x, y, salt) % 100 < 74:
                    buffer.write_cell(x, y, " ", fg=BLACK)
        for offset in range(-width, width + 1, 3):
            x = cx + offset
            for y in range(2, buffer.height - 2, 2):
                if grain(x, y, salt + 7) % 100 < 42 + amount * 40:
                    char = "|" if offset % 2 else ":"
                    buffer.write_cell(x, y, char, fg=RED, dim=abs(offset) > width * 0.55)
