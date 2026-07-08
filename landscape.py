#!/usr/bin/env python3
"""
landscape.py — an ultra-real nature scene, made only from math.

Layered fractal-noise mountain ridgelines, atmospheric perspective (haze),
a graded dawn sky with a glowing sun, and drifting fog between the ridges.
Nothing is painted or photographed: every pixel is a function of position.
"""

import os

import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from PIL import Image

W, H = 1600, 1000


def fbm1(width, octaves, seed, persistence=0.5, base=5):
    """1-D fractal noise across the image width, normalized to ~[-1, 1]."""
    out = np.zeros(width)
    amp, tot, g = 1.0, 0.0, base
    r = np.random.default_rng(seed)
    for _ in range(octaves):
        grid = r.standard_normal(g + 1)
        up = zoom(grid, width / (g + 1), order=3)[:width]
        out += amp * up
        tot += amp
        amp *= persistence
        g *= 2
    return out / tot


def fbm2(h, w, octaves, seed, persistence=0.55, base=(4, 6)):
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    gh, gw = base
    r = np.random.default_rng(seed)
    for _ in range(octaves):
        grid = r.standard_normal((gh + 1, gw + 1))
        up = zoom(grid, (h / (gh + 1), w / (gw + 1)), order=3)[:h, :w]
        out += amp * up
        tot += amp
        amp *= persistence
        gh *= 2
        gw *= 2
    return out / tot


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def main():
    xs = np.linspace(0, 1, W)
    ys = np.linspace(0, 1, H)
    X, Y = np.meshgrid(xs, ys)              # 0..1 across, 0(top)..1(bottom)
    img = np.zeros((H, W, 3))

    # ---- sky: dawn gradient + sun glow ---------------------------------
    zenith = np.array([64, 104, 168]) / 255.0     # cool blue up high
    horizon = np.array([252, 226, 198]) / 255.0   # warm pale at the horizon
    tsky = smoothstep(0.0, 0.72, Y)               # blend down toward horizon
    sky = zenith[None, None] * (1 - tsky[..., None]) + horizon[None, None] * tsky[..., None]

    sun_x, sun_y = 0.70, 0.30
    sun = np.array([255, 244, 214]) / 255.0
    dist = np.sqrt(((X - sun_x) * (W / H)) ** 2 + (Y - sun_y) ** 2)
    glow = np.exp(-(dist / 0.26) ** 2) * 0.5 + np.exp(-(dist / 0.07) ** 2) * 0.85
    sky = sky + sun[None, None] * glow[..., None] * (1 - tsky[..., None] * 0.3)

    # soft clouds
    clouds = fbm2(H, W, 6, seed=21, persistence=0.55)
    clouds = smoothstep(0.05, 0.5, clouds) * smoothstep(0.62, 0.2, Y)
    cloud_col = np.array([255, 248, 236]) / 255.0
    sky = sky * (1 - 0.5 * clouds[..., None]) + cloud_col[None, None] * 0.5 * clouds[..., None]

    img[:] = np.clip(sky, 0, 1)

    # ---- mountain ranges, far to near ----------------------------------
    row = np.arange(H)[:, None].astype(float)
    n_layers = 7
    rock_far = np.array([150, 168, 190]) / 255.0    # pale bluish (hazy)
    rock_near = np.array([58, 60, 58]) / 255.0      # dark warm-grey rock
    snow_col = np.array([255, 252, 248]) / 255.0
    haze = horizon.copy()

    # light points from the surface toward the sun (upper-right in the image)
    Lx, Ly = 0.55, -0.62

    for k in range(n_layers):
        frac = k / (n_layers - 1)                   # 0 far .. 1 near
        base_y = (0.48 + 0.22 * frac) * H
        amp = (0.035 + 0.17 * frac) * H
        ridge = fbm1(W, octaves=5 + k, seed=100 + k, persistence=0.5)
        ridge = (ridge - ridge.min()) / (np.ptp(ridge) + 1e-9)
        ridge_y = base_y - amp * ridge              # screen row of the ridge per column

        cover = smoothstep(-1.5, 1.5, row - ridge_y[None, :])   # AA silhouette edge

        # lighting from a SMOOTHED height field so it follows big landforms
        # (ridges and gullies), not per-pixel speckle
        tex = fbm2(H, W, octaves=5, seed=200 + k, base=(2 + k, 3 + k), persistence=0.5)
        hs = gaussian_filter(tex, sigma=max(2.0, 9.0 - 1.1 * k))
        gy, gx = np.gradient(hs)
        relief = -(gx * Lx + gy * Ly)
        relief /= (relief.std() + 1e-9)
        relief = np.clip(relief, -3, 3)
        fine = fbm2(H, W, 3, seed=300 + k, base=(18, 30))     # subtle grain
        bright = 0.90 + (0.10 + 0.24 * frac) * relief + 0.05 * fine
        if k >= n_layers - 2:                      # crisper rock on near ranges
            g2y, g2x = np.gradient(gaussian_filter(tex, sigma=2.0))
            r2 = -(g2x * Lx + g2y * Ly)
            r2 /= (r2.std() + 1e-9)
            bright = bright + 0.10 * np.clip(r2, -2.5, 2.5) * frac
        bright = np.clip(bright, 0.55, 1.45)

        # atmospheric perspective: far ranges wash toward the haze color
        rock = rock_far * (1 - frac) + rock_near * frac
        depth_haze = (1 - frac) ** 1.2 * 0.78
        col = rock * (1 - depth_haze) + haze * depth_haze
        layer = col[None, None] * bright[..., None]

        # golden-hour light: warm the sun-lit faces, cool the shadows
        tf = np.clip((bright - 0.92) * 1.4, -1, 1)[..., None]
        warm = np.array([1.10, 1.01, 0.86])
        cool = np.array([0.90, 0.96, 1.14])
        pos = np.clip(tf, 0, 1)
        neg = np.clip(-tf, 0, 1)
        layer = layer * (1 + (warm - 1) * pos * 0.8 + (cool - 1) * neg * 0.8)

        # snow only on the highest ground of the two nearest ranges
        if k >= n_layers - 2:
            elev = np.clip((base_y - row) / (amp * 1.0) + 0.4 * hs, 0, 1)
            snow = smoothstep(0.74, 0.95, elev) * (frac ** 2)
            snow = snow * smoothstep(0.45, 0.85, np.clip(bright, 0, 1))
            snow = snow[..., None]
            layer = layer * (1 - snow) + snow_col[None, None] * snow

        img = img * (1 - cover[..., None]) + layer * cover[..., None]

        # low fog band between ranges: smooth (horizontal), not per-column jagged
        fog_center = base_y - amp * 0.18
        fog = np.exp(-((row - fog_center) / (amp * 0.7 + 1e-6)) ** 2)[:, 0][:, None]
        fog = fog * np.ones((1, W))
        fog *= (0.28 + 0.45 * (1 - frac)) * (0.7 + 0.3 * fbm2(H, W, 4, seed=50 + k))
        fog = np.clip(fog, 0, 1)
        fog_col = np.array([242, 238, 235]) / 255.0
        img = img * (1 - fog[..., None]) + fog_col[None, None] * fog[..., None]

    # ---- gentle photographic grade -------------------------------------
    img = np.clip(img, 0, 1)
    img = np.clip((img - 0.5) * 1.08 + 0.5, 0, 1)          # a little contrast
    img[..., 0] = np.clip(img[..., 0] * 1.03, 0, 1)        # warm the highlights
    img = img ** (1 / 1.03)                                # slight lift
    Image.fromarray((img * 255).astype(np.uint8)).save(OUT)
    print("saved", OUT)


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landscape.png")

if __name__ == "__main__":
    main()
