<!-- AUTO-GENERATED from doc/raw/canvas.md by doc/raw/doxylink.py — do not edit; edit the raw version and regenerate. -->

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

[`Canvas`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html "Stores drawable objects and exports them as an SVG image.") is a lightweight renderer for Pangolin shapes. It is designed for
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
| [`canvas.stroke("value")`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a2e234c901f9abf59d6a354cdc9a9168f "Creates a command that changes the current stroke color.") | Sets the stroke color or stroke paint used for subsequent shapes. Typical values are color names such as `"red"`, hex codes such as `"#3366cc"`, or any SVG paint value. |
| [`canvas.fill("value")`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ac8cbf973d67ef1569c611788f93f6761 "Creates a command that changes the current fill color.") | Sets the interior fill used for subsequent filled shapes and points. Use `"none"` to disable filling. |
| [`canvas.fillOpacity("value")`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a8cf94a6c54fd68e2972ff7440eca978b "Creates a command that changes the current fill opacity.") | Sets the fill opacity for subsequent shapes. Values are forwarded as SVG strings, so `"0.2"` makes the fill translucent. |
| [`canvas.strokeOpacity("value")`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a7c60899586c30e2ea3c3aacfc192228e "Creates a command that changes the current stroke opacity.") | Sets the stroke opacity for subsequent shapes. |
| [`canvas.strokeWidth(width)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a49586374ddc1970a6253da193b279526 "Creates a command that changes the current stroke width.") | Sets the stroke width in pixels for subsequent shapes. |
| [`canvas.pointRadius(radius)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a1e29fcb65cc1bf621121dac846204aeb "Creates a command that changes the current point radius.") | Sets the rendered radius of [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload.") primitives in pixels for subsequent shapes. |

[`strokeWidth`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a49586374ddc1970a6253da193b279526 "Creates a command that changes the current stroke width.") and [`pointRadius`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a1e29fcb65cc1bf621121dac846204aeb "Creates a command that changes the current point radius.") are lengths rather than colors, so they take
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
so draws chain. Every bound shape can be drawn: [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload."), [`Segment`](https://gfonsecabr.github.io/pgl/structpgl_1_1Segment.html "Unoriented closed segment between two endpoints plus optional segment label."),
[`OrientedSegment`](https://gfonsecabr.github.io/pgl/structpgl_1_1OrientedSegment.html "Directed segment preserving source-to-target order plus optional segment label."), [`Line`](https://gfonsecabr.github.io/pgl/structpgl_1_1Line.html "Unoriented infinite line."), [`OrientedLine`](https://gfonsecabr.github.io/pgl/structpgl_1_1OrientedLine.html "Directed infinite line with left/right side semantics plus optional line label."), [`Ray`](https://gfonsecabr.github.io/pgl/structpgl_1_1Ray.html "Half-infinite line starting from one source point plus optional ray label."), [`Halfplane`](https://gfonsecabr.github.io/pgl/structpgl_1_1Halfplane.html "Closed half-plane defined by an oriented boundary line."), [`Triangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangle.html "Closed triangle stored by three vertices."),
[`Rectangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Rectangle.html "Axis-aligned rectangle stored by minimum and maximum corners."), [`Convex`](https://gfonsecabr.github.io/pgl/structpgl_1_1Convex.html "Closed convex polygon stored by its vertices."), [`MonotoneChain`](https://gfonsecabr.github.io/pgl/structpgl_1_1MonotoneChain.html "Weakly x-monotone polyline stored by lexicographically sorted vertices."), [`Polyline`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polyline.html "Open polygonal chain stored in traversal order; may self-intersect."), [`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices."), and [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label.") — plus
[`Triangulation`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangulation.html "Triangulation whose connectivity may change and whose vertex set may grow.") and [`ShapeTree`](https://gfonsecabr.github.io/pgl/classpgl_1_1ShapeTree.html "Static shape tree of bounded shapes."). Results of constructions such as
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
| [`scale(factor)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a40b9eaa91fa720483a2999d09e89e47b "Sets the global zoom factor used during SVG export.") | Multiplies the automatically fitted scale by `factor`. Values greater than `1` zoom in; values between `0` and `1` zoom out. Must be strictly positive. |
| [`width(pixels)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#ae77d195e33e5becef12de273bd327f51 "Sets the exported SVG width in pixels.") | Sets the SVG width in pixels. Must be strictly positive. |
| [`height(pixels)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a8256fca52537707a7288cd82a42f016c "Sets the exported SVG height in pixels.") | Sets the SVG height in pixels. Must be strictly positive. |
| [`size(width, height)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#ab56282ffe4990051d30b69a0468e2394 "Sets the exported SVG size in pixels.") | Convenience wrapper for setting width and height together. |
| [`margin(pixels)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#ac5d887cdc706ea1473bebdda02c2390d "Sets the margin reserved around the fitted drawing.") | Reserves blank space around the fitted drawing, giving the geometry more breathing room inside the image. Must be non-negative. |
| [`borders(enabled=True)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a6621826426cfa82bd0b5fd8221b7376b "Enables or disables the optional border around the SVG.") | Enables or disables a thin rectangular frame around the whole drawing. Especially helpful when debugging clipping and margins. |

The invalid-argument checks raise a Python exception, so e.g. [`canvas.width(0)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#ae77d195e33e5becef12de273bd327f51 "Sets the exported SVG width in pixels.")
raises rather than producing a broken image.

([`strokeWidth`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a49586374ddc1970a6253da193b279526 "Creates a command that changes the current stroke width.") and [`pointRadius`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a1e29fcb65cc1bf621121dac846204aeb "Creates a command that changes the current point radius.") used to live here, as canvas-wide numeric
settings. They are now per-shape [style](#style) commands.)

### Export formats

A canvas renders the same fitted drawing to three formats. Each `write*` method
returns `None` and raises if the file cannot be opened.

| Method | Result |
| --- | --- |
| [`toSVG()`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a9d02568a8bf29a1d7c7638a1186a9f14 "Serializes the canvas contents to an SVG string.") / [`writeSVG(path)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#ade8bd4b3d2c895f3659aa101552e3031 "Serializes the canvas to an SVG file.") | The SVG document, as a `str` / written to disk. |
| [`toPDF()`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#aba98293b6bb5b0f48390b75ef4c3499a "Serializes the canvas contents to a PDF byte string.") / [`writePDF(path)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#adcaf7407be62f98643ed1a5071883ab3 "Serializes the canvas to a PDF file.") | The PDF document. [`toPDF()`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#aba98293b6bb5b0f48390b75ef4c3499a "Serializes the canvas contents to a PDF byte string.") returns `bytes`, not `str` — a PDF is binary. |
| [`toIPE()`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a39f0d14964126ee113728583b5bd9da9 "Serializes the canvas contents to an Ipe XML string.") / [`writeIPE(path)`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a205567fff67ef15a96e959be8327dfc2 "Serializes the canvas to an Ipe XML file (.ipe).") | An [Ipe](https://ipe.otfried.org/) XML document, as a `str`. Ipe is a vector editor widely used in computational geometry, so this is the format to reach for when a figure is headed for a paper. |

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
own [`size`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#ab56282ffe4990051d30b69a0468e2394 "Sets the exported SVG size in pixels.").

A canvas displays itself the same way, so you do not need [`toSVG()`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a9d02568a8bf29a1d7c7638a1186a9f14 "Serializes the canvas contents to an SVG string.") to preview a
drawing in a notebook — just put the canvas on the last line of the cell:

```python
canvas = pgl.Canvas().size(300, 300)
canvas.stroke("crimson").draw(pgl.Disk(pgl.Point(0, 0), 2))
canvas                                    # displays the canvas
```

You can still call [`canvas.toSVG()`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html#a9d02568a8bf29a1d7c7638a1186a9f14 "Serializes the canvas contents to an SVG string.") to obtain the SVG string explicitly (for
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

- [`Line`](https://gfonsecabr.github.io/pgl/structpgl_1_1Line.html "Unoriented infinite line.") becomes the visible chord of the line inside the SVG box;
- [`OrientedLine`](https://gfonsecabr.github.io/pgl/structpgl_1_1OrientedLine.html "Directed infinite line with left/right side semantics plus optional line label.") behaves the same but keeps its orientation arrow;
- [`Ray`](https://gfonsecabr.github.io/pgl/structpgl_1_1Ray.html "Half-infinite line starting from one source point plus optional ray label.") starts at its source and stops at the first viewport boundary it meets;
- [`Halfplane`](https://gfonsecabr.github.io/pgl/structpgl_1_1Halfplane.html "Closed half-plane defined by an oriented boundary line.") is clipped to the viewport as a polygonal region.

The generated SVG uses `vector-effect="non-scaling-stroke"`, so stroke widths
stay visually constant even when the geometry is scaled to fit the output box.

### Notes

- [`Canvas`](https://gfonsecabr.github.io/pgl/classpgl_1_1Canvas.html "Stores drawable objects and exports them as an SVG image.") is intentionally lightweight. It is a geometry inspection tool, not a
  general plotting framework.
- Shapes are stored in draw order, and SVG output preserves that order, so later
  shapes are drawn on top of earlier ones.
- Because style is captured when a shape is drawn, it is easy to layer highlights
  on top of a base drawing by switching style right before drawing the
  highlighted object.
- [`Halfplane`](https://gfonsecabr.github.io/pgl/structpgl_1_1Halfplane.html "Closed half-plane defined by an oriented boundary line.") fill and [`Rectangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Rectangle.html "Axis-aligned rectangle stored by minimum and maximum corners.") fill are often easier to read when combined
  with a translucent [`fillOpacity(...)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a8cf94a6c54fd68e2972ff7440eca978b "Creates a command that changes the current fill opacity.").
- [`Triangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangle.html "Closed triangle stored by three vertices.") supports both stroke and fill just like [`Rectangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Rectangle.html "Axis-aligned rectangle stored by minimum and maximum corners.").
