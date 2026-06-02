from __future__ import annotations

from collections import deque
from threading import Lock

from .analyzer import AudioAnalyzer
from .music import MusicFrame


class AudioInputSource:
    def __init__(
        self,
        device: str | int | None = None,
        sample_rate: int = 16_000,
        block_size: int = 512,
    ) -> None:
        try:
            import sounddevice
        except ImportError as exc:
            message = "Install audio support with `python3 -m pip install -e .[audio]`."
            raise RuntimeError(message) from exc
        self.sample_rate = sample_rate
        self.samples: deque[float] = deque(maxlen=sample_rate)
        self.lock = Lock()
        self.analyzer = AudioAnalyzer()
        self.stream = sounddevice.InputStream(
            device=device,
            channels=1,
            samplerate=sample_rate,
            blocksize=block_size,
            callback=self._callback,
        )
        self.stream.start()

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
        self.stream.stop()
        self.stream.close()

    def _callback(self, indata, _frames, _time, _status) -> None:
        with self.lock:
            for frame in indata:
                self.samples.append(float(frame[0]))
