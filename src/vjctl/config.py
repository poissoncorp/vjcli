from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_FILENAME = "vjctl.toml"
TUNING_KEYS = {
    "sensitivity",
    "confidence_threshold",
    "onset_threshold",
    "onset_debounce",
    "effect_threshold",
    "effect_debounce",
}


@dataclass(frozen=True)
class PerformanceConfig:
    preset: str | None = None
    visual_mode: str | None = None
    tuning: dict[str, float] = field(default_factory=dict)
    loaded_from: Path | None = None


def load_performance_config(path: str | None, disabled: bool) -> PerformanceConfig:
    resolved = _config_path(path, disabled)
    if resolved is None:
        return PerformanceConfig()
    try:
        data = tomllib.loads(resolved.read_text(encoding="utf-8"))
    except OSError as error:
        raise RuntimeError(f"Could not read config {resolved}: {error}") from error
    except tomllib.TOMLDecodeError as error:
        raise RuntimeError(f"Could not parse config {resolved}: {error}") from error
    section = data.get("performance", data)
    if not isinstance(section, dict):
        raise RuntimeError("Config performance section must be a table.")
    return _performance_config(section, resolved)


def _config_path(path: str | None, disabled: bool) -> Path | None:
    if disabled:
        return None
    if path is not None:
        return Path(path).expanduser()
    candidate = Path.cwd() / CONFIG_FILENAME
    return candidate if candidate.exists() else None


def _performance_config(data: dict[str, Any], loaded_from: Path) -> PerformanceConfig:
    allowed = TUNING_KEYS | {"preset", "visual_mode"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        names = ", ".join(unknown)
        raise RuntimeError(f"Unknown performance config key: {names}")
    preset = _text(data.get("preset"), "preset")
    visual_mode = _text(data.get("visual_mode"), "visual_mode")
    tuning = {key: _number(data[key], key) for key in TUNING_KEYS if key in data}
    return PerformanceConfig(preset, visual_mode, tuning, loaded_from)


def _text(value: Any, key: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise RuntimeError(f"Config key {key} must be text.")


def _number(value: Any, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"Config key {key} must be a number.")
    return float(value)
