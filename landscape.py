#!/usr/bin/env python3
"""
landscape.py — an intricate superposition of parametric graphs.

Several families of curves — each a single equation, drawn many times in
rotational symmetry — are laid over one another until no individual graph
can be picked out; only the woven whole remains. Every generating equation
is printed beneath the image, colour-matched to its curves.
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landscape.png")

BG = "#0a0c15"
COL = {
    "maurer":  (0.96, 0.71, 0.16),   # gold
    "rose":    (1.00, 0.36, 0.56),    # rose
    "epi":     (0.22, 0.84, 0.80),    # cyan
    "liss":    (0.62, 0.49, 1.00),    # violet
    "hypo":    (0.42, 0.90, 0.52),    # green
    "harm":    (0.94, 0.90, 0.80),    # warm white
}

T = np.linspace(0, 2 * np.pi, 3000)


def rot(x, y, a):
    c, s = np.cos(a), np.sin(a)
    return x * c - y * s, x * s + y * c


def norm(x, y, target=1.0):
    m = max(np.abs(x).max(), np.abs(y).max())
    return x / m * target, y / m * target


def sym(ax, x, y, color, copies, lw=0.55, alpha=0.35, spin=0.0):
    """Draw a curve in `copies`-fold rotational symmetry."""
    segs = []
    for j in range(copies):
        a = spin + 2 * np.pi * j / copies
        rx, ry = rot(x, y, a)
        p = np.stack([rx, ry], 1)
        segs.append(np.stack([p[:-1], p[1:]], 1))
    ax.add_collection(LineCollection(np.concatenate(segs), colors=color,
                                     linewidths=lw, alpha=alpha))


def maurer(n, d):
    i = np.arange(0, 361)
    k = np.deg2rad(i * d)
    r = np.sin(n * k)
    return r * np.cos(k), r * np.sin(k)


def main():
    fig = plt.figure(figsize=(11, 13), dpi=150, facecolor=BG)
    ax = fig.add_axes([0.0, 0.30, 1.0, 0.70])
    ax.set_xlim(-1.16, 1.16)
    ax.set_ylim(-1.16, 1.16)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(BG)

    # 1. Maurer roses -------------------------------------------------------
    for n, d in [(6, 71), (5, 97), (7, 47)]:
        x, y = maurer(n, d)
        x, y = norm(x, y, 1.05)
        sym(ax, x, y, COL["maurer"], copies=4, lw=0.4, alpha=0.28)

    # 2. Rose curves  r = cos(k theta) -------------------------------------
    for k in [4, 7, 12]:
        r = np.cos(k * T)
        x, y = norm(r * np.cos(T), r * np.sin(T), 1.0)
        sym(ax, x, y, COL["rose"], copies=6, lw=0.5, alpha=0.3)

    # 3. Epicycloids -------------------------------------------------------
    for a, b in [(5, 1), (7, 2), (3, 1)]:
        x = (a + b) * np.cos(T) - b * np.cos((a + b) / b * T)
        y = (a + b) * np.sin(T) - b * np.sin((a + b) / b * T)
        x, y = norm(x, y, 1.1)
        sym(ax, x, y, COL["epi"], copies=5, lw=0.45, alpha=0.28)

    # 4. Lissajous  x=sin(pt+d), y=sin(qt) ---------------------------------
    for p, q, dl in [(3, 4, 0.4), (5, 6, 1.1), (7, 8, 0.0)]:
        x, y = norm(np.sin(p * T + dl), np.sin(q * T), 1.08)
        sym(ax, x, y, COL["liss"], copies=8, lw=0.4, alpha=0.24, spin=0.2)

    # 5. Hypotrochoids (spirograph) ----------------------------------------
    for a, b, h in [(8, 3, 5), (7, 4, 3), (9, 2, 4)]:
        x = (a - b) * np.cos(T) + h * np.cos((a - b) / b * T)
        y = (a - b) * np.sin(T) - h * np.sin((a - b) / b * T)
        x, y = norm(x, y, 1.0)
        sym(ax, x, y, COL["hypo"], copies=6, lw=0.4, alpha=0.26)

    # 6. Harmonograph  (damped sums of sines) ------------------------------
    tt = np.linspace(0, 60, 9000)
    for ph in [0.0, 0.9, 1.8]:
        x = (np.exp(-0.006 * tt) * np.sin(2.01 * tt + ph)
             + np.exp(-0.004 * tt) * np.sin(2.98 * tt))
        y = (np.exp(-0.005 * tt) * np.sin(3.02 * tt + 1.3)
             + np.exp(-0.007 * tt) * np.sin(1.99 * tt + ph))
        x, y = norm(x, y, 1.12)
        sym(ax, x, y, COL["harm"], copies=1, lw=0.35, alpha=0.35)

    # ---- all the equations, colour-matched, beneath ----------------------
    lines = [
        ("maurer", r"$r=\sin(n\theta),\quad \theta = i\,d^{\circ},\quad (n,d)\in\{(6,71),(5,97),(7,47)\}$"),
        ("rose",   r"$r=\cos(k\theta),\quad (x,y)=(r\cos\theta,\ r\sin\theta),\quad k\in\{4,7,12\}$"),
        ("epi",    r"$x=(a{+}b)\cos t-b\cos\frac{a+b}{b}t,\quad y=(a{+}b)\sin t-b\sin\frac{a+b}{b}t$"),
        ("liss",   r"$x=\sin(pt+\delta),\quad y=\sin(qt),\quad (p,q)\in\{(3,4),(5,6),(7,8)\}$"),
        ("hypo",   r"$x=(a{-}b)\cos t+h\cos\frac{a-b}{b}t,\quad y=(a{-}b)\sin t-h\sin\frac{a-b}{b}t$"),
        ("harm",   r"$x=\sum_i e^{-\lambda_i t}\sin(f_i t+\varphi_i),\quad y=\sum_i e^{-\mu_i t}\sin(g_i t+\psi_i)$"),
    ]
    fig.text(0.5, 0.265, "ALL OF THE ABOVE, AT ONCE",
             ha="center", va="center", color="#8b8fa3", fontsize=12,
             fontweight="bold")
    y0 = 0.225
    for key, eq in lines:
        fig.text(0.075, y0, "—", color=COL[key], fontsize=15,
                 fontweight="bold", ha="left", va="center")
        fig.text(0.11, y0, eq, color="#d9dce6", fontsize=12.5,
                 ha="left", va="center")
        y0 -= 0.037

    fig.savefig(OUT, facecolor=BG)
    print("saved", OUT)


if __name__ == "__main__":
    main()
