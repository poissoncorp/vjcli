from __future__ import annotations

import argparse
import sys

from .app import render_preview, run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="vjctl", description="Terminal VJ control realm.")
    parser.add_argument("--preview-frames", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--width", type=int, default=132, help=argparse.SUPPRESS)
    parser.add_argument("--height", type=int, default=36, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.preview_frames > 0:
        sys.stdout.write(render_preview(args.preview_frames, args.width, args.height))
        return 0
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
