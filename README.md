# math-art

Pictures made from nothing but equations.

## `landscape.py` — a superposition of graphs

![the rendered superposition](landscape.png)

Six families of parametric curves — each a single equation, each drawn many times in rotational symmetry — laid over one another until no individual graph can be picked out; only the woven whole remains. The generating equations are printed beneath the image, colour-matched to their curves:

- **Maurer roses** — `r = sin(nθ)`, `θ = i·d°`
- **rose curves** — `r = cos(kθ)`
- **epicycloids** — `x = (a+b)cos t − b·cos((a+b)/b·t)`, `y = …`
- **Lissajous figures** — `x = sin(pt+δ)`, `y = sin(qt)`
- **hypotrochoids** (spirograph) — `x = (a−b)cos t + h·cos((a−b)/b·t)`, `y = …`
- **a harmonograph** — damped sums of sines, `x = Σ e^(−λt)·sin(ft+φ)`

```bash
python3 landscape.py      # writes landscape.png
```

Requires `numpy` and `matplotlib`.

## `plasma.py`

A morphing truecolor plasma field for the terminal, built from layered sine waves. `python3 plasma.py` (Ctrl-C to quit).

## License

MIT
