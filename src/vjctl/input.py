from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputEvent:
    kind: str
    value: str = ""


ESCAPE_EVENTS = {
    b"\x1b[A": InputEvent("slider", "up"),
    b"\x1b[B": InputEvent("slider", "down"),
    b"\x1b[C": InputEvent("jog", "right"),
    b"\x1b[D": InputEvent("jog", "left"),
}


class InputDecoder:
    def __init__(self) -> None:
        self._buffer = b""
        self._esc_waiting = False

    def feed(self, data: bytes) -> list[InputEvent]:
        self._buffer += data
        events: list[InputEvent] = []
        while self._buffer:
            event = self._next_event()
            if event is None:
                break
            events.append(event)
        return events

    def flush_escape(self) -> list[InputEvent]:
        if self._buffer == b"\x1b":
            self._buffer = b""
            if self._esc_waiting:
                self._esc_waiting = False
                return [InputEvent("exit")]
            self._esc_waiting = True
            return []
        return []

    def _next_event(self) -> InputEvent | None:
        b0 = self._buffer[0]
        if b0 == 0x03:
            self._buffer = self._buffer[1:]
            return InputEvent("exit")
        if b0 in (0x7F, 0x08):
            self._buffer = self._buffer[1:]
            self._esc_waiting = False
            return InputEvent("backspace")
        if b0 in (0x0A, 0x0D):
            self._buffer = self._buffer[1:]
            self._esc_waiting = False
            return InputEvent("enter")
        if b0 == 0x09:
            self._buffer = self._buffer[1:]
            self._esc_waiting = False
            return InputEvent("tap")
        if b0 == 0x1B:
            return self._escape_event()
        if b0 < 0x20:
            self._buffer = self._buffer[1:]
            return InputEvent("ignore")

        try:
            text = self._buffer.decode("utf-8")
        except UnicodeDecodeError as exc:
            if exc.reason == "unexpected end of data":
                return None
            self._buffer = self._buffer[1:]
            return InputEvent("ignore")
        char = text[0]
        self._buffer = text[1:].encode("utf-8")
        self._esc_waiting = False
        return InputEvent("char", char)

    def _escape_event(self) -> InputEvent | None:
        for sequence, event in ESCAPE_EVENTS.items():
            if self._buffer.startswith(sequence):
                self._buffer = self._buffer[len(sequence):]
                self._esc_waiting = False
                return event
        if any(sequence.startswith(self._buffer) for sequence in ESCAPE_EVENTS):
            return None
        if self._buffer == b"\x1b":
            return None
        self._buffer = self._buffer[1:]
        if self._esc_waiting:
            self._esc_waiting = False
            return InputEvent("exit")
        self._esc_waiting = True
        return InputEvent("ignore")
