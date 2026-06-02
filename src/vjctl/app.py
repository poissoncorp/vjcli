from __future__ import annotations

import os
import select
import shutil
import sys
import termios
import time
import tty

from .ansi import ALT_SCREEN, CLEAR, HIDE_CURSOR, MAIN_SCREEN, RESET, SHOW_CURSOR
from .audio_input import AudioInputSource
from .effects import EFFECT_BY_KEY
from .input import InputDecoder, InputEvent
from .model import MusicTuning, VJModel
from .music import MusicFrame, MusicSource
from .renderer import Renderer
from .sources import SimulatedMusicSource, SimulatedSocialSource


class TerminalSession:
    def __init__(self) -> None:
        self.fd = sys.stdin.fileno()
        self.original: list[int] | None = None

    def __enter__(self) -> "TerminalSession":
        self.original = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        sys.stdout.write(ALT_SCREEN + HIDE_CURSOR + CLEAR)
        sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        sys.stdout.write(RESET + SHOW_CURSOR + MAIN_SCREEN)
        sys.stdout.flush()
        if self.original is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.original)


def run(
    music: str = "none",
    audio_device: str | int | None = None,
    music_tuning: MusicTuning | None = None,
) -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        sys.stderr.write(
            "vjctl needs an interactive terminal. Use --preview-frames for text preview.\n"
        )
        return 2
    try:
        music_source = _music_source(music, audio_device)
    except RuntimeError as error:
        sys.stderr.write(f"{error}\n")
        return 2

    model = VJModel(music_tuning=music_tuning or MusicTuning())
    renderer = Renderer()
    decoder = InputDecoder()
    social_source = SimulatedSocialSource()
    target_dt = 1.0 / 60.0
    last_frame = time.monotonic()
    last_esc_check = last_frame

    try:
        with TerminalSession():
            while True:
                now = time.monotonic()
                dt = min(0.1, now - last_frame)
                last_frame = now

                for event in _read_events(decoder):
                    if _handle_event(model, event, now):
                        return 0

                if now - last_esc_check > 0.32:
                    for event in decoder.flush_escape():
                        if _handle_event(model, event, now):
                            return 0
                    last_esc_check = now

                model.update(dt, now)
                _poll_music(model, music_source, now)
                for event in social_source.poll(now, model.cooldown):
                    model.apply_event(event, now)
                size = shutil.get_terminal_size((132, 36))
                frame = renderer.render(model, size.columns, size.lines, now)
                sys.stdout.write(renderer.flush(frame))
                sys.stdout.flush()

                elapsed = time.monotonic() - now
                if elapsed < target_dt:
                    time.sleep(target_dt - elapsed)
    except KeyboardInterrupt:
        return 0
    finally:
        _close_source(music_source)


def render_preview(
    frames: int,
    width: int,
    height: int,
    fps: int = 12,
    music: str = "none",
    music_tuning: MusicTuning | None = None,
) -> str:
    model = VJModel(music_tuning=music_tuning or MusicTuning())
    renderer = Renderer()
    social_source = SimulatedSocialSource()
    music_source = _music_source(music if music == "demo" else "none")
    lines: list[str] = []
    now = 0.0
    dt = 1.0 / max(1, fps)
    model.prompt = "vjctl realm"
    model.submit_prompt(now)
    for index in range(max(0, frames)):
        beat = model.update(dt, now)
        _poll_music(model, music_source, now)
        for event in social_source.poll(now, model.cooldown):
            model.apply_event(event, now)
        if beat and index % 8 == 0:
            model.hold("3", now)
        frame = renderer.render(model, width, height, now)
        lines.append(f"vjctl preview frame {index + 1}")
        lines.extend(frame.row_text(y).rstrip() for y in range(frame.height))
        lines.append("")
        now += dt
    return "\n".join(lines)


def run_meter(
    music: str,
    audio_device: str | int | None = None,
    frames: int = 120,
    fps: int = 20,
    music_tuning: MusicTuning | None = None,
) -> int:
    if music == "none":
        sys.stderr.write("Choose --music demo or --music audio for meter.\n")
        return 2
    try:
        source = _music_source(music, audio_device)
    except RuntimeError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    if source is None:
        return 2
    model = VJModel(music_tuning=music_tuning or MusicTuning())
    interval = 1.0 / max(1, fps)
    next_at = time.monotonic()
    sys.stdout.write("frame energy bass high dens onset change conf trig aggr mdens\n")
    try:
        for index in range(max(0, frames)):
            now = time.monotonic()
            frame = source.poll(now) or MusicFrame()
            wave_count = len(model.waves)
            model.apply_music(frame, now)
            hit = len(model.waves) > wave_count
            sys.stdout.write(_meter_line(index, frame, model, hit))
            sys.stdout.flush()
            next_at += interval
            delay = next_at - time.monotonic()
            if delay > 0.0:
                time.sleep(delay)
        return 0
    finally:
        _close_source(source)


def _music_source(name: str, audio_device: str | int | None = None) -> MusicSource | None:
    if name == "demo":
        return SimulatedMusicSource()
    if name == "audio":
        return AudioInputSource(device=audio_device)
    return None


def _close_source(source: MusicSource | None) -> None:
    close = getattr(source, "close", None)
    if close is not None:
        close()


def _poll_music(model: VJModel, source: MusicSource | None, now: float) -> None:
    if source is None:
        return
    frame = source.poll(now)
    if frame is not None:
        model.apply_music(frame, now)


def _meter_line(index: int, frame: MusicFrame, model: VJModel, hit: bool) -> str:
    values = (
        frame.energy,
        frame.bass,
        frame.brightness,
        frame.density,
        frame.onset,
        frame.change,
        frame.confidence,
        1.0 if hit else 0.0,
        model.effective_aggression,
        model.effective_density,
    )
    return f"{index:05d} " + " ".join(f"{value:.3f}" for value in values) + "\n"


def _read_events(decoder: InputDecoder) -> list[InputEvent]:
    events: list[InputEvent] = []
    while True:
        readable, _, _ = select.select([sys.stdin], [], [], 0)
        if not readable:
            return events
        data = os.read(sys.stdin.fileno(), 64)
        if not data:
            return events
        events.extend(decoder.feed(data))


def _handle_event(model: VJModel, event: InputEvent, now: float) -> bool:
    if event.kind == "exit":
        return True
    if event.kind == "ignore":
        return False
    if event.kind == "tap":
        model.tap(now)
        return False
    if event.kind == "enter":
        model.submit_prompt(now)
        return False
    if event.kind == "backspace":
        model.text_input("\b")
        return False
    if event.kind == "char":
        if not model.prompt and event.value.isdigit():
            effect = EFFECT_BY_KEY.get(event.value)
            if effect is not None:
                model.hold(event.value, now)
            return False
        model.text_input(event.value)
        return False
    if event.kind == "hold":
        model.hold(event.value, now)
        return False
    if event.kind == "slider":
        model.slider(0.25 if event.value == "up" else -0.25)
        return False
    if event.kind == "jog":
        model.jog(0.018 if event.value == "right" else -0.018)
        return False
    return False
