# terminal-art

Living, animated art pieces for your terminal. Pure Python standard library — no dependencies, truecolor, adapts to your terminal size in real time.

## Pieces

### `hat.py`
A living tiling of **"the hat"** — the aperiodic monotile discovered by Smith, Myers, Kaplan & Goodman-Strauss in 2023. It's a single 13-sided shape that tiles the plane but *never* repeats periodically. A vivid plasma field flows across the tiles like light through stained glass, and the reflected "anti-hats" (the ~1-in-7 mirror-image tiles the tiling can't avoid) glow as contrasting accents.

```bash
python3 hat.py
```

The tiling geometry lives in `hat_tiling.json` (1,156 hats, baked offline from Craig Kaplan's substitution system) so the renderer itself stays pure standard library.

**Tunable knobs** at the top of the file:

| Knob | Effect |
|------|--------|
| `UNITS_ACROSS` | zoom — lower shows fewer, bigger hats |
| `FLOW_SPEED` | how fast the plasma flows across the tiling |
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
