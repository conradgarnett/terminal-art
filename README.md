# terminal-art

Living, animated art pieces for your terminal. Pure Python standard library — no dependencies, truecolor, adapts to your terminal size in real time.

## Pieces

### `hat.py`
An **endless Droste log-spiral zoom** into a tiling of **"the spectre"** — the aperiodic monotile discovered by Smith, Myers, Kaplan & Goodman-Strauss in 2023. It's a single 14-sided shape that tiles the plane, *never* repeats periodically, and — unlike its sibling "the hat" — needs **no reflections**, making it a true "einstein" (one stone). The view pulls outward forever, twisting into a logarithmic spiral. Every tile gets its own fixed distinct color (golden-ratio hue spacing, so neighbors always clash) with a black outline, and the whole palette drifts slowly.

The per-cell spiral geometry is precomputed once and the tile lookup uses a spatial hash plus a same-tile fast path, so it stays smooth (tens of fps) in pure Python even on large terminals.

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
| `PALETTE_SPEED` | how fast the whole palette drifts |
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
