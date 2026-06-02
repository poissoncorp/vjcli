from __future__ import annotations

from dataclasses import dataclass


Color = tuple[int, int, int]


@dataclass(frozen=True)
class Cell:
    char: str = " "
    fg: Color = (216, 222, 233)
    bg: Color | None = None
    bold: bool = False
    dim: bool = False


class FrameBuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self._blank = Cell()
        self._rows = [[self._blank for _ in range(self.width)] for _ in range(self.height)]

    def clear(self) -> None:
        for y in range(self.height):
            row = self._rows[y]
            for x in range(self.width):
                row[x] = self._blank

    def write_cell(
        self,
        x: int,
        y: int,
        char: str,
        *,
        fg: Color = (216, 222, 233),
        bg: Color | None = None,
        bold: bool = False,
        dim: bool = False,
    ) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self._rows[y][x] = Cell((char or " ")[0], fg, bg, bold, dim)

    def write_text(
        self,
        x: int,
        y: int,
        text: str,
        *,
        fg: Color = (216, 222, 233),
        bg: Color | None = None,
        bold: bool = False,
        dim: bool = False,
    ) -> None:
        if not (0 <= y < self.height):
            return
        for offset, char in enumerate(text):
            self.write_cell(x + offset, y, char, fg=fg, bg=bg, bold=bold, dim=dim)

    def row(self, y: int) -> list[Cell]:
        return self._rows[y]

    def row_text(self, y: int) -> str:
        return "".join(cell.char for cell in self._rows[y])
