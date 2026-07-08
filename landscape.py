#!/usr/bin/env python3
"""
landscape.py — a nature scene made only of line segments, in the style of
Hamid Naderi Yeganeh.

Nothing is drawn freehand: the whole picture is families of straight line
segments whose endpoints are explicit trigonometric functions of an index
k. Where the segments crowd, the plane darkens; where they fan out, it
glows. Three families make a sunrise over the sea:

  * the sun    — radial segments to a wavy corona
  * the sea    — stacked wave segments, gold where the sun reflects
  * the birds  — small twin-arc segment fans

The k-th segment of a family joins A(k) to B(k); see the caption.
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landscape.png")

GOLD = np.array([0.96, 0.66, 0.11])
DEEP = np.array([0.06, 0.16, 0.28])
SHAL = np.array([0.42, 0.60, 0.72])


def sun_rays(center, R, n=1200, spike=0.09):
    """Segment k joins the center C to a point on a spiked circle; the many
    segments crowd near C into a bright disc that softens toward the rim."""
    k = np.arange(1, n + 1)
    t = 2 * np.pi * k / n
    outer = R * (1 + spike * np.sin(12 * t) + 0.4 * spike * np.sin(31 * t))
    bx = center[0] + outer * np.cos(t)
    by = center[1] + outer * np.sin(t)
    a = np.stack([np.full(n, center[0]), np.full(n, center[1])], 1)
    b = np.stack([bx, by], 1)
    return np.stack([a, b], 1)


def sea(ax, horizon, sun_x, x0=-2.3, x1=2.3, rows=150, samples=520):
    x = np.linspace(x0, x1, samples)
    blue_segs, gold_segs = [], []
    blue_cols = []
    for i in range(rows):
        u = i / (rows - 1)                               # 0 horizon .. 1 near
        y0 = horizon - (0.015 + 1.7 * u ** 1.45)
        amp = 0.004 + 0.055 * u
        wl = 0.16 + 1.0 * u
        ph = 2.7 * i
        y = (y0 + amp * np.sin(2 * np.pi * x / wl + ph)
             + 0.4 * amp * np.sin(2 * np.pi * x / (wl * 0.5) + 1.7 * ph))
        pts = np.stack([x, y], 1)
        seg = np.stack([pts[:-1], pts[1:]], 1)
        mid = 0.5 * (x[:-1] + x[1:])
        # sun's reflected path: a widening column under the sun -> gold
        halfw = 0.05 + 0.42 * u
        gold_mask = np.abs(mid - sun_x) < halfw
        gold_segs.append(seg[gold_mask])
        blue_segs.append(seg[~gold_mask])
        col = DEEP * u + SHAL * (1 - u)
        blue_cols.append(np.tile(col, ((~gold_mask).sum(), 1)))

    blue = np.concatenate(blue_segs)
    ax.add_collection(LineCollection(blue, colors=np.concatenate(blue_cols),
                                     linewidths=0.8, alpha=0.85))
    gold = np.concatenate(gold_segs)
    ax.add_collection(LineCollection(gold, colors=GOLD, linewidths=0.9, alpha=0.5))


def birds(ax, n=16):
    j = np.arange(n)
    r = np.random.default_rng(3)
    bx = -1.85 + 3.4 * (j / n) + 0.12 * np.sin(4.1 * j)
    by = 0.98 - 0.34 * (j / n) + 0.13 * np.sin(2.3 * j + 1)
    s = 0.045 * (0.55 + 0.9 * (1 - j / n))               # nearer birds bigger
    segs = []
    t = np.linspace(-1, 1, 22)
    for i in j:
        wx = bx[i] + s[i] * 1.5 * t
        wy = by[i] + s[i] * 0.6 * np.abs(np.sin(np.pi * t)) - s[i] * 0.15 * t ** 2
        pts = np.stack([wx, wy], 1)
        segs.append(np.stack([pts[:-1], pts[1:]], 1))
    ax.add_collection(LineCollection(np.concatenate(segs),
                                     colors=(0.16, 0.18, 0.22), linewidths=1.1))


def main():
    fig = plt.figure(figsize=(12, 9.6), dpi=150, facecolor="white")
    ax = fig.add_axes([0.0, 0.11, 1.0, 0.88])
    ax.set_xlim(-2.3, 2.3)
    ax.set_ylim(-1.7, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")

    horizon = 0.16
    sun_c = (0.0, 0.62)

    # sun: three families of radial segments -> corona, disc, hot core
    ax.add_collection(LineCollection(sun_rays(sun_c, 0.48, 1500, spike=0.12),
                      colors=GOLD, linewidths=0.6, alpha=0.08, zorder=3))
    ax.add_collection(LineCollection(sun_rays(sun_c, 0.22, 1500, spike=0.05),
                      colors=GOLD, linewidths=0.7, alpha=0.16, zorder=4))
    ax.add_collection(LineCollection(sun_rays(sun_c, 0.11, 800, spike=0.0),
                      colors=(1.0, 0.92, 0.66), linewidths=0.7, alpha=0.22, zorder=5))
    sea(ax, horizon, sun_c[0])
    birds(ax)

    cap = (r"segment $k$ joins the center $C$ to $P(k)$:$\quad$"
           r"$P(k)=C+R_0\left(1+\frac{9}{100}\sin 12\theta\right)"
           r"(\cos\theta,\,\sin\theta),\quad \theta=\frac{2\pi k}{N}$")
    fig.text(0.5, 0.055, "MADE ONLY OF LINE SEGMENTS",
             ha="center", va="center", color=GOLD, fontsize=11,
             fontfamily="sans-serif", fontweight="bold")
    fig.text(0.5, 0.022, cap, ha="center", va="center", color="#3a3a3a",
             fontsize=11.5)

    fig.savefig(OUT, facecolor="white")
    print("saved", OUT)


if __name__ == "__main__":
    main()
