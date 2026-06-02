from __future__ import annotations

from collections import deque
from threading import Lock

from .analyzer import AudioAnalyzer
from .music import MusicFrame

INSTALL_AUDIO_MESSAGE = "Install audio support with `python3 -m pip install -e .[audio]`."


class AudioInputSource:
    def __init__(
        self,
        device: str | int | None = None,
        sample_rate: int = 16_000,
        block_size: int = 512,
    ) -> None:
        sounddevice = _audio_stack()
        self.sample_rate = sample_rate
        self.samples: deque[float] = deque(maxlen=sample_rate)
        self.lock = Lock()
        self.analyzer = AudioAnalyzer()
        self.stream = None
        try:
            self.stream = sounddevice.InputStream(
                device=device,
                channels=1,
                samplerate=sample_rate,
                blocksize=block_size,
                callback=self._callback,
            )
            self.stream.start()
        except Exception as exc:
            self.close()
            raise RuntimeError(_audio_open_message(device, exc)) from exc

    def poll(self, now: float) -> MusicFrame | None:
        with self.lock:
            if not self.samples:
                return None
            samples = list(self.samples)
            self.samples.clear()
        if not samples:
            return None
        return self.analyzer.read(samples, self.sample_rate)

    def close(self) -> None:
        stream = self.stream
        if stream is None:
            return
        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass
        self.stream = None

    def _callback(self, indata, _frames, _time, _status) -> None:
        with self.lock:
            for frame in indata:
                self.samples.append(float(frame[0]))


def audio_device_lines() -> list[str]:
    return _audio_device_lines("input")


def audio_output_lines() -> list[str]:
    return _audio_device_lines("output")


def _audio_stack():
    try:
        import numpy
        import sounddevice
    except ImportError as exc:
        raise RuntimeError(INSTALL_AUDIO_MESSAGE) from exc
    return sounddevice


def _audio_device_lines(kind: str) -> list[str]:
    sounddevice = _audio_stack()
    devices = sounddevice.query_devices()
    lines: list[str] = []
    channel_key = "max_input_channels" if kind == "input" else "max_output_channels"
    suffix = "in" if kind == "input" else "out"
    for index, device in enumerate(devices):
        channels = int(device.get(channel_key, 0))
        if channels <= 0:
            continue
        name = str(device.get("name", "unknown"))
        rate = round(float(device.get("default_samplerate", 0.0)))
        lines.append(f"{index}: {name} ({channels} {suffix}, {rate} Hz)")
    return lines


def _audio_open_message(device: str | int | None, error: Exception) -> str:
    name = "default input" if device is None else f"input {device}"
    detail = str(error).strip()
    if detail:
        return f"Could not open {name}: {detail}. Run `vjctl --list-audio-devices`."
    return f"Could not open {name}. Run `vjctl --list-audio-devices`."
