from __future__ import annotations

from functools import cache
from pathlib import Path


FONT_MEDIUM = {
    "A": ("  ###  ", " ## ## ", "##   ##", "#######", "##   ##", "##   ##", "##   ##"),
    "B": ("###### ", "##   ##", "##   ##", "###### ", "##   ##", "##   ##", "###### "),
    "C": (" ##### ", "##   ##", "##     ", "##     ", "##     ", "##   ##", " ##### "),
    "D": ("###### ", "##   ##", "##   ##", "##   ##", "##   ##", "##   ##", "###### "),
    "E": ("#######", "##     ", "##     ", "###### ", "##     ", "##     ", "#######"),
    "F": ("#######", "##     ", "##     ", "###### ", "##     ", "##     ", "##     "),
    "G": (" ##### ", "##   ##", "##     ", "## ####", "##   ##", "##   ##", " ##### "),
    "H": ("##   ##", "##   ##", "##   ##", "#######", "##   ##", "##   ##", "##   ##"),
    "I": ("#######", "  ###  ", "  ###  ", "  ###  ", "  ###  ", "  ###  ", "#######"),
    "J": ("#######", "    ## ", "    ## ", "    ## ", "##  ## ", "##  ## ", " ####  "),
    "K": ("##   ##", "##  ## ", "## ##  ", "####   ", "## ##  ", "##  ## ", "##   ##"),
    "L": ("##     ", "##     ", "##     ", "##     ", "##     ", "##     ", "#######"),
    "M": ("##   ##", "### ###", "#######", "## # ##", "##   ##", "##   ##", "##   ##"),
    "N": ("##   ##", "###  ##", "#### ##", "## ####", "##  ###", "##   ##", "##   ##"),
    "O": (" ##### ", "##   ##", "##   ##", "##   ##", "##   ##", "##   ##", " ##### "),
    "P": ("###### ", "##   ##", "##   ##", "###### ", "##     ", "##     ", "##     "),
    "Q": (" ##### ", "##   ##", "##   ##", "##   ##", "## # ##", "##  ## ", " #### #"),
    "R": ("###### ", "##   ##", "##   ##", "###### ", "## ##  ", "##  ## ", "##   ##"),
    "S": (" ######", "##     ", "##     ", " ##### ", "     ##", "     ##", "###### "),
    "T": ("#######", "  ###  ", "  ###  ", "  ###  ", "  ###  ", "  ###  ", "  ###  "),
    "U": ("##   ##", "##   ##", "##   ##", "##   ##", "##   ##", "##   ##", " ##### "),
    "V": ("##   ##", "##   ##", "##   ##", "##   ##", " ## ## ", " ## ## ", "  ###  "),
    "W": ("##   ##", "##   ##", "##   ##", "## # ##", "#######", "### ###", "##   ##"),
    "X": ("##   ##", "##   ##", " ## ## ", "  ###  ", " ## ## ", "##   ##", "##   ##"),
    "Y": ("##   ##", "##   ##", " ## ## ", "  ###  ", "  ###  ", "  ###  ", "  ###  "),
    "Z": ("#######", "    ## ", "   ##  ", "  ###  ", " ##    ", "##     ", "#######"),
    "0": (" ##### ", "##   ##", "##  ###", "## # ##", "###  ##", "##   ##", " ##### "),
    "1": ("  ##   ", " ###   ", "####   ", "  ##   ", "  ##   ", "  ##   ", "###### "),
    "2": (" ##### ", "##   ##", "     ##", "   ### ", "  ##   ", " ##    ", "#######"),
    "3": ("###### ", "     ##", "     ##", " ##### ", "     ##", "     ##", "###### "),
    "4": ("##   ##", "##   ##", "##   ##", "#######", "     ##", "     ##", "     ##"),
    "5": ("#######", "##     ", "##     ", "###### ", "     ##", "     ##", "###### "),
    "6": (" ##### ", "##     ", "##     ", "###### ", "##   ##", "##   ##", " ##### "),
    "7": ("#######", "    ## ", "   ##  ", "  ##   ", " ##    ", " ##    ", " ##    "),
    "8": (" ##### ", "##   ##", "##   ##", " ##### ", "##   ##", "##   ##", " ##### "),
    "9": (" ##### ", "##   ##", "##   ##", " ######", "     ##", "     ##", " ##### "),
    " ": ("   ", "   ", "   ", "   ", "   ", "   ", "   "),
    ".": ("   ", "   ", "   ", "   ", "   ", "   ", "## "),
    ",": ("   ", "   ", "   ", "   ", "   ", "## ", "## "),
    "!": ("## ", "## ", "## ", "## ", "## ", "   ", "## "),
    "?": ("####  ", "   ## ", "   ## ", " ###  ", " ##   ", "      ", " ##   "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "_": ("       ", "       ", "       ", "       ", "       ", "       ", "#######"),
    "=": ("       ", "#######", "       ", "#######", "       ", "       ", "       "),
    "+": ("       ", "  ##   ", "  ##   ", "###### ", "  ##   ", "  ##   ", "       "),
    "/": ("    ##", "   ## ", "   ## ", "  ##  ", " ##   ", " ##   ", "##    "),
    "<": ("    ##", "  ### ", " ###  ", "##    ", " ###  ", "  ### ", "    ##"),
    ">": ("##    ", " ###  ", "  ### ", "    ##", "  ### ", " ###  ", "##    "),
    "(": ("  ### ", " ##   ", "##    ", "##    ", "##    ", " ##   ", "  ### "),
    ")": ("###   ", "  ##  ", "   ## ", "   ## ", "   ## ", "  ##  ", "###   "),
    "[": ("##### ", "##    ", "##    ", "##    ", "##    ", "##    ", "##### "),
    "]": ("##### ", "   ## ", "   ## ", "   ## ", "   ## ", "   ## ", "##### "),
    ":": ("   ", "## ", "## ", "   ", "## ", "## ", "   "),
    "'": ("## ", "## ", "   ", "   ", "   ", "   ", "   "),
}

def choose_art(text: str, width: int, height: int) -> list[str]:
    text = normalize(text)
    for figlet in _figlet_fonts():
        lines = _line(text, figlet)
        if _font_can_render(text, figlet, True) and _fits(lines, width, height):
            return lines
        wrapped = _wrapped(text, width, height, figlet, True)
        if wrapped:
            return wrapped
    for font in (FONT_XL, FONT_LARGE, FONT_MEDIUM, FONT_SMALL):
        if not _font_can_render(text, font, False):
            continue
        lines = _line(text, font)
        if lines and _fits(lines, width, height):
            return lines
    return _wrapped(text, width, height, FONT_SMALL, False)


def choose_compact_art(text: str, width: int, height: int) -> list[str]:
    text = normalize(text)
    for font in _figlet_fonts():
        if not _font_can_render(text, font, True):
            continue
        lines = _compact(_line(text, font), width, height)
        if lines:
            return lines
    return choose_art(text, width, height)


def normalize(text: str) -> str:
    return "".join(_normalize_char(char) for char in text.upper())


def _line(text: str, font: dict[str, tuple[str, ...]]) -> list[str]:
    rows = [""] * len(next(iter(font.values())))
    gap = _font_gap(font)
    for char in text:
        glyph = _glyph(font, char)
        for index, row in enumerate(glyph):
            rows[index] += row + " " * gap
    return _trim(rows)


def _font_can_render(text: str, font: dict[str, tuple[str, ...]], exact: bool) -> bool:
    for char in text:
        if char == " ":
            continue
        glyph = font.get(char)
        if glyph is not None and not _blank(glyph):
            continue
        if exact:
            return False
        fallback = font.get("?")
        if fallback is None or _blank(fallback):
            return False
    return True


def _glyph(font: dict[str, tuple[str, ...]], char: str) -> tuple[str, ...]:
    glyph = font.get(char)
    if glyph is not None and not _blank(glyph):
        return glyph
    return font.get("?", font[" "])


def _blank(glyph: tuple[str, ...]) -> bool:
    return not any(row.strip() for row in glyph)


@cache
def _figlet_fonts() -> tuple[dict[str, tuple[str, ...]], ...]:
    root = Path(__file__).with_name("fonts")
    delta = _try_read_figlet(root / "Delta_Corps_Priest_1.flf")
    doom = _try_read_figlet(root / "Doom.flf")
    fonts = []
    if delta and doom:
        fonts.append(_merged_font(delta, doom))
    if delta:
        fonts.append(delta)
    if doom:
        fonts.append(doom)
    return tuple(fonts)


def _try_read_figlet(path: Path) -> dict[str, tuple[str, ...]] | None:
    try:
        return _read_figlet(path)
    except OSError:
        return None


def _merged_font(
    primary: dict[str, tuple[str, ...]],
    fallback: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    height = len(next(iter(primary.values())))
    font: dict[str, tuple[str, ...]] = {}
    for codepoint in range(32, 127):
        char = chr(codepoint)
        glyph = primary.get(char)
        if glyph is not None and not _blank(glyph):
            font[char] = glyph
            continue
        fallback_glyph = fallback.get(char)
        if fallback_glyph is not None and not _blank(fallback_glyph):
            font[char] = _adjust_height(fallback_glyph, height)
            continue
        font[char] = _adjust_height(primary.get(" ", ("",) * height), height)
    return font


def _adjust_height(rows: tuple[str, ...], height: int) -> tuple[str, ...]:
    if len(rows) == height:
        return rows
    if len(rows) > height:
        top = (len(rows) - height) // 2
        return rows[top:top + height]
    top = (height - len(rows)) // 2
    bottom = height - len(rows) - top
    blank = " " * max((len(row) for row in rows), default=0)
    return (blank,) * top + rows + (blank,) * bottom


def _read_figlet(path: Path) -> dict[str, tuple[str, ...]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split()
    hardblank = header[0][-1]
    height = int(header[1])
    comments = int(header[5])
    rows = lines[1 + comments:]
    font: dict[str, tuple[str, ...]] = {}
    index = 0
    for codepoint in range(32, 127):
        glyph = rows[index:index + height]
        if len(glyph) == height:
            font[chr(codepoint)] = tuple(_figlet_row(row, hardblank) for row in glyph)
        index += height
    return font


def _figlet_row(row: str, hardblank: str) -> str:
    if not row:
        return ""
    endmark = row[-1]
    while row.endswith(endmark):
        row = row[:-1]
    return row.replace(hardblank, " ")


def _font_gap(font: dict[str, tuple[str, ...]]) -> int:
    height = len(next(iter(font.values())))
    if height >= 20:
        return 3
    if height >= 12:
        return 2
    return 1


def _wrapped(text: str, width: int, height: int, font: dict[str, tuple[str, ...]], exact: bool) -> list[str]:
    blocks: list[list[str]] = []
    line = ""
    for word in text.split():
        if not _font_can_render(word, font, exact):
            return []
        candidate = word if not line else f"{line} {word}"
        if _fits(_line(candidate, font), width, height):
            line = candidate
        else:
            if not line:
                return []
            if line:
                blocks.append(_line(line, font))
            line = word
    if line:
        blocks.append(_line(line, font))

    lines: list[str] = []
    for block in blocks:
        if lines:
            lines.append("")
        lines.extend(block)
    return lines if _fits(lines, width, height) else []


def _fits(lines: list[str], width: int, height: int) -> bool:
    return bool(lines) and len(lines) <= height and all(len(line) <= width for line in lines)


def _compact(lines: list[str], width: int, height: int) -> list[str]:
    if not lines or height <= 0 or width <= 0:
        return []
    target_height = min(height, 5, len(lines))
    y_step = max(1, (len(lines) - 1) / max(1, target_height - 1))
    sampled = [lines[round(index * y_step)] for index in range(target_height)]
    for x_step in range(2, 8):
        output = [_compact_row(row, x_step) for row in sampled]
        output = _trim(output)
        if _fits(output, width, height):
            return output
    return []


def _compact_row(row: str, x_step: int) -> str:
    output = []
    for index in range(0, len(row), x_step):
        chunk = row[index:index + x_step]
        ink = sum(1 for char in chunk if char != " ")
        if ink == 0:
            output.append(" ")
        elif ink == len(chunk):
            output.append("█")
        else:
            output.append("▓" if ink > len(chunk) / 2 else "▒")
    return "".join(output).rstrip()


def _trim(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    width = max((len(line.rstrip()) for line in lines), default=0)
    return [line[:width].rstrip() for line in lines]


def _small(rows: tuple[str, ...]) -> tuple[str, ...]:
    sample_y = (0, 1, 3, 5, 6)
    sample_x = (0, len(rows[0]) // 2, len(rows[0]) - 1)
    return tuple("".join("#" if rows[y][x] != " " else " " for x in sample_x if x < len(rows[y])) for y in sample_y)


def _large(rows: tuple[str, ...]) -> tuple[str, ...]:
    return _scale(rows, 3, 1)


def _xl(rows: tuple[str, ...]) -> tuple[str, ...]:
    return _scale(rows, 4, 2)


def _scale(rows: tuple[str, ...], x_scale: int, y_scale: int) -> tuple[str, ...]:
    output: list[str] = []
    for row in rows:
        expanded = "".join("#" * x_scale if char != " " else " " * x_scale for char in row)
        output.extend(expanded for _ in range(y_scale))
    return tuple(output)


def _normalize_char(char: str) -> str:
    replacements = {
        "Ą": "A",
        "Ć": "C",
        "Ę": "E",
        "Ł": "L",
        "Ń": "N",
        "Ó": "O",
        "Ś": "S",
        "Ż": "Z",
        "Ź": "Z",
    }
    char = replacements.get(char, char)
    return char if 32 <= ord(char) <= 126 else " "


FONT_SMALL = {key: _small(value) for key, value in FONT_MEDIUM.items()}
FONT_LARGE = {key: _large(value) for key, value in FONT_MEDIUM.items()}
FONT_XL = {key: _xl(value) for key, value in FONT_MEDIUM.items()}
