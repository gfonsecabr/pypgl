<img align="left" src="figures/logo.png" width="23%"/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/logotextdark.svg"/>
  <img alt="Pangolin: Plane Geometry Library" src="figures/logotext.svg" width="65%"/>
</picture>

<!-- [![Tests](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml/badge.svg)](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml)
[![Standard](https://img.shields.io/badge/C%2B%2B-20/23/26-rgb(10,66,158).svg)](https://en.wikipedia.org/wiki/C%2B%2B#Standardization) -->
[![License](https://img.shields.io/badge/license-MIT-rgb(216,134,42).svg)](https://opensource.org/licenses/MIT)
<!-- [![Benchmarks](https://img.shields.io/badge/benchmarks-online-rgb(21,153,135).svg)](https://gfonsecabr.github.io/pgl/benchmarks/index.html) -->


⚠️ **Work in Progress**: This library is still under construction and contains **bugs and missing features**. Use in production environments is not recommended.

## Canvas

`Canvas` is a lightweight renderer for Pangolin shapes. It is designed for
inspection, debugging, examples, and test output: you draw shapes onto a canvas,
optionally change the drawing style in between, and then export the result as
[SVG, PDF, or Ipe XML](#export-formats).

The canvas automatically fits the drawn geometry into the output image,
preserves aspect ratio, clips infinite primitives to the visible viewport, and
stores an SVG `<title>` for each drawn element so that exported images keep a
human-readable tooltip.

In Jupyter / IPython every shape and every canvas renders itself inline (through
`_repr_svg_`), so simply evaluating a shape or a canvas as the last expression in
a cell displays it — see [Inline display in Jupyter](#inline-display-in-jupyter)
below.

<table>
  <tr>
    <td valign="top" width="58%">

```python
import pypgl as pgl

# Let's set up two segments that cross in a nice visible spot.
p, q = pgl.Point(1, 0), pgl.Point(4, 7)
s, t = pgl.Segment(p, q), pgl.Segment(0, 8, 2, 1)

# Create your canvas
canvas = pgl.Canvas()
canvas.size(900, 560) \
      .margin(30) \
      .pointRadius(5) \
      .strokeWidth(4) \
      .borders(True)   # if you want borders

# Draw the two segments with distinct colors.
canvas.stroke("royalblue").fill("none").draw(s)
canvas.stroke("darkorange").draw(t)
# Then draw the endpoints on top so they stay easy to spot.
canvas.stroke("black").fill("black").draw(p).draw(q)

# When they cross, highlight the exact intersection too! drawing None (an empty
# intersection) is a harmless no-op, so no guard is needed.
canvas.stroke("crimson").fill("crimson").draw(s.intersection(t))

# One call writes the finished SVG.
canvas.writeSVG("example1.svg")
```

  </td>
    <td valign="top" width="42%">
      <img src="figures/canvas_example_intersection.svg" alt="Canvas intersection example" width="100%"/>
    </td>
  </tr>
</table>

The exact intersection point is computed with rational arithmetic and drawn on
top, so the highlight sits precisely where the two segments meet.

### Style

The canvas maintains a current style. When you draw a shape, that shape captures
the style that is active at that exact moment. Changing the style afterwards
affects only shapes drawn later.

This is why the order of calls matters:

```python
canvas = pgl.Canvas()
first, second = pgl.Segment(0, 0, 4, 3), pgl.Segment(0, 3, 4, 0)
# Each shape remembers the style that was active when it was drawn.
canvas.stroke("royalblue").draw(first)
# So changing the stroke now only affects what comes next.
canvas.stroke("crimson").draw(second)
```

Here `first` stays blue even though the current canvas stroke later becomes
crimson.

Each style method takes an SVG string and returns the canvas:

| Method | Effect |
| --- | --- |
| `canvas.stroke("value")` | Sets the stroke color or stroke paint used for subsequent shapes. Typical values are color names such as `"red"`, hex codes such as `"#3366cc"`, or any SVG paint value. |
| `canvas.fill("value")` | Sets the interior fill used for subsequent filled shapes and points. Use `"none"` to disable filling. |
| `canvas.fillOpacity("value")` | Sets the fill opacity for subsequent shapes. Values are forwarded as SVG strings, so `"0.2"` makes the fill translucent. |
| `canvas.strokeOpacity("value")` | Sets the stroke opacity for subsequent shapes. |
| `canvas.strokeWidth(width)` | Sets the stroke width in pixels for subsequent shapes. |
| `canvas.pointRadius(radius)` | Sets the rendered radius of `Point` primitives in pixels for subsequent shapes. |

`strokeWidth` and `pointRadius` are lengths rather than colors, so they take
either an SVG length string (`"4"`) or a plain number (`4`). Like every other
style command they apply per shape: only the shapes drawn *after* the call
capture them.

Example:

```python
canvas = pgl.Canvas()
halfplane = pgl.Halfplane(0, 0, 4, 2)
rectangle = pgl.Rectangle(pgl.Point(1, 1), pgl.Point(3, 3))
# Soft fill for the half-plane so the rest of the drawing still shows through.
canvas.stroke("teal").fill("teal").fillOpacity("0.18").draw(halfplane)
# Then switch gears and draw the rectangle.
canvas.stroke("sienna").fill("gold").fillOpacity("0.22").draw(rectangle)
```

### Drawing shapes

`canvas.draw(shape)` adds a shape using the current style and returns the canvas,
so draws chain. Every bound shape can be drawn: `Point`, `Segment`,
`OrientedSegment`, `Line`, `OrientedLine`, `Ray`, `Halfplane`, `Triangle`,
`Rectangle`, `Convex`, `MonotoneChain`, `Polyline`, `Polygon`, and `Disk` — plus
`Triangulation` and `ShapeTree`. Results of constructions such as
`intersection` are concrete shapes too, so they can be drawn directly. Drawing
`None` (which an empty `intersection` returns) is a no-op that still returns the
canvas, so no `None` guard is needed.

```python
canvas = pgl.Canvas()
canvas.draw(pgl.Triangle(-1, -1, 0, 2, 1, -2)) \
      .draw(pgl.Disk(pgl.Point(0, 0), 2)) \
      .draw(pgl.Point(0, 0))
```

### Configuration

These methods configure the exported image or update the current drawing
defaults. Each returns the canvas, so they chain:

| Method | What it changes |
| --- | --- |
| `scale(factor)` | Multiplies the automatically fitted scale by `factor`. Values greater than `1` zoom in; values between `0` and `1` zoom out. Must be strictly positive. |
| `width(pixels)` | Sets the SVG width in pixels. Must be strictly positive. |
| `height(pixels)` | Sets the SVG height in pixels. Must be strictly positive. |
| `size(width, height)` | Convenience wrapper for setting width and height together. |
| `margin(pixels)` | Reserves blank space around the fitted drawing, giving the geometry more breathing room inside the image. Must be non-negative. |
| `borders(enabled=True)` | Enables or disables a thin rectangular frame around the whole drawing. Especially helpful when debugging clipping and margins. |

The invalid-argument checks raise a Python exception, so e.g. `canvas.width(0)`
raises rather than producing a broken image.

(`strokeWidth` and `pointRadius` used to live here, as canvas-wide numeric
settings. They are now per-shape [style](#style) commands.)

### Export formats

A canvas renders the same fitted drawing to three formats. Each `write*` method
returns `None` and raises if the file cannot be opened.

| Method | Result |
| --- | --- |
| `toSVG()` / `writeSVG(path)` | The SVG document, as a `str` / written to disk. |
| `toPDF()` / `writePDF(path)` | The PDF document. `toPDF()` returns `bytes`, not `str` — a PDF is binary. |
| `toIPE()` / `writeIPE(path)` | An [Ipe](https://ipe.otfried.org/) XML document, as a `str`. Ipe is a vector editor widely used in computational geometry, so this is the format to reach for when a figure is headed for a paper. |

```python
canvas = pgl.Canvas().size(300, 300)
canvas.stroke("crimson").draw(pgl.Disk(pgl.Point(0, 0), 2))
canvas.writeSVG("figure.svg")
canvas.writePDF("figure.pdf")
canvas.writeIPE("figure.ipe")
```

### Inline display in Jupyter

Every shape and every canvas defines `_repr_svg_`, the hook Jupyter / IPython use
for rich display. Evaluating a shape as the last expression in a cell draws it on
a one-shot canvas and shows the SVG inline:

```python
pgl.Triangle(-1, -1, 0, 2, 1, -2)        # displays the triangle
```

A shape is drawn on a one-shot canvas whose side length is `pypgl.REPR_SVG_SIZE`
pixels (500 by default, half pgl's 1000×1000, so a shape does not dominate the
cell). Reassign it to scale every inline shape — e.g. `pypgl.REPR_SVG_SIZE = 250`
for half again as small. A canvas you build yourself is unaffected: it honors its
own `size`.

A canvas displays itself the same way, so you do not need `toSVG()` to preview a
drawing in a notebook — just put the canvas on the last line of the cell:

```python
canvas = pgl.Canvas().size(300, 300)
canvas.stroke("crimson").draw(pgl.Disk(pgl.Point(0, 0), 2))
canvas                                    # displays the canvas
```

You can still call `canvas.toSVG()` to obtain the SVG string explicitly (for
tests, web responses, or your own output layer):

```python
canvas = pgl.Canvas()
canvas.stroke("black").draw(pgl.Segment(0, 0, 4, 3))
svg = canvas.toSVG()
```

### How fitting works

Canvas fitting is automatic:

- the bounds of all drawn elements are collected;
- the drawing is uniformly scaled to fit inside the chosen width and height;
- the aspect ratio is preserved;
- the configured margin and optional border are respected;
- the y-axis is flipped during export so that mathematical coordinates still feel
  natural while SVG receives screen-space coordinates.

Infinite primitives are clipped to the visible viewport:

- `Line` becomes the visible chord of the line inside the SVG box;
- `OrientedLine` behaves the same but keeps its orientation arrow;
- `Ray` starts at its source and stops at the first viewport boundary it meets;
- `Halfplane` is clipped to the viewport as a polygonal region.

The generated SVG uses `vector-effect="non-scaling-stroke"`, so stroke widths
stay visually constant even when the geometry is scaled to fit the output box.

### Notes

- `Canvas` is intentionally lightweight. It is a geometry inspection tool, not a
  general plotting framework.
- Shapes are stored in draw order, and SVG output preserves that order, so later
  shapes are drawn on top of earlier ones.
- Because style is captured when a shape is drawn, it is easy to layer highlights
  on top of a base drawing by switching style right before drawing the
  highlighted object.
- `Halfplane` fill and `Rectangle` fill are often easier to read when combined
  with a translucent `fillOpacity(...)`.
- `Triangle` supports both stroke and fill just like `Rectangle`.
