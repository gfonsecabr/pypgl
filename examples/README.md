# pypgl examples

The Python ports of pgl's [`examples/`](https://github.com/gfonsecabr/pgl/tree/main/examples),
one file each. Every one is a plain script with no arguments:

```bash
pip install pypgl
python example1.py
```

Most write an SVG (a couple also a PDF and an [Ipe](https://ipe.otfried.org/)
file) into the working directory. `make` runs them all, `make clean` removes
what they wrote.

| example | what it shows | output |
|---|---|---|
| [`example1.py`](example1.py) | `intersects` vs. `interiorsIntersect` — two shapes can meet without their interiors meeting | *(prints)* |
| [`example2.py`](example2.py) | Canvas styling and drawing; the style applies to shapes drawn *after* it | `example2.svg` |
| [`example3.py`](example3.py) | The iterated midpoint polygon, converging to an affine-regular shape over 100 exact iterations | `midpoint_polygon.svg` |
| [`example_canvas.py`](example_canvas.py) | A gallery of all twelve bounded shapes on a grid, including `PolygonWithHoles` and `HalfplaneIntersection` | `canvas_gallery.{svg,pdf,ipe}` |
| [`example_shapetree.py`](example_shapetree.py) | `ShapeTree` region queries, with the tree's own node boxes drawn underneath | `example_shapetree_{points,triangles}.svg` |
| [`example_triangulation.py`](example_triangulation.py) | The Delaunay triangulation of a point set, walked by a segment | `example_triangulation.svg` |
| [`example_triangulation2.py`](example_triangulation2.py) | A *constrained* Delaunay triangulation of a spiral corridor, whose mesh never crosses a wall | `example_triangulation2.svg` |

## Differences from the C++ originals

The examples follow pgl's line for line where they can. Three things necessarily
read differently:

**The canvas has methods, not a stream.** pgl's
`canvas << stroke("green") << shape` has no Python equivalent, so each stream
operation became a method. They return the canvas, so they still chain:

```python
canvas.stroke("green").fill("red").fillOpacity("25%").draw(shape)
```

**Coordinates are exact, and `float` is rejected.** pypgl binds only pgl's exact
rational instantiation, so coordinates are `int`, `fractions.Fraction`, or
`"a/b"` strings — never `float`. Where an example computes a layout with
trigonometry ([`example_triangulation2.py`](example_triangulation2.py)), it
rounds to `int` before building the shape rather than letting an approximation
in silently.

**The fixed-size shapes take flat coordinates; the variable-size ones do not.**
`Segment(0, 0, 8, 8)` and `Triangle(0, 0, 8, 0, 4, 8)` work as in C++, but
`Convex`, `Polygon`, `MonotoneChain` and `Polyline` want a sequence of `Point`.
[`example_canvas.py`](example_canvas.py) has a small `points(*coords)` helper for
the brace-list constructors the C++ originals use.

Random points are drawn with Python's `random` rather than C++'s `std::mt19937`,
so the pictures differ from pgl's in detail while showing the same thing.

## In a notebook

Every shape and canvas has a `_repr_svg_`, so a bare expression renders inline in
Jupyter without any of the file-writing above:

```python
import pypgl as pgl
pgl.Convex([pgl.Point(0, 0), pgl.Point(4, 0), pgl.Point(2, 3)])   # draws itself
```
