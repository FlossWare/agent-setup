"""Capture the real curses TUI and render its PTY screen as an SVG artifact."""
from __future__ import annotations

import html
import os
from pathlib import Path

import pexpect
import pyte

COLS, ROWS = 120, 36
CELL_W, CELL_H = 9, 18
OUT = Path("artifacts/live-tui.svg")


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"TERM": "xterm-256color", "COLUMNS": str(COLS), "LINES": str(ROWS)})
    state = env.get("FLOSSWARE_SETUP_STATE_DIR")
    if state:
        Path(state).mkdir(parents=True, exist_ok=True)

    screen = pyte.Screen(COLS, ROWS)
    stream = pyte.Stream(screen)
    child = pexpect.spawn("flossware-setup", ["--theme", "turbo"], env=env, dimensions=(ROWS, COLS), encoding=None)
    try:
        # Give curses enough time to paint the initial screen, then use the
        # documented Q exit path.  The screen buffer remains our evidence.
        child.delaybeforesend = 0.1
        child.expect(pexpect.TIMEOUT, timeout=2)
        stream.feed(child.before.decode("utf-8", "replace"))
        child.send(b"q")
        child.expect(pexpect.EOF, timeout=5)
        stream.feed(child.before.decode("utf-8", "replace"))
    finally:
        if child.isalive():
            child.terminate(force=True)

    lines = ["".join(row) for row in screen.display]
    text = "\n".join(lines)
    if "Profiles" not in text or "Configuration" not in text or "READY" not in text:
        raise SystemExit("Live TUI capture did not contain expected main-screen markers")

    bg = "#000000"
    fg = "#FFFFFF"
    width, height = COLS * CELL_W, ROWS * CELL_H
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{bg}"/>',
        '<g font-family="DejaVu Sans Mono, monospace" font-size="14" xml:space="preserve">',
    ]
    for y, line in enumerate(lines):
        parts.append(f'<text x="0" y="{(y + 1) * CELL_H - 3}" fill="{fg}">{html.escape(line)}</text>')
    parts.extend(["</g>", "</svg>"])
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Captured live TUI: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
