from __future__ import annotations

import argparse
import sys

from .app import render_preview, run, run_meter
from .audio_input import audio_device_lines


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="vjctl", description="Terminal VJ control realm.")
    parser.add_argument("--music", choices=("none", "demo", "audio"), default="none")
    parser.add_argument("--audio-device", default=None)
    parser.add_argument("--list-audio-devices", action="store_true")
    parser.add_argument("--meter", action="store_true")
    parser.add_argument("--meter-frames", type=int, default=120, help=argparse.SUPPRESS)
    parser.add_argument("--meter-fps", type=int, default=20, help=argparse.SUPPRESS)
    parser.add_argument("--preview-frames", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--width", type=int, default=132, help=argparse.SUPPRESS)
    parser.add_argument("--height", type=int, default=36, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_audio_devices:
        return _list_audio_devices()
    if args.meter:
        device = _audio_device(args.audio_device)
        return run_meter(args.music, device, args.meter_frames, args.meter_fps)
    if args.preview_frames > 0:
        sys.stdout.write(
            render_preview(args.preview_frames, args.width, args.height, music=args.music)
        )
        return 0
    return run(args.music, _audio_device(args.audio_device))


def _audio_device(value: str | None) -> str | int | None:
    if value is None:
        return None
    if value.isdigit():
        return int(value)
    return value


def _list_audio_devices() -> int:
    try:
        lines = audio_device_lines()
    except RuntimeError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    if not lines:
        sys.stdout.write("No audio input devices found.\n")
        return 0
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
