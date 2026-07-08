#!/usr/bin/env python3
"""
plasma.py — a living, breathing terminal art piece.

A morphing truecolor plasma field with drifting flow lines. Pure standard
library, no dependencies. Adapts to your terminal size in real time.

Run:   python3 plasma.py
Quit:  Ctrl-C
"""

import math
import os
import shutil
import signal
import sys
import time

# ---- rendering knobs -------------------------------------------------------
CHARS = " .:-=+*#%@"          # low -> high intensity ramp
FPS = 30
PALETTE_SPEED = 0.15          # how fast the colors cycle
FLOW_SPEED = 0.9             # how fast the plasma churns


def hsv_to_rgb(h, s, v):
    """h,s,v in [0,1] -> (r,g,b) in 0..255."""
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6
    r, g, b = [
        (v, t, p), (q, v, p), (p, v, t),
        (p, q, v), (t, p, v), (v, p, q),
    ][i]
    return int(r * 255), int(g * 255), int(b * 255)


def main():
    # hide cursor, save screen
    sys.stdout.write("\033[?25l\033[?1049h")

    def cleanup(*_):
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    frame = 0
    try:
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            rows -= 1  # leave a status line
            t = frame * (1.0 / FPS)

            out = ["\033[H"]  # cursor home
            aspect = 0.5      # chars are ~2x taller than wide
            for y in range(rows):
                ny = (y / rows - 0.5) * 2.0
                for x in range(cols):
                    nx = (x / cols - 0.5) * 2.0
                    # layered sine field -> classic plasma
                    v = (
                        math.sin(nx * 3.0 + t * FLOW_SPEED)
                        + math.sin((ny + nx) * 2.5 - t * FLOW_SPEED * 0.7)
                        + math.sin(math.hypot(nx, ny * aspect * 2) * 5.0
                                   - t * FLOW_SPEED * 1.3)
                        + math.sin((nx * math.sin(t * 0.3)
                                    + ny * math.cos(t * 0.3)) * 4.0)
                    )
                    v = (v + 4.0) / 8.0            # -> 0..1
                    ch = CHARS[min(len(CHARS) - 1,
                                   int(v * (len(CHARS) - 1) + 0.5))]
                    hue = (v * 0.6 + t * PALETTE_SPEED) % 1.0
                    r, g, b = hsv_to_rgb(hue, 0.85, 0.35 + 0.65 * v)
                    out.append(f"\033[38;2;{r};{g};{b}m{ch}")
                out.append("\n")

            out.append("\033[0m\033[38;2;120;120;120m"
                       "  plasma · Ctrl-C to quit ")
            sys.stdout.write("".join(out))
            sys.stdout.flush()

            frame += 1
            time.sleep(1.0 / FPS)
    except (KeyboardInterrupt, BrokenPipeError):
        cleanup()


if __name__ == "__main__":
    main()
