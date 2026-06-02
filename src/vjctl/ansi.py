from __future__ import annotations

from .buffer import Cell

RESET = "\x1b[0m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
ALT_SCREEN = "\x1b[?1049h"
MAIN_SCREEN = "\x1b[?1049l"
CLEAR = "\x1b[2J\x1b[H"


def row_to_ansi(row: list[Cell]) -> str:
    parts: list[str] = []
    fg: tuple[int, int, int] | None = None
    bg: tuple[int, int, int] | None = None
    bold = False
    dim = False
    for cell in row:
        if cell.fg != fg or cell.bg != bg or cell.bold != bold or cell.dim != dim:
            attrs = []
            if cell.bold:
                attrs.append("1")
            elif cell.dim:
                attrs.append("2")
            else:
                attrs.append("22")
            attrs.append(f"38;2;{cell.fg[0]};{cell.fg[1]};{cell.fg[2]}")
            if cell.bg is None:
                attrs.append("49")
            else:
                attrs.append(f"48;2;{cell.bg[0]};{cell.bg[1]};{cell.bg[2]}")
            parts.append("\x1b[" + ";".join(attrs) + "m")
            fg, bg, bold, dim = cell.fg, cell.bg, cell.bold, cell.dim
        parts.append(cell.char)
    return "".join(parts)
