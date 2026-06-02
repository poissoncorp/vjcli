from __future__ import annotations

from .buffer import FrameBuffer
from .model import VJModel
from .noise import grain
from .palette import ASH, DEEP_RED, RED


class SceneRenderer:
    def render(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        if model.cooldown > 0.92:
            return
        scene = model.auto_scene
        pressure = max(model.auto_pressure, model.music.energy * 0.08, model.auto_hit * 0.54)
        if scene in ("idle", "listen"):
            self._listen(buffer, model, beat_time, pressure)
        elif scene == "drive":
            self._drive(buffer, model, beat_time, pressure)
        elif scene == "fault":
            self._fault(buffer, model, beat_time, pressure)
        elif scene == "weight":
            self._weight(buffer, model, beat_time, pressure)
        elif scene == "rupture":
            self._rupture(buffer, model, beat_time, pressure)
        elif scene == "chaos":
            self._chaos(buffer, model, beat_time, pressure)
        self._aftershock(buffer, model, beat_time)

    def _listen(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        pressure: float,
    ) -> None:
        if pressure < 0.04:
            return
        salt = round(beat_time * 2)
        for x in range(0, buffer.width, 24):
            if grain(x, salt, 11) % 100 > 18 + pressure * 34:
                continue
            buffer.write_text(x, 1, ".-", fg=DEEP_RED, dim=True)
            buffer.write_text(x, buffer.height - 2, "_.", fg=DEEP_RED, dim=True)

    def _drive(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        pressure: float,
    ) -> None:
        amount = max(0.16, min(1.0, pressure + model.music.energy * 0.18))
        salt = round(beat_time * (4 + amount * 6))
        step = max(3, round(9 - amount * 4))
        drift = salt % max(1, step * 3)
        for y in range(3, buffer.height - 3, step):
            length = round(buffer.width * (0.12 + amount * 0.18))
            for x in range(-drift, buffer.width, max(9, length + 8)):
                self._rail(buffer, x, y, length, amount, salt + y)

    def _fault(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        pressure: float,
    ) -> None:
        amount = max(0.22, min(1.0, pressure + model.music.brightness * 0.4))
        salt = round(beat_time * (6 + amount * 10))
        for y in range(2, buffer.height - 2):
            if grain(y, salt, 23) % 100 > 18 + amount * 38:
                continue
            shift = grain(y, salt, 29) % 9 - 4
            for x in range(0, buffer.width, 13):
                if grain(x, y, salt) % 100 > 28 + amount * 44:
                    continue
                char = "=" if amount > 0.56 else "-"
                color = ASH if shift > 0 else RED
                buffer.write_cell(x + shift, y, char, fg=color, dim=amount < 0.6)

    def _weight(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        pressure: float,
    ) -> None:
        amount = max(0.20, min(1.0, pressure + model.music.bass * 0.36))
        salt = round(beat_time * 3)
        columns = 4 + round(amount * 8)
        span = max(6, buffer.width // max(1, columns))
        for index in range(columns):
            x = index * span + span // 2
            height = round(buffer.height * (0.10 + amount * 0.34))
            height += grain(index, salt, 31) % max(1, round(2 + amount * 5))
            for y in range(buffer.height - 3, max(1, buffer.height - height), -1):
                if grain(x, y, salt) % 100 > 34 + amount * 42:
                    continue
                char = "|" if y % 2 else ":"
                buffer.write_cell(x, y, char, fg=DEEP_RED, dim=amount < 0.58)
                if amount > 0.62:
                    buffer.write_cell(x + 1, y, char, fg=RED, dim=True)

    def _rupture(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        pressure: float,
    ) -> None:
        amount = max(0.30, min(1.0, pressure + model.music.change * 0.28))
        salt = round(beat_time * (5 + amount * 7))
        center = buffer.width // 2
        cuts = 2 + round(amount * 5)
        for cut in range(cuts):
            x0 = center + (cut - cuts // 2) * max(7, round(buffer.width * 0.08))
            lean = grain(cut, salt, 41) % 9 - 4
            for y in range(2, buffer.height - 2):
                x = x0 + round((y - buffer.height / 2) * lean / 9)
                if grain(x, y, salt + cut) % 100 > 44 + amount * 34:
                    continue
                char = "/" if lean > 0 else "\\" if lean < 0 else "|"
                buffer.write_cell(x, y, char, fg=RED, bold=amount > 0.62)

    def _chaos(
        self,
        buffer: FrameBuffer,
        model: VJModel,
        beat_time: float,
        pressure: float,
    ) -> None:
        amount = max(0.42, min(1.0, pressure + model.music.drive * 0.22))
        self._drive(buffer, model, beat_time, amount)
        self._fault(buffer, model, beat_time, amount)
        if amount > 0.62:
            self._rupture(buffer, model, beat_time, amount * 0.86)

    def _aftershock(self, buffer: FrameBuffer, model: VJModel, beat_time: float) -> None:
        hit = model.auto_hit
        if hit < 0.06:
            return
        salt = round(beat_time * (7 + hit * 9))
        center_x = buffer.width // 2
        center_y = buffer.height // 2
        bands = 2 + round(hit * 4)
        span = round(buffer.width * (0.16 + hit * 0.28))
        for band in range(bands):
            y = center_y + (band - bands // 2) * max(2, round(buffer.height * 0.07))
            jitter = grain(band, salt, 53) % 7 - 3
            for x in range(center_x - span, center_x + span, 2):
                if grain(x, y, salt + band) % 100 > 52 + hit * 30:
                    continue
                char = "=" if hit > 0.52 and x % 3 == 0 else "-"
                color = RED if grain(x, band, salt) % 100 < 70 else ASH
                buffer.write_cell(x + jitter, y, char, fg=color, bold=hit > 0.7, dim=hit < 0.42)

        step = max(2, round(7 - hit * 4))
        inset = max(1, round(buffer.width * (0.025 + hit * 0.035)))
        for y in range(3, buffer.height - 3, step):
            if grain(y, salt, 61) % 100 > 34 + hit * 42:
                continue
            char = "|" if hit > 0.58 else ":"
            buffer.write_cell(inset, y, char, fg=RED, dim=hit < 0.5)
            buffer.write_cell(buffer.width - inset - 1, y, char, fg=RED, dim=hit < 0.5)

    def _rail(
        self,
        buffer: FrameBuffer,
        x: int,
        y: int,
        length: int,
        amount: float,
        salt: int,
    ) -> None:
        for offset in range(max(0, length)):
            xx = x + offset
            if not (0 <= xx < buffer.width):
                continue
            if grain(xx, y, salt) % 100 > 46 + amount * 32:
                continue
            char = "=" if amount > 0.64 and offset % 3 == 0 else "-"
            color = RED if amount > 0.7 else DEEP_RED
            buffer.write_cell(xx, y, char, fg=color, dim=amount < 0.68)
