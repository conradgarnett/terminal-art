#!/usr/bin/env python3
"""
hat.py — the aperiodic monotile, in an endless Droste zoom.

Renders a tiling of "the hat" (Smith, Myers, Kaplan & Goodman-Strauss's
2023 aperiodic monotile — a single 13-sided shape that tiles the plane
but never repeats periodically) and falls into it forever: a seamless
infinite zoom with a slow rotation, like an Escher staircase for tiles.

The illusion: the tiling is drawn at two zoom levels one octave apart and
crossfaded. As the big octave grows too large and fades out, the small
one grows into the exact size the big one started at — so the loop never
shows a seam. A vivid plasma field flows across everything as it spins.

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
UNITS_ACROSS = 12.0           # world units across the width at the base zoom
FPS = 24
ZOOM_PERIOD = 2.5             # seconds to zoom out by one octave (2x)
ZOOM_DIR = -1                 # 1 = fall inward, -1 = pull outward
ROT_SPEED = 0.5               # steady rotation, radians/sec (0 = no spin)
TWIST = 0.9                   # log-spiral: twist per e-fold of radius (0 = off)
PALETTE_SPEED = 0.05          # how fast every tile's color drifts
SATURATION = 0.9              # color richness (0 = gray, 1 = neon)
GROUT = (0, 0, 0)             # color of the lines between tiles
BG = (8, 8, 12)               # color outside the tiling

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "hat_tiling.json")
BUCKET = 1.5                  # spatial-hash cell size (~ half a tile)

# 4x4 ordered-dither thresholds: composite the two zoom octaves as a clean
# stippled dissolve so each cell keeps a real tile's flat color (no muddy
# blending, no doubled outlines).
_B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
BAYER = [[(v + 0.5) / 16.0 for v in row] for row in _B4]
BAYER_MIN = 0.5 / 16.0        # below this, no cell picks the small octave
BAYER_MAX = 15.5 / 16.0       # above this, no cell picks the big octave


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
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        tiles.append({
            "pts": pts,
            "cx": sum(xs) / len(xs),
            "cy": sum(ys) / len(ys),
            "r": bool(t["r"]),
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
                        inside = False
                        j = 12
                        for i in range(13):
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
                    inside = False
                    j = 12
                    for i in range(13):
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

            s0 = W / UNITS_ACROSS
            z = (t / ZOOM_PERIOD) * ZOOM_DIR
            f = z - math.floor(z)          # 0..1 within the octave
            s_hi = s0 * (2.0 ** f)         # big octave, fades out
            s_lo = s0 * (2.0 ** (f - 1))   # small octave, fades in
            # dissolve weight pinned to 0/1 outside a mid-octave band, so most
            # frames only need to build one octave (see the skip below)
            if f <= 0.35:
                w_lo = 0.0
            elif f >= 0.65:
                w_lo = 1.0
            else:
                u = (f - 0.35) / 0.30
                w_lo = u * u * (3.0 - 2.0 * u)

            # only build an octave if the dither actually shows any of it
            idhi = ehi = idlo = elo = None
            grds = []
            if w_lo <= BAYER_MAX:
                chi = -theta + TWIST * math.log(s_hi)
                idhi = id_grid(PX, PY, math.cos(chi), math.sin(chi),
                               1.0 / s_hi, W, H)
                ehi = edges(idhi, W, H)
                grds.append(idhi)
            if w_lo > BAYER_MIN:
                clo = -theta + TWIST * math.log(s_lo)
                idlo = id_grid(PX, PY, math.cos(clo), math.sin(clo),
                               1.0 / s_lo, W, H)
                elo = edges(idlo, W, H)
                grds.append(idlo)

            # one fixed, distinct color per tile: golden-ratio hue spacing so
            # every hat clashes with its neighbors. Whole palette drifts slowly.
            colcache = {-1: BG}
            drift = t * PALETTE_SPEED
            for grd in grds:
                for row in grd:
                    for idx in row:
                        if idx not in colcache:
                            hue = (idx * 0.61803398875 + drift) % 1.0
                            val = 0.62 + 0.38 * ((idx * 0.7548776662) % 1.0)
                            colcache[idx] = hsv_to_rgb(hue, SATURATION, val)

            out = ["\033[H"]
            last = None
            for row in range(H):
                ih = idhi[row] if idhi else None
                il = idlo[row] if idlo else None
                eh = ehi[row] if ehi else None
                el = elo[row] if elo else None
                brow = BAYER[row & 3]
                for col in range(W):
                    # pick exactly one octave for this cell -> flat, pure color
                    if w_lo > brow[col & 3]:
                        idx = il[col]
                        ed = el[col]
                    else:
                        idx = ih[col]
                        ed = eh[col]
                    rgb = GROUT if ed else colcache[idx]
                    if rgb != last:
                        out.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")
                        last = rgb
                    out.append("█")
                out.append("\n")
                last = None
            out.append("\033[0m\033[38;2;120;120;120m"
                       "  the hat · infinite zoom · Ctrl-C to quit ")
            sys.stdout.write("".join(out))
            sys.stdout.flush()

            frame += 1
            time.sleep(1.0 / FPS)
    except (KeyboardInterrupt, BrokenPipeError):
        cleanup()


if __name__ == "__main__":
    main()
