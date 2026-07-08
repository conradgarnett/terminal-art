#!/usr/bin/env python3
"""
hat.py — a slow color-field painting on the aperiodic monotile.

A composition built on a tiling of "the hat" (Smith, Myers, Kaplan &
Goodman-Strauss's 2023 aperiodic monotile — a single 13-sided shape that
tiles the plane but never repeats). The geometry holds still, like a
print; only the color moves. A curated flat palette drifts across the
tiling in slow bands — warm paper as negative space, a few bold accents,
the occasional near-black shape for weight. Think Matisse cut-outs by way
of Bauhaus, rendered in a terminal.

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

# ---- composition -----------------------------------------------------------
UNITS_ACROSS = 22.0           # world units across the width (lower = bigger shapes)
FPS = 20
SPEED = 1.0                   # overall tempo of the color drift
PAPER_LEVEL = 0.50            # fraction of the field left as bare paper
INK_LEVEL = 0.86             # above this a shape goes near-black for weight

PAPER = (234, 228, 214)       # warm off-white ground
INK = (38, 35, 42)           # near-black
GROUT = (196, 189, 173)       # quiet line between tiles (a shade under paper)
ACCENTS = [                   # Bauhaus primaries
    (211, 83, 61),            # vermilion red
    (233, 171, 76),           # ochre yellow
    (58, 74, 122),            # indigo blue
]
NACC = len(ACCENTS)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "hat_tiling.json")


def load_tiles():
    with open(DATA_FILE) as fh:
        data = json.load(fh)
    tiles = []
    for t in data["tiles"]:
        pts = [(float(x), float(y)) for x, y in t["p"]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        tiles.append({
            "pts": pts,
            "cx": sum(xs) / len(xs),
            "cy": sum(ys) / len(ys),
        })
    return tiles


def point_in_poly(px, py, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def build_map(tiles, W, H):
    """Assign each cell to a tile, once. Returns (cellmap, edge)."""
    wcx = sum(t["cx"] for t in tiles) / len(tiles)
    wcy = sum(t["cy"] for t in tiles) / len(tiles)
    sx = W / UNITS_ACROSS
    sy = sx * 0.5  # undistort ~2:1 character cells

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

    # single-width line where a cell's right/down neighbour is another tile
    edge = [[False] * W for _ in range(H)]
    for row in range(H):
        cr = cellmap[row]
        nr = cellmap[row + 1] if row + 1 < H else None
        er = edge[row]
        for col in range(W):
            me = cr[col]
            if me == -1:
                continue
            if (col + 1 < W and cr[col + 1] != me) or \
               (nr is not None and nr[col] != me):
                er[col] = True
    return cellmap, edge


def tile_color(cx, cy, t):
    """Two fields at different scales: a broad one carves paper/ink/colour,
    a finer one scatters which accent so colours alternate in blocks."""
    a = (math.sin(cx * 0.17 + t * 0.045)
         + math.sin(cy * 0.20 - t * 0.033)
         + math.sin((cx * 0.6 + cy) * 0.12 + t * 0.040))
    v = (a + 3.0) / 6.0
    if v < PAPER_LEVEL:
        return PAPER
    if v > INK_LEVEL:
        return INK
    b = (math.sin(cx * 0.33 - t * 0.030 + 1.3)
         + math.sin(cy * 0.38 + t * 0.041 + 2.1)
         + math.sin((cx - cy * 0.7) * 0.29 - t * 0.035))
    c = (b + 3.0) / 6.0
    return ACCENTS[int(c * NACC * 2.0) % NACC]  # *2 breaks spectral order


def main():
    tiles = load_tiles()
    sys.stdout.write("\033[?25l\033[?1049h")

    def cleanup(*_):
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    size = None
    cellmap = edge = None
    frame = 0
    try:
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            H = rows - 1
            W = cols
            if (W, H) != size:
                size = (W, H)
                cellmap, edge = build_map(tiles, W, H)
            t = frame * (SPEED / FPS)

            colc = {-1: PAPER}
            out = ["\033[H"]
            last = None
            for row in range(H):
                cr = cellmap[row]
                er = edge[row]
                for col in range(W):
                    idx = cr[col]
                    if er[col]:
                        rgb = GROUT
                    else:
                        rgb = colc.get(idx)
                        if rgb is None:
                            tl = tiles[idx]
                            rgb = tile_color(tl["cx"], tl["cy"], t)
                            colc[idx] = rgb
                    if rgb != last:
                        out.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")
                        last = rgb
                    out.append("█")
                out.append("\n")
                last = None
            out.append(f"\033[38;2;{GROUT[0]};{GROUT[1]};{GROUT[2]}m"
                       "  the hat · Ctrl-C to quit ")
            sys.stdout.write("".join(out))
            sys.stdout.flush()

            frame += 1
            time.sleep(1.0 / FPS)
    except (KeyboardInterrupt, BrokenPipeError):
        cleanup()


if __name__ == "__main__":
    main()
