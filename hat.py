#!/usr/bin/env python3
"""
hat.py — the aperiodic monotile, slowly spinning.

Renders a tiling of "the spectre" (Smith, Myers, Kaplan & Goodman-
Strauss's 2023 aperiodic monotile — a single 14-sided shape that tiles
the plane, never repeats, and needs no reflections, unlike its sibling
"the hat") and turns it slowly in place like a colored-glass wheel. Every
tile keeps its own distinct color; the whole palette drifts as it spins.

The tiling geometry lives in spectre_tiling.json (baked offline from
Craig Kaplan's substitution system) so this renderer is pure stdlib.

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
UNITS_ACROSS = 20.0           # world units across the width (lower = bigger tiles)
FPS = 24
ROT_SPEED = 0.4               # spin speed, radians/sec
TWIST = 0.0                   # log-spiral swirl on top of the spin (0 = rigid)
PALETTE_SPEED = 0.05          # how fast every tile's color drifts
SATURATION = 0.9              # color richness (0 = gray, 1 = neon)
GROUT = (0, 0, 0)             # color of the lines between tiles
BG = (8, 8, 12)               # color outside the tiling

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spectre_tiling.json")
BUCKET = 1.5                  # spatial-hash cell size (~ half a tile)


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
    raw = [[(float(x), float(y)) for x, y in t["p"]] for t in data["tiles"]]
    # recenter the whole patch on the origin, which is the spin center --
    # otherwise the view sits off to one edge and half the screen is empty
    minx = min(p[0] for pts in raw for p in pts)
    maxx = max(p[0] for pts in raw for p in pts)
    miny = min(p[1] for pts in raw for p in pts)
    maxy = max(p[1] for pts in raw for p in pts)
    ox, oy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    tiles = []
    for pts0 in raw:
        pts = [(x - ox, y - oy) for x, y in pts0]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        tiles.append({
            "pts": pts,
            "cx": sum(xs) / len(xs),
            "cy": sum(ys) / len(ys),
            "bb": (min(xs), max(xs), min(ys), max(ys)),
        })
    return tiles


def build_hash(tiles):
    grid = {}
    for idx, t in enumerate(tiles):
        x0, x1, y0, y1 = t["bb"]
        for gx in range(int(x0 // BUCKET), int(x1 // BUCKET) + 1):
            for gy in range(int(y0 // BUCKET), int(y1 // BUCKET) + 1):
                grid.setdefault((gx, gy), []).append(idx)
    return grid


def main():
    tiles = load_tiles()
    grid = build_hash(tiles)
    # parallel lists for the hot loop -- list indexing beats dict lookups
    BB = [t["bb"] for t in tiles]
    PTS = [t["pts"] for t in tiles]

    sys.stdout.write("\033[?25l\033[?1049h")

    def cleanup(*_):
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    def spiral_geometry(W, H):
        """Per-cell log-spiral constants, rebuilt only when the size changes.

        The world sample for a cell is  world = inv_scale * R(C) * (px, py),
        where (px, py) folds in the cell's radius and its log-spiral twist and
        depends only on the cell. That leaves the per-frame hot loop as plain
        multiply-adds with no trig at all.
        """
        cx, cy = W / 2.0, H / 2.0
        PX = [[0.0] * W for _ in range(H)]
        PY = [[0.0] * W for _ in range(H)]
        for row in range(H):
            dy = -2.0 * (row + 0.5 - cy)  # undistort ~2:1 character cells
            prx = PX[row]
            pry = PY[row]
            for col in range(W):
                dx = col + 0.5 - cx
                r = math.hypot(dx, dy)
                if r < 1e-9:
                    continue
                phi = math.atan2(dy, dx) - TWIST * math.log(r)
                prx[col] = r * math.cos(phi)
                pry[col] = r * math.sin(phi)
        return PX, PY

    def id_grid(PX, PY, cosC, sinC, inv_scale, W, H):
        """Which tile covers each cell, given the per-frame spiral rotation."""
        g = grid
        bb = BB
        pts_all = PTS
        b = BUCKET
        floor = math.floor
        out = [[-1] * W for _ in range(H)]
        for row in range(H):
            prx = PX[row]
            pry = PY[row]
            orow = out[row]
            prev = -1  # tile the previous cell landed in (spatial coherence)
            for col in range(W):
                px = prx[col]
                py = pry[col]
                x = (px * cosC - py * sinC) * inv_scale
                y = (px * sinC + py * cosC) * inv_scale

                # fast path: is this cell still inside the previous cell's tile?
                if prev != -1:
                    x0, x1, y0, y1 = bb[prev]
                    if x0 <= x <= x1 and y0 <= y <= y1:
                        pts = pts_all[prev]
                        n = len(pts)
                        inside = False
                        j = n - 1
                        for i in range(n):
                            xi, yi = pts[i]
                            xj, yj = pts[j]
                            if ((yi > y) != (yj > y)) and \
                               (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                                inside = not inside
                            j = i
                        if inside:
                            orow[col] = prev
                            continue

                bucket = g.get((int(floor(x / b)), int(floor(y / b))))
                if not bucket:
                    prev = -1
                    continue
                prev = -1
                for idx in bucket:
                    x0, x1, y0, y1 = bb[idx]
                    if x < x0 or x > x1 or y < y0 or y > y1:
                        continue
                    pts = pts_all[idx]
                    n = len(pts)
                    inside = False
                    j = n - 1
                    for i in range(n):
                        xi, yi = pts[i]
                        xj, yj = pts[j]
                        if ((yi > y) != (yj > y)) and \
                           (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                            inside = not inside
                        j = i
                    if inside:
                        orow[col] = idx
                        prev = idx
                        break
        return out

    def edges(idg, W, H):
        e = [[0] * W for _ in range(H)]
        for row in range(H):
            ir = idg[row]
            up = idg[row - 1] if row > 0 else None
            dn = idg[row + 1] if row + 1 < H else None
            er = e[row]
            for col in range(W):
                me = ir[col]
                if me == -1:
                    continue
                if (col + 1 < W and ir[col + 1] != me) or \
                   (col > 0 and ir[col - 1] != me) or \
                   (up is not None and up[col] != me) or \
                   (dn is not None and dn[col] != me):
                    er[col] = 1
        return e

    frame = 0
    size = None
    PX = PY = None
    try:
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            H = rows - 1
            W = cols
            if (W, H) != size:
                size = (W, H)
                PX, PY = spiral_geometry(W, H)
            t = frame * (1.0 / FPS)
            theta = ROT_SPEED * t

            # single fixed-scale layer: the tiling just spins in place
            s0 = W / UNITS_ACROSS
            C = -theta + TWIST * math.log(s0)
            idg = id_grid(PX, PY, math.cos(C), math.sin(C), 1.0 / s0, W, H)
            eg = edges(idg, W, H)

            # one fixed, distinct color per tile: golden-ratio hue spacing so
            # every tile clashes with its neighbors. Whole palette drifts slowly.
            colcache = {-1: BG}
            drift = t * PALETTE_SPEED
            for row in idg:
                for idx in row:
                    if idx not in colcache:
                        hue = (idx * 0.61803398875 + drift) % 1.0
                        val = 0.62 + 0.38 * ((idx * 0.7548776662) % 1.0)
                        colcache[idx] = hsv_to_rgb(hue, SATURATION, val)

            out = ["\033[H"]
            last = None
            for row in range(H):
                ig = idg[row]
                eb = eg[row]
                for col in range(W):
                    rgb = GROUT if eb[col] else colcache[ig[col]]
                    if rgb != last:
                        out.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")
                        last = rgb
                    out.append("█")
                out.append("\n")
                last = None
            out.append("\033[0m\033[38;2;120;120;120m"
                       "  the spectre · spinning · Ctrl-C to quit ")
            sys.stdout.write("".join(out))
            sys.stdout.flush()

            frame += 1
            time.sleep(1.0 / FPS)
    except (KeyboardInterrupt, BrokenPipeError):
        cleanup()


if __name__ == "__main__":
    main()
