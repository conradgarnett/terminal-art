#!/usr/bin/env python3
"""
landscape.py — an ultra-real nature scene, made only from math.

Layered fractal-noise mountain ridgelines, atmospheric perspective (haze),
sun-direction lighting on ridged height fields, golden-hour grading, snow,
a graded dawn sky, and drifting fog. Nothing is painted or photographed:
every pixel is a function of its coordinates. The equations that build it
are printed on a placard beneath the render.
"""

import os

import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1000


def fbm1(width, octaves, seed, persistence=0.5, base=5):
    out = np.zeros(width)
    amp, tot, g = 1.0, 0.0, base
    r = np.random.default_rng(seed)
    for _ in range(octaves):
        up = zoom(r.standard_normal(g + 1), width / (g + 1), order=3)[:width]
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
        up = zoom(r.standard_normal((gh + 1, gw + 1)),
                  (h / (gh + 1), w / (gw + 1)), order=3)[:h, :w]
        out += amp * up
        tot += amp
        amp *= persistence
        gh *= 2
        gw *= 2
    return out / tot


def ridged1(width, octaves, seed, persistence=0.5, base=5):
    """1-D ridged fractal noise: sharp crests instead of rounded hills."""
    out = np.zeros(width)
    amp, tot, g = 1.0, 0.0, base
    r = np.random.default_rng(seed)
    for _ in range(octaves):
        up = zoom(r.standard_normal(g + 1), width / (g + 1), order=3)[:width]
        up /= (np.abs(up).max() + 1e-9)
        out += amp * (1.0 - np.abs(up))
        tot += amp
        amp *= persistence
        g *= 2
    return out / tot


def ridged2(h, w, octaves, seed, persistence=0.5, base=(3, 4)):
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    gh, gw = base
    r = np.random.default_rng(seed)
    for _ in range(octaves):
        up = zoom(r.standard_normal((gh + 1, gw + 1)),
                  (h / (gh + 1), w / (gw + 1)), order=3)[:h, :w]
        up /= (np.abs(up).max() + 1e-9)
        out += amp * (1.0 - np.abs(up))
        tot += amp
        amp *= persistence
        gh *= 2
        gw *= 2
    return out / tot


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def render_scene():
    xs = np.linspace(0, 1, W)
    ys = np.linspace(0, 1, H)
    X, Y = np.meshgrid(xs, ys)
    img = np.zeros((H, W, 3))

    # ---- sky: dawn gradient + sun glow ---------------------------------
    zenith = np.array([60, 100, 166]) / 255.0
    horizon = np.array([252, 226, 198]) / 255.0
    tsky = smoothstep(0.0, 0.72, Y)
    sky = zenith[None, None] * (1 - tsky[..., None]) + horizon[None, None] * tsky[..., None]

    sun_x, sun_y = 0.70, 0.30
    sun = np.array([255, 244, 214]) / 255.0
    dist = np.sqrt(((X - sun_x) * (W / H)) ** 2 + (Y - sun_y) ** 2)
    glow = np.exp(-(dist / 0.26) ** 2) * 0.5 + np.exp(-(dist / 0.07) ** 2) * 0.85
    sky = sky + sun[None, None] * glow[..., None] * (1 - tsky[..., None] * 0.3)

    clouds = fbm2(H, W, 6, seed=21)
    clouds = smoothstep(0.05, 0.5, clouds) * smoothstep(0.62, 0.2, Y)
    cloud_col = np.array([255, 248, 236]) / 255.0
    sky = sky * (1 - 0.5 * clouds[..., None]) + cloud_col[None, None] * 0.5 * clouds[..., None]
    img[:] = np.clip(sky, 0, 1)

    # ---- mountain ranges, far to near ----------------------------------
    row = np.arange(H)[:, None].astype(float)
    n_layers = 7
    rock_far = np.array([150, 168, 190]) / 255.0
    rock_near = np.array([60, 58, 54]) / 255.0
    snow_col = np.array([255, 252, 248]) / 255.0
    haze = horizon.copy()
    Lx, Ly = 0.55, -0.62

    for k in range(n_layers):
        frac = k / (n_layers - 1)
        base_y = (0.48 + 0.22 * frac) * H
        amp = (0.035 + 0.17 * frac) * H

        ridge = ridged1(W, octaves=5 + k, seed=100 + k)
        ridge = (ridge - ridge.min()) / (np.ptp(ridge) + 1e-9)
        ridge_y = base_y - amp * ridge
        cover = smoothstep(-1.5, 1.5, row - ridge_y[None, :])

        # ridged height field -> crisp ridges/gullies under sun-direction light
        hegt = ridged2(H, W, octaves=6, seed=200 + k, base=(2 + k, 3 + k))
        hs = gaussian_filter(hegt, sigma=max(1.5, 6.0 - 0.9 * k))
        gy, gx = np.gradient(hs)
        relief = -(gx * Lx + gy * Ly)
        relief /= (relief.std() + 1e-9)
        relief = np.clip(relief, -3, 3)
        fine = fbm2(H, W, 3, seed=300 + k, base=(18, 30))
        bright = 0.90 + (0.10 + 0.26 * frac) * relief + 0.05 * fine
        if k >= n_layers - 2:
            g2y, g2x = np.gradient(gaussian_filter(hegt, sigma=1.6))
            r2 = -(g2x * Lx + g2y * Ly)
            r2 /= (r2.std() + 1e-9)
            bright = bright + 0.12 * np.clip(r2, -2.5, 2.5) * frac
        bright = np.clip(bright, 0.52, 1.5)

        rock = rock_far * (1 - frac) + rock_near * frac
        depth_haze = (1 - frac) ** 1.2 * 0.78
        col = rock * (1 - depth_haze) + haze * depth_haze
        layer = col[None, None] * bright[..., None]

        # golden hour: warm the lit faces, cool the shadows
        tf = np.clip((bright - 0.92) * 1.4, -1, 1)[..., None]
        warm = np.array([1.10, 1.01, 0.86])
        cool = np.array([0.90, 0.96, 1.14])
        pos = np.clip(tf, 0, 1)
        neg = np.clip(-tf, 0, 1)
        layer = layer * (1 + (warm - 1) * pos * 0.8 + (cool - 1) * neg * 0.8)

        if k >= n_layers - 2:
            elev = np.clip((base_y - row) / (amp * 1.0) + 0.4 * hs, 0, 1)
            snow = smoothstep(0.74, 0.95, elev) * (frac ** 2)
            snow = (snow * smoothstep(0.45, 0.85, np.clip(bright, 0, 1)))[..., None]
            layer = layer * (1 - snow) + snow_col[None, None] * snow

        img = img * (1 - cover[..., None]) + layer * cover[..., None]

        fog_center = base_y - amp * 0.18
        fog = np.exp(-((row - fog_center) / (amp * 0.7 + 1e-6)) ** 2) * np.ones((1, W))
        fog *= (0.28 + 0.45 * (1 - frac)) * (0.7 + 0.3 * fbm2(H, W, 4, seed=50 + k))
        fog = np.clip(fog, 0, 1)
        fog_col = np.array([242, 238, 235]) / 255.0
        img = img * (1 - fog[..., None]) + fog_col[None, None] * fog[..., None]

    # ---- photographic grade + vignette ---------------------------------
    img = np.clip(img, 0, 1)
    img = np.clip((img - 0.5) * 1.10 + 0.5, 0, 1)
    img[..., 0] = np.clip(img[..., 0] * 1.03, 0, 1)
    img = img ** (1 / 1.03)
    vig = np.clip(1 - 0.6 * (((X - 0.5) * 1.15) ** 2 + ((Y - 0.5) * 1.15) ** 2), 0.62, 1)
    img = img * vig[..., None]
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


# ------------------------------------------------------------------------
# The equations, printed on a placard under the render.
# ------------------------------------------------------------------------
EQUATIONS = [
    ("fractal noise", "fbm(p) = Σ a^n · noise(2^n · p),   a = 0.5"),
    ("dawn sky", "C(y) = C_zenith·(1 − s) + C_horizon·s,   s = smoothstep(0, 0.72, y)"),
    ("sun glow", "G = 0.5·exp(−(d/0.26)²) + 0.85·exp(−(d/0.07)²)"),
    ("ridgelines", "y_ridge(x) = y₀ − A · ridged-fbm(x)"),
    ("relief lighting", "b = 0.9 + k · ( −∇(Gσ ∗ h) · L )"),
    ("atmosphere", "C = C_rock·(1 − f) + C_haze·f,   f = (1 − depth)^1.2"),
    ("golden hour", "warm where b > 0.92,   cool where b < 0.92"),
    ("fog", "F = exp( −((y − y_f) / w)² )"),
]

FONTS = {
    "sans": ["/System/Library/Fonts/Helvetica.ttc",
             "/System/Library/Fonts/Supplemental/Arial.ttf"],
    "mono": ["/System/Library/Fonts/Menlo.ttc",
             "/System/Library/Fonts/SFNSMono.ttf",
             "/System/Library/Fonts/Supplemental/Courier New.ttf"],
}


def load_font(kind, size):
    for p in FONTS[kind]:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def tracked(draw, pos, text, font, fill, track):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track


def compose(scene):
    H0, W0 = scene.shape[:2]
    pad, panel_h = 78, 546
    bg = (16, 18, 24)
    accent = (233, 181, 120)
    ink = (222, 225, 232)
    muted = (146, 149, 164)
    rule = (52, 56, 66)

    canvas = Image.new("RGB", (W0, H0 + panel_h), bg)
    canvas.paste(Image.fromarray(scene), (0, 0))
    d = ImageDraw.Draw(canvas)

    f_eye = load_font("sans", 16)
    f_sub = load_font("sans", 15)
    f_lab = load_font("sans", 18)
    f_eq = load_font("mono", 22)

    y = H0 + 42
    tracked(d, (pad, y), "THE MATHEMATICS BEHIND THE IMAGE", f_eye, accent, 3)
    y += 27
    d.text((pad, y), "Every pixel above is a function of its coordinates — "
           "no photograph, no brush.", font=f_sub, fill=muted)
    y += 33
    d.line([(pad, y), (W0 - pad, y)], fill=rule, width=1)
    y += 20
    for label, eq in EQUATIONS:
        d.text((pad, y + 2), label, font=f_lab, fill=accent)
        d.text((pad + 200, y), eq, font=f_eq, fill=ink)
        y += 45
    return canvas


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "landscape.png")


def main():
    compose(render_scene()).save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
