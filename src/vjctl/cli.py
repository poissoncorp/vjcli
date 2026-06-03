from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from .audio_input import audio_device_lines, audio_output_lines
from .app import render_preview, run, run_meter
from .config import PerformanceConfig, load_performance_config
from .music_reactor import MusicTuning
from .performance import (
    DEFAULT_PERFORMANCE_PRESET,
    PERFORMANCE_PRESETS,
    performance_preset,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="vjctl", description="Terminal VJ control realm.")
    parser.add_argument("--music", choices=("none", "demo", "audio"), default="audio")
    parser.add_argument("--audio-device", default=None)
    parser.add_argument("--list-audio-devices", action="store_true")
    parser.add_argument("--list-audio-outputs", action="store_true")
    parser.add_argument("--meter", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--lsd", action="store_true")
    parser.add_argument("--config", default=None)
    parser.add_argument("--no-config", action="store_true")
    parser.add_argument(
        "--preset",
        choices=tuple(PERFORMANCE_PRESETS),
        default=None,
    )
    parser.add_argument("--sensitivity", type=float, default=None)
    parser.add_argument("--visual-mode", choices=("waves", "string"), default=None)
    parser.add_argument("--meter-frames", type=int, default=120, help=argparse.SUPPRESS)
    parser.add_argument("--meter-fps", type=int, default=20, help=argparse.SUPPRESS)
    parser.add_argument("--confidence-threshold", type=float, default=None)
    parser.add_argument("--onset-threshold", type=float, default=None)
    parser.add_argument("--onset-debounce", type=float, default=None)
    parser.add_argument("--effect-threshold", type=float, default=None)
    parser.add_argument("--effect-debounce", type=float, default=None)
    parser.add_argument("--preview-frames", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--width", type=int, default=132, help=argparse.SUPPRESS)
    parser.add_argument("--height", type=int, default=36, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_audio_devices:
        return _list_audio_devices()
    if args.list_audio_outputs:
        return _list_audio_outputs()
    try:
        config = load_performance_config(args.config, args.no_config)
        preset_name, tuning, visual_mode = _performance(args, config)
    except RuntimeError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    if args.meter:
        device = _audio_device(args.audio_device)
        return run_meter(
            args.music,
            device,
            args.meter_frames,
            args.meter_fps,
            tuning,
            args.lsd,
            visual_mode,
            preset_name,
        )
    if args.preview_frames > 0:
        sys.stdout.write(
            render_preview(
                args.preview_frames,
                args.width,
                args.height,
                music=args.music,
                music_tuning=tuning,
                debug=args.debug,
                lsd=args.lsd,
                visual_mode=visual_mode,
                performance_preset=preset_name,
            )
        )
        return 0
    return run(
        music=args.music,
        audio_device=_audio_device(args.audio_device),
        music_tuning=tuning,
        debug=args.debug,
        lsd=args.lsd,
        visual_mode=visual_mode,
        performance_preset=preset_name,
    )


def _audio_device(value: str | None) -> str | int | None:
    if value is None:
        return None
    if value.isdigit():
        return int(value)
    return value


def _performance(
    args: argparse.Namespace,
    config: PerformanceConfig,
) -> tuple[str, MusicTuning, str]:
    requested_preset = args.preset or config.preset or DEFAULT_PERFORMANCE_PRESET
    preset = performance_preset(requested_preset)
    if preset is None:
        raise RuntimeError(f"Unknown performance preset: {requested_preset}")
    tuning = preset.tuning
    overrides = _config_overrides(config)
    overrides.update(_cli_overrides(args))
    if overrides:
        tuning = replace(tuning, **overrides)
    visual_mode = args.visual_mode or config.visual_mode or preset.visual_mode
    if visual_mode not in ("waves", "string"):
        raise RuntimeError(f"Unknown visual mode: {visual_mode}")
    custom = bool(overrides or args.visual_mode is not None or config.visual_mode is not None)
    preset_name = "custom" if custom else preset.name
    return preset_name, tuning, visual_mode


def _config_overrides(config: PerformanceConfig) -> dict[str, float]:
    return {key: _tuning_value(key, value) for key, value in config.tuning.items()}


def _cli_overrides(args: argparse.Namespace) -> dict[str, float]:
    values = {
        "sensitivity": args.sensitivity,
        "confidence_threshold": args.confidence_threshold,
        "onset_threshold": args.onset_threshold,
        "onset_debounce": args.onset_debounce,
        "effect_threshold": args.effect_threshold,
        "effect_debounce": args.effect_debounce,
    }
    return {
        key: _tuning_value(key, value)
        for key, value in values.items()
        if value is not None
    }


def _tuning_value(key: str, value: float) -> float:
    if key in ("onset_debounce", "effect_debounce"):
        return max(0.0, float(value))
    return _amount(value)


def _amount(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


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


def _list_audio_outputs() -> int:
    try:
        lines = audio_output_lines()
    except RuntimeError as error:
        sys.stderr.write(f"{error}\n")
        return 2
    if not lines:
        sys.stdout.write("No audio output devices found.\n")
        return 0
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
