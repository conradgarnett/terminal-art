# terminal-art

Living, animated art pieces for your terminal. Pure Python standard library — no dependencies, truecolor, adapts to your terminal size in real time.

## Pieces

### `hat.py`
A slow **color-field painting** on a tiling of **"the hat"** — the aperiodic monotile discovered by Smith, Myers, Kaplan & Goodman-Strauss in 2023 (a single 13-sided shape that tiles the plane but *never* repeats periodically). The geometry holds still like a print; only the color moves. A curated **Bauhaus palette** — red, yellow, blue, near-black, and warm paper — drifts across the tiling in slow bands: paper as generous negative space, bold flat accents in alternating blocks, the occasional black shape for weight. Matisse cut-outs by way of Bauhaus, in a terminal.

```bash
python3 hat.py
```

Two slow fields at different scales drive it: a broad one carves paper / ink / colour, a finer one scatters which accent. The tiling is mapped to the screen once, so it runs at hundreds of fps in pure standard library.

The tiling geometry lives in `hat_tiling.json` (1,156 hats, baked offline from Craig Kaplan's substitution system).

**Tunable knobs** at the top of the file:

| Knob | Effect |
|------|--------|
| `UNITS_ACROSS` | scale — lower shows fewer, bigger shapes |
| `SPEED` | tempo of the color drift |
| `PAPER_LEVEL` | how much of the field stays bare paper (negative space) |
| `INK_LEVEL` | how readily a shape goes near-black |
| `ACCENTS` | the accent palette |
| `PAPER` / `INK` / `GROUT` | ground, black, and the line between tiles |

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
