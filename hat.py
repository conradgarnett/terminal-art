#!/usr/bin/env python3
"""
hat.py — the aperiodic monotile, alive in your terminal.

Renders a tiling of "the hat" (Smith, Myers, Kaplan & Goodman-Strauss's
2023 aperiodic monotile — a single 13-sided shape that tiles the plane
but never repeats periodically). A vivid plasma field flows across the
tiles like light through stained glass, and the reflected "anti-hats"
(the ~1-in-7 mirror-image tiles the tiling can't avoid) glow as accents.

The tiling geometry lives in hat_tiling.json (baked offline from Craig
Kaplan's substitution system) so this renderer is pure standard library.

Run:   python3 hat.py
Quit:  Ctrl-C
"""

import json
import math
import os
import shutil
import signal
import sys
import time

# ---- knobs -----------------------------------------------------------------
UNITS_ACROSS = 18.0           # world units shown across the width (lower = zoom in)
FPS = 24
PALETTE_SPEED = 0.06          # how fast the colors cycle
FLOW_SPEED = 0.6             # how fast the plasma flows across the tiling
SATURATION = 0.85             # color richness (0 = gray, 1 = neon)
GROUT = (24, 24, 30)          # color of the lines between tiles

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "hat_tiling.json")


def hsv_to_rgb(h, s, v):
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


def load_tiles():
    with open(DATA_FILE) as fh:
        data = json.load(fh)
    tiles = []
    for t in data["tiles"]:
        pts = [(float(x), float(y)) for x, y in t["p"]]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        tiles.append({"pts": pts, "cx": cx, "cy": cy, "r": bool(t["r"])})
    return tiles


def point_in_poly(px, py, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def build_map(tiles, W, H):
    """Assign each terminal cell to a tile. Returns (cellmap, edge, wcx, wcy)."""
    wcx = sum(t["cx"] for t in tiles) / len(tiles)
    wcy = sum(t["cy"] for t in tiles) / len(tiles)
    sx = W / UNITS_ACROSS
    sy = sx * 0.5  # terminal cells are ~2x taller than wide -> undistort

    def to_screen(x, y):
        return ((x - wcx) * sx + W / 2.0, H / 2.0 - (y - wcy) * sy)

    cellmap = [[-1] * W for _ in range(H)]
    for idx, t in enumerate(tiles):
        spts = [to_screen(x, y) for x, y in t["pts"]]
        xs = [p[0] for p in spts]
        ys = [p[1] for p in spts]
        minx = max(0, int(math.floor(min(xs))))
        maxx = min(W - 1, int(math.ceil(max(xs))))
        miny = max(0, int(math.floor(min(ys))))
        maxy = min(H - 1, int(math.ceil(max(ys))))
        if minx > maxx or miny > maxy:
            continue
        for row in range(miny, maxy + 1):
            py = row + 0.5
            crow = cellmap[row]
            for col in range(minx, maxx + 1):
                if crow[col] == -1 and point_in_poly(col + 0.5, py, spts):
                    crow[col] = idx

    # edge = a cell whose right or down neighbor sits in a different tile.
    # Only two directions -> single-width grout lines instead of double.
    edge = [[False] * W for _ in range(H)]
    for row in range(H):
        for col in range(W):
            me = cellmap[row][col]
            if me == -1:
                continue
            for dr, dc in ((0, 1), (1, 0)):
                r2, c2 = row + dr, col + dc
                if (0 <= r2 < H and 0 <= c2 < W and cellmap[r2][c2] != me
                        and cellmap[r2][c2] != -1):
                    edge[row][col] = True
                    break
    return cellmap, edge, wcx, wcy


def plasma(x, y, t):
    v = (math.sin(x * 0.35 + t * FLOW_SPEED)
         + math.sin(y * 0.30 - t * FLOW_SPEED * 0.8)
         + math.sin((x + y) * 0.22 + t * FLOW_SPEED * 1.1)
         + math.sin(math.hypot(x, y) * 0.30 - t * FLOW_SPEED))
    return (v + 4.0) / 8.0  # -> 0..1


def main():
    tiles = load_tiles()
    sys.stdout.write("\033[?25l\033[?1049h")

    def cleanup(*_):
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    grout_sgr = f"\033[38;2;{GROUT[0]};{GROUT[1]};{GROUT[2]}m"
    size = None
    cellmap = edge = None
    frame = 0
    try:
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            H = rows - 1
            if (cols, rows) != size:
                size = (cols, rows)
                cellmap, edge, _, _ = build_map(tiles, cols, H)
            t = frame * (1.0 / FPS)

            # one flat color per tile this frame -> flowing stained glass
            tint = {}
            for row in range(H):
                for idx in cellmap[row]:
                    if idx != -1 and idx not in tint:
                        tl = tiles[idx]
                        v = plasma(tl["cx"], tl["cy"], t)
                        if tl["r"]:  # reflected anti-hat -> contrasting glow
                            hue = (v * 0.6 + t * PALETTE_SPEED + 0.5) % 1.0
                            rgb = hsv_to_rgb(hue, SATURATION,
                                             0.55 + 0.45 * v)
                        else:
                            hue = (v * 0.6 + t * PALETTE_SPEED) % 1.0
                            rgb = hsv_to_rgb(hue, SATURATION,
                                             0.30 + 0.60 * v)
                        tint[idx] = rgb

            out = ["\033[H"]
            last = None
            for row in range(H):
                crow = cellmap[row]
                erow = edge[row]
                for col in range(cols):
                    idx = crow[col]
                    if idx == -1:
                        if last is not None:
                            out.append("\033[0m")
                            last = None
                        out.append(" ")
                        continue
                    rgb = GROUT if erow[col] else tint[idx]
                    if rgb != last:
                        out.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")
                        last = rgb
                    out.append("█")
                out.append("\033[0m\n")
                last = None

            out.append(grout_sgr + "  the hat · aperiodic monotile · "
                       "Ctrl-C to quit ")
            sys.stdout.write("".join(out))
            sys.stdout.flush()

            frame += 1
            time.sleep(1.0 / FPS)
    except (KeyboardInterrupt, BrokenPipeError):
        cleanup()


if __name__ == "__main__":
    main()
