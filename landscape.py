#!/usr/bin/env python3
"""
landscape.py — a nature scene made only of line segments, after the manner
of Hamid Naderi Yeganeh.

Every mark is a straight segment whose endpoints are trigonometric functions
of an index k. Where segments crowd, their envelope glows; the picture lives
in the caustics. A sunrise over the sea:

  * the sun          — chord caustics of a circle (k-th segment joins the
                       points at angles θ and mθ), layered and colour-graded
  * its reflection   — the same segments mirrored and rippled on the water
  * the sea          — stacked interfering wave-segment families
  * the birds        — small twin-arc segment fans
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landscape.png")

WARM = LinearSegmentedColormap.from_list("warm", [
    (0.78, 0.09, 0.12), (0.94, 0.42, 0.06),
    (0.99, 0.76, 0.23), (1.00, 0.97, 0.82)])
DEEP = np.array([0.05, 0.15, 0.27])
SHAL = np.array([0.40, 0.58, 0.71])
GOLD = np.array([0.96, 0.66, 0.11])


def sun_caustic(center, R, n=4200, mults=((6, 0.0), (11, 0.35), (18, 0.9))):
    """Chord caustics: segment k joins the circle points at angle θ and mθ."""
    k = np.arange(1, n + 1)
    th = 2 * np.pi * k / n
    seg_list, idx_list = [], []
    for m, ph in mults:
        b = m * th + ph
        p = np.stack([center[0] + R * np.cos(th), center[1] + R * np.sin(th)], 1)
        q = np.stack([center[0] + R * np.cos(b), center[1] + R * np.sin(b)], 1)
        seg_list.append(np.stack([p, q], 1))
        idx_list.append((k / n + m) % 1.0)          # colour phase per family
    return np.concatenate(seg_list), np.concatenate(idx_list)


def corona(center, R, n=1400, spike=0.1):
    k = np.arange(1, n + 1)
    t = 2 * np.pi * k / n
    outer = R * (1 + spike * np.sin(12 * t) + 0.4 * spike * np.sin(31 * t))
    a = np.stack([np.full(n, center[0]), np.full(n, center[1])], 1)
    b = np.stack([center[0] + outer * np.cos(t), center[1] + outer * np.sin(t)], 1)
    return np.stack([a, b], 1)


def reflect(segs, horizon):
    """Mirror segments across the horizon and ripple them like water."""
    s = segs.copy()
    s[:, :, 1] = 2 * horizon - s[:, :, 1]            # flip below the horizon
    depth = np.clip(horizon - s[:, :, 1], 0, None)
    s[:, :, 1] = horizon - depth * 0.92              # slight foreshortening
    s[:, :, 0] += (0.012 + 0.05 * depth) * np.sin(17 * depth + 5 * s[:, :, 0])
    keep = (s[:, :, 1] < horizon).all(axis=1)        # only what lands on water
    return s[keep]


def sea(ax, horizon, sun_x, x0=-2.35, x1=2.35, rows=200, samples=620):
    x = np.linspace(x0, x1, samples)
    blue_segs, blue_cols, gold_segs = [], [], []
    for i in range(rows):
        u = i / (rows - 1)
        y0 = horizon - (0.012 + 1.75 * u ** 1.5)
        amp = 0.004 + 0.058 * u
        wl = 0.15 + 1.05 * u
        ph = 2.6 * i
        y = (y0 + amp * np.sin(2 * np.pi * x / wl + ph)
             + 0.45 * amp * np.sin(2 * np.pi * x / (wl * 0.5) + 1.7 * ph)
             + 0.2 * amp * np.sin(2 * np.pi * x / (wl * 0.27) + 0.6 * ph))
        pts = np.stack([x, y], 1)
        seg = np.stack([pts[:-1], pts[1:]], 1)
        mid = 0.5 * (x[:-1] + x[1:])
        gold_mask = np.abs(mid - sun_x) < (0.045 + 0.4 * u)
        gold_segs.append(seg[gold_mask])
        blue_segs.append(seg[~gold_mask])
        col = DEEP * u + SHAL * (1 - u)
        blue_cols.append(np.tile(col, ((~gold_mask).sum(), 1)))
    ax.add_collection(LineCollection(np.concatenate(blue_segs),
                      colors=np.concatenate(blue_cols), linewidths=0.7, alpha=0.85))
    ax.add_collection(LineCollection(np.concatenate(gold_segs),
                      colors=GOLD, linewidths=0.85, alpha=0.5))


def birds(ax, n=22):
    j = np.arange(n)
    bx = -2.0 + 3.9 * (j / n) + 0.12 * np.sin(4.1 * j)
    by = 1.02 - 0.30 * (j / n) + 0.14 * np.sin(2.3 * j + 1)
    s = 0.045 * (0.5 + 1.0 * (1 - j / n))
    t = np.linspace(-1, 1, 24)
    segs = []
    for i in j:
        wx = bx[i] + s[i] * 1.5 * t
        wy = by[i] + s[i] * 0.6 * np.abs(np.sin(np.pi * t)) - s[i] * 0.15 * t ** 2
        pts = np.stack([wx, wy], 1)
        segs.append(np.stack([pts[:-1], pts[1:]], 1))
    ax.add_collection(LineCollection(np.concatenate(segs),
                      colors=(0.15, 0.17, 0.21), linewidths=1.0))


def main():
    fig = plt.figure(figsize=(12, 9.6), dpi=150, facecolor="white")
    ax = fig.add_axes([0.0, 0.11, 1.0, 0.88])
    ax.set_xlim(-2.35, 2.35)
    ax.set_ylim(-1.72, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")

    horizon = 0.16
    sun_c = (0.0, 0.66)
    segs, idx = sun_caustic(sun_c, 0.52)

    # reflection first (under everything), then sea, then the sun on top
    ax.add_collection(LineCollection(reflect(segs, horizon),
                      colors=GOLD, linewidths=0.25, alpha=0.08, zorder=1))
    ax.add_collection(LineCollection(corona(sun_c, 0.64, spike=0.14),
                      colors=GOLD, linewidths=0.5, alpha=0.05, zorder=2))
    sea(ax, horizon, sun_c[0])
    lc = LineCollection(segs, array=idx, cmap=WARM, linewidths=0.3, alpha=0.32, zorder=6)
    ax.add_collection(lc)
    birds(ax)

    cap = (r"segment $k$ joins two points of a circle:$\quad$"
           r"$P(k)=C+R(\cos\theta,\sin\theta),\ \ Q(k)=C+R(\cos m\theta,\sin m\theta),"
           r"\ \ \theta=\frac{2\pi k}{N},\ \ m\in\{6,11,18\}$")
    fig.text(0.5, 0.055, "MADE ONLY OF LINE SEGMENTS", ha="center", va="center",
             color=GOLD, fontsize=11, fontweight="bold")
    fig.text(0.5, 0.022, cap, ha="center", va="center", color="#3a3a3a", fontsize=11.5)

    fig.savefig(OUT, facecolor="white")
    print("saved", OUT)


if __name__ == "__main__":
    main()
