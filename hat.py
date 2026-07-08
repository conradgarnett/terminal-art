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
BUCKET = 4.0                  # spatial-hash cell size (~ one tile wide)


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

    sys.stdout.write("\033[?25l\033[?1049h")

    def cleanup(*_):
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    def id_grid(scale, theta, W, H, cx, cy):
        """Which tile covers each cell, at a given scale + log-spiral twist."""
        sy = scale * 0.5  # undistort ~2:1 character cells
        g = grid
        tl = tiles
        b = BUCKET
        cos = math.cos
        sin = math.sin
        log = math.log
        hyp = math.hypot
        floor = math.floor
        out = [[-1] * W for _ in range(H)]
        for row in range(H):
            yr = -(row + 0.5 - cy) / sy
            orow = out[row]
            for col in range(W):
                xr = (col + 0.5 - cx) / scale
                # rotate by theta plus a twist that winds up toward the center
                r = hyp(xr, yr)
                ang = theta + TWIST * log(r if r > 1e-9 else 1e-9)
                ca = cos(ang)
                sa = sin(ang)
                x = xr * ca + yr * sa
                y = -xr * sa + yr * ca
                bucket = g.get((int(floor(x / b)), int(floor(y / b))))
                if not bucket:
                    continue
                for idx in bucket:
                    x0, x1, y0, y1 = tl[idx]["bb"]
                    if x < x0 or x > x1 or y < y0 or y > y1:
                        continue
                    pts = tl[idx]["pts"]
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
    try:
        while True:
            cols, rows = shutil.get_terminal_size((80, 24))
            H = rows - 1
            W = cols
            cx, cy = W / 2.0, H / 2.0
            t = frame * (1.0 / FPS)
            theta = ROT_SPEED * t

            s0 = W / UNITS_ACROSS
            z = (t / ZOOM_PERIOD) * ZOOM_DIR
            f = z - math.floor(z)          # 0..1 within the octave
            s_hi = s0 * (2.0 ** f)         # big octave, fades out
            s_lo = s0 * (2.0 ** (f - 1))   # small octave, fades in
            w_lo = f * f * (3.0 - 2.0 * f)  # smoothstep crossfade
            w_hi = 1.0 - w_lo

            idhi = id_grid(s_hi, theta, W, H, cx, cy)
            idlo = id_grid(s_lo, theta, W, H, cx, cy)
            ehi = edges(idhi, W, H)
            elo = edges(idlo, W, H)

            # one fixed, distinct color per tile: golden-ratio hue spacing so
            # every hat clashes with its neighbors. Whole palette drifts slowly.
            colcache = {-1: BG}
            drift = t * PALETTE_SPEED
            for grd in (idhi, idlo):
                for row in grd:
                    for idx in row:
                        if idx not in colcache:
                            hue = (idx * 0.61803398875 + drift) % 1.0
                            val = 0.60 + 0.40 * ((idx * 0.7548776662) % 1.0)
                            if tiles[idx]["r"]:  # reflected anti-hat -> pale glow
                                colcache[idx] = hsv_to_rgb(
                                    hue, SATURATION * 0.45, min(1.0, val + 0.25))
                            else:
                                colcache[idx] = hsv_to_rgb(hue, SATURATION, val)

            gr0, gr1, gr2 = GROUT
            out = ["\033[H"]
            last = None
            for row in range(H):
                ih = idhi[row]
                il = idlo[row]
                eh = ehi[row]
                el = elo[row]
                for col in range(W):
                    ch = colcache[ih[col]]
                    cl = colcache[il[col]]
                    r = w_hi * ch[0] + w_lo * cl[0]
                    g = w_hi * ch[1] + w_lo * cl[1]
                    b = w_hi * ch[2] + w_lo * cl[2]
                    gf = w_hi * eh[col] + w_lo * el[col]
                    if gf > 0.0:
                        inv = 1.0 - gf
                        r = r * inv + gr0 * gf
                        g = g * inv + gr1 * gf
                        b = b * inv + gr2 * gf
                    rgb = (int(r), int(g), int(b))
                    if rgb != last:
                        out.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")
                        last = rgb
                    out.append("█")
                out.append("\n")
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
