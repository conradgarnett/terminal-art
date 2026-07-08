# math-art

Pictures made from nothing but equations.

## `landscape.py` — a seascape of line segments

![the rendered seascape](landscape.png)

A sunrise over the sea, built the way mathematician-artist **Hamid Naderi Yeganeh** builds his images: the entire picture is families of straight **line segments** whose endpoints are explicit trigonometric functions of an index `k`. Where the segments crowd, the plane darkens or glows; where they fan out, it fades. Nothing is drawn freehand or filled.

Three families make the scene:

- **Sun** — segment `k` joins the center `C` to a point on a spiked circle,
  `P(k) = C + R₀(1 + 0.09·sin12θ)(cosθ, sinθ)`, `θ = 2πk/N`. The segments
  crowd near `C` into a bright disc and fan outward into a soft corona.
- **Sea** — stacked families of wave segments (sums of sines), spaced non-linearly
  for perspective. The segments beneath the sun are drawn gold, tracing its
  shimmering reflection down the water.
- **Birds** — small twin-arc segment fans, `y ∝ |sin πt|`.

```bash
python3 landscape.py      # writes landscape.png
```

Requires `numpy` and `matplotlib`.

## `plasma.py`

A morphing truecolor plasma field for the terminal, built from layered sine waves. `python3 plasma.py` (Ctrl-C to quit).

## License

MIT
