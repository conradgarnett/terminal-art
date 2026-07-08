# terminal-art

Living, animated art pieces for your terminal. Pure Python standard library — no dependencies, truecolor, adapts to your terminal size in real time.

## Pieces

### `hat.py`
A slowly **spinning** tiling of **"the spectre"** — the aperiodic monotile discovered by Smith, Myers, Kaplan & Goodman-Strauss in 2023. It's a single 14-sided shape that tiles the plane, *never* repeats periodically, and — unlike its sibling "the hat" — needs **no reflections**, making it a true "einstein" (one stone). The tiling turns in place like a colored-glass wheel.

```bash
python3 hat.py
```

Every tile gets its **own distinct color** (golden-ratio hue spacing, so adjacent shapes always clash). There are no outlines — they read as grey at this scale — so the color changes themselves mark the tile edges, and each spectre reads on its own.

The tiling geometry lives in `spectre_tiling.json`, baked offline from a level-4 patch of Craig Kaplan's substitution system. The bake step (`bake_spectre.py`) also runs a small **machine-learning** pass: it fingerprints each tile's local neighborhood (rotation-invariant) and **k-means clusters** them into the tiling's recurring "local motifs," storing a cluster label per tile. Those labels ship in the data as an alternate way to color the piece (motif-class instead of per-tile), even though the default coloring is one hue per tile.

The per-cell rotation geometry is precomputed once and the tile lookup uses a spatial hash plus a same-tile fast path, so it stays smooth (100+ fps) in pure Python even on large terminals.

**Tunable knobs** at the top of the file:

| Knob | Effect |
|------|--------|
| `ROT_SPEED` | spin speed in radians/sec (negative to reverse) |
| `TWIST` | log-spiral swirl on top of the spin (`0` = rigid spin) |
| `UNITS_ACROSS` | scale — lower shows fewer, bigger tiles |
| `PALETTE_SPEED` | how fast the palette drifts |
| `SATURATION` | color richness |

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
