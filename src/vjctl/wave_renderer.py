from __future__ import annotations

import math

from .buffer import FrameBuffer
from .model import Wave
from .noise import grain
from .palette import DEEP_RED, RED


class WaveRenderer:
    def render(self, buffer: FrameBuffer, waves: list[Wave], now: float) -> None:
        cx = buffer.width // 2
        cy = buffer.height // 2
        max_radius = math.hypot(buffer.width / 2, buffer.height * 1.25) * 1.18
        for wave in waves:
            age = now - wave.born_at
            if age < 0.0:
                continue
            progress = min(1.0, age / wave.lifetime)
            radius = progress * max_radius
            edge = max(0.0, (max_radius - radius) / max(1.0, max_radius * 0.18))
            energy = 0.34 + wave.strength * 0.42 + wave.aggression * 0.32 + wave.density * 0.14
            energy = min(1.0, energy * min(1.0, edge))
            if energy <= 0.04:
                continue
            bands = 1 + round(wave.density * 3)
            thickness = min(6, 1 + round(wave.density * 3.2 + energy * 1.5))
            spacing = max(thickness * 2.6, 8.0 - wave.density * 1.2)
            for band in range(bands):
                band_radius = radius - band * spacing
                if band_radius <= 0:
                    continue
                band_energy = energy * (1.0 - band / (bands + 2.0))
                draw_shockwave(buffer, cx, cy, band_radius, thickness, band_energy, wave.density, band)


def draw_shockwave(
    buffer: FrameBuffer,
    cx: int,
    cy: int,
    radius: float,
    thickness: int,
    energy: float,
    density: float,
    band: int,
) -> None:
    vertical_scale = 2.5
    y0 = max(2, round(cy - radius / vertical_scale) - thickness)
    y1 = min(buffer.height - 2, round(cy + radius / vertical_scale) + thickness)
    for y in range(y0, y1 + 1):
        vertical = abs(y - cy) * vertical_scale
        remaining = radius * radius - vertical * vertical
        if remaining < 0:
            continue
        dx = round(math.sqrt(remaining))
        for sign in (-1, 1):
            _wave_cluster(buffer, cx, y, dx, sign, thickness, energy, density, band)


def _wave_cluster(
    buffer: FrameBuffer,
    cx: int,
    y: int,
    dx: int,
    sign: int,
    thickness: int,
    energy: float,
    density: float,
    band: int,
) -> None:
    for spread in range(-thickness, thickness + 1):
        x = cx + sign * (dx + spread)
        if not (0 <= x < buffer.width):
            continue
        cell_grain = grain(x, y, band)
        edge = abs(spread) / max(1, thickness)
        if edge > 0.55 and cell_grain % 100 > 42 + density * 18:
            continue
        buffer.write_cell(
            x,
            y,
            _wave_char(energy, edge, cell_grain),
            fg=RED if energy > 0.42 else DEEP_RED,
            bold=energy > 0.56 and edge < 0.55,
        )

    debris = min(5, 1 + round(density * 3 + energy * 1.5))
    for i in range(debris):
        cell_grain = grain(cx + sign * dx + i * sign, y + band, band + i + 9)
        if cell_grain % 100 > 10 + density * 22 + energy * 18:
            continue
        x = cx + sign * (dx + cell_grain % max(2, debris * 2) - debris)
        yy = y + (cell_grain // 13) % 5 - 2
        if 0 <= x < buffer.width and 2 <= yy < buffer.height - 2:
            buffer.write_cell(x, yy, _debris_char(energy, cell_grain), fg=DEEP_RED, dim=energy < 0.66)


def _wave_char(energy: float, edge: float, cell_grain: int) -> str:
    if energy > 0.78 and edge < 0.45:
        return "#" if cell_grain % 5 == 0 else "="
    if energy > 0.5:
        return "=" if cell_grain % 3 else "-"
    if energy > 0.25:
        return "-" if cell_grain % 2 else ":"
    return "." if cell_grain % 3 else ":"


def _debris_char(energy: float, cell_grain: int) -> str:
    if energy > 0.62 and cell_grain % 3 == 0:
        return "="
    if cell_grain % 2 == 0:
        return "-"
    return "."
