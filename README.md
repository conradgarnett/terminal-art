# terminal-art

Living, animated art pieces for your terminal. Pure Python standard library — no dependencies, truecolor, adapts to your terminal size in real time.

## Pieces

### `hat.py`
An **endless Droste log-spiral zoom** into a tiling of **"the hat"** — the aperiodic monotile discovered by Smith, Myers, Kaplan & Goodman-Strauss in 2023. It's a single 13-sided shape that tiles the plane but *never* repeats periodically. The view falls into the tiling forever, twisting into a logarithmic spiral that winds tighter toward the center, a vivid plasma field flowing across everything. Each hat is outlined so the shapes stay crisp; the reflected "anti-hats" (the ~1-in-7 mirror-image tiles the tiling can't avoid) glow as contrasting accents.

```bash
python3 hat.py
```

**The illusion:** the tiling is drawn at two zoom levels one octave apart and crossfaded. As the large octave grows too big and fades out, the small one grows into the exact size the large one started at — so the loop is seamless and the zoom never ends. (Verified: the dominant layer is bit-identical across the loop point.)

The tiling geometry lives in `hat_tiling.json` (1,156 hats, baked offline from Craig Kaplan's substitution system) so the renderer itself stays pure standard library.

**Tunable knobs** at the top of the file:

| Knob | Effect |
|------|--------|
| `TWIST` | log-spiral strength — twist per e-fold of radius (`0` = straight zoom) |
| `ZOOM_PERIOD` | seconds per octave — lower = faster fall inward |
| `ZOOM_DIR` | `1` = fall inward, `-1` = pull outward |
| `ROT_SPEED` | steady rotation on top of the spiral (radians/sec) |
| `UNITS_ACROSS` | base zoom — lower shows fewer, bigger hats |
| `TILE_JITTER` | per-tile hue variation so neighbors stay distinct |
| `FLOW_SPEED` | how fast the plasma flows |
| `PALETTE_SPEED` | how fast the colors cycle |
| `SATURATION` | color richness |
| `GROUT` | color of the lines between tiles |

### `plasma.py`
A morphing truecolor plasma field built from layered sine waves, cycling through an HSV color wheel with brightness driving an ASCII intensity ramp.

```bash
python3 plasma.py
```

Quit with `Ctrl-C` (uses the alternate screen buffer, so it leaves your scrollback clean).

**Tunable knobs** at the top of the file:

| Knob | Effect |
|------|--------|
| `FLOW_SPEED` | how fast the plasma churns |
| `PALETTE_SPEED` | how fast the colors cycle |
| `FPS` | frame rate / smoothness |
| `CHARS` | the character intensity ramp (try `" ░▒▓█"` for a blockier look) |

## Requirements

- Python 3.6+
- A terminal with 24-bit (truecolor) support — iTerm2 and modern macOS Terminal both work.

## License

MIT
