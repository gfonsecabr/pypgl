<img align="left" src="https://raw.githubusercontent.com/gfonsecabr/pypgl/main/doc/figures/logo.png" width="23%"/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/gfonsecabr/pypgl/main/doc/figures/logotextdark.svg"/>
  <img alt="Pangolin: Plane Geometry Library" src="https://raw.githubusercontent.com/gfonsecabr/pypgl/main/doc/figures/logotext.svg" width="65%"/>
</picture>

<!-- [![Tests](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml/badge.svg)](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml)
[![Standard](https://img.shields.io/badge/C%2B%2B-20/23/26-rgb(10,66,158).svg)](https://en.wikipedia.org/wiki/C%2B%2B#Standardization) -->
[![License](https://img.shields.io/badge/license-MIT-rgb(216,134,42).svg)](https://opensource.org/licenses/MIT)
<!-- [![Benchmarks](https://img.shields.io/badge/benchmarks-online-rgb(21,153,135).svg)](https://gfonsecabr.github.io/pgl/benchmarks/index.html) -->

⚠️ **Work in Progress**: This library is still under construction and contains **bugs and missing features**. Use in production environments is not recommended.

[Pangolin](https://github.com/gfonsecabr/pgl) (or `pgl`) is a C++ library for computational geometry in the plane and `pypgl` is the **official python binding** for it. It is designed to be pleasant to use and always exact. Calculations are **exact using rational numbers** (floating point is not accepted).

```python
import pypgl as pgl

p = pgl.Point(1, 0)
q = pgl.Point(4, '15/2')
s = pgl.Segment(p, q)
t = pgl.Segment(0, 8, '7/3', 1)
if s.intersects(t):
    print(s, "intersects", t)
# Output: (1,0)--(4,15/2) intersects (0,8)--(7/3,1)
```

## Shapes and Predicates

| Family | Shapes |
| --- | --- |
| 0-dimensional | [`Point`](doc/shapes.md#point) |
| 1-dimensional | [`Segment`](doc/shapes.md#segment), [`OrientedSegment`](doc/shapes.md#oriented-segment), [`Line`](doc/shapes.md#line), [`OrientedLine`](doc/shapes.md#oriented-line), [`Ray`](doc/shapes.md#ray), [`Polyline`](doc/shapes.md#polyline), [`MonotoneChain`](doc/shapes.md#monotonechain) |
| 2-dimensional | [`Halfplane`](doc/shapes.md#half-plane), [`Triangle`](doc/shapes.md#triangle), [`Rectangle`](doc/shapes.md#rectangle), [`Disk`](doc/shapes.md#disk), [`Convex`](doc/shapes.md#convex), [`Polygon`](doc/shapes.md#polygon) |

The following [predicates](doc/shape_methods.md#predicates) are implemented as methods of all shapes.

- `contains(Shape)` Does it contain the other shape?
- `boundaryContains(Shape)` Does its boundary contain the other shape?
- `interiorContains(Shape)` Does it contain the other shape in the interior?
- `intersects(Shape)` Do the two shapes intersect?
- `interiorsIntersect(Shape)` Do the interiors of the two shapes intersect?
- `separates(Shape)` Does one shape cut the other into two (or more) components?
- `crosses(Shape)` Do both shapes separate each other?

```python
import pypgl as pgl

o = pgl.Point()      # Point (0,0)
d = pgl.Disk(o, 10)  # Disk of radius 10 centered at (0,0)
if d.contains(o):
    print("Disk contains", o)
diam = d.diameter()
if d.contains(diam):
    print("Disk contains the diameter")
if not d.interiorContains(diam):
    print("Disk's interior does not contain the diameter")
# Output:
# Disk contains (0,0)
# Disk contains the diameter
# Disk's interior does not contain the diameter
```

## Other Methods

Several [other methods](doc/shape_methods.md) are supported by the shapes.

```python
import pypgl as pgl

c = pgl.Convex([pgl.Point(0, 0), pgl.Point(1, 0), pgl.Point(1, 2), pgl.Point(0, 1)])
s = c.diameter()
print("The diameter of", c,
      "is defined by", s,
      "and has length", s.length())
# Output: The diameter of Convex[(0,0),(1,0),(1,2),(0,1)] is defined by (0,0)--(1,2) and has length 2.23607
```

## Visualization

A `Canvas` class is provided for [visualization](doc/canvas.md), exporting to SVG, PDF, or [Ipe](https://ipe.otfried.org/):

<img align="right" src="https://raw.githubusercontent.com/gfonsecabr/pypgl/main/doc/figures/example2.svg" width="200"/>

```python
import pypgl as pgl

canvas = pgl.Canvas()
canvas.draw(pgl.Point(0, 0))

tri = pgl.Triangle(-1, -1, 0, 2, 1, -2)
canvas.stroke("green")
canvas.draw(tri)
canvas.stroke("blue")
canvas.draw(2*tri)
canvas.writeSVG("example2.svg")
```


## Algorithms and Data Structures

<img align="right" src="https://raw.githubusercontent.com/gfonsecabr/pypgl/main/doc/figures/example_triangulation.svg" width="200"/>

PGL includes [fundamental algorithms](doc/algorithms.md) and [data structures](doc/data_structures.md) such as:

- Convex hull: computed with Graham scan.
- Line segment intersection: Bentley-Ottmann sweep line using rational numbers.
- Sort points: by angle or Hilbert order.
- Kd-tree: for points and a generalization for other bounded shapes.
- Triangulation: including Delaunay and constrained Delaunay triangulations for points and polygons.


## Installation

`pypgl` requires **Python 3.9 or newer**.

### From PyPI

```bash
pip install pypgl
```

Pre-built wheels are published for CPython 3.9–3.13 on Linux (`manylinux_2_28`,
x86_64), macOS (Apple Silicon), and Windows, so most users need no compiler.

### From source

Installing from a source tree or directly from GitHub builds the extension
locally and therefore needs a **C++20 compiler** (GCC 12+, Clang 15+, or, on
Windows, the LLVM/ClangCL toolset). The header-only `pgl` library is fetched
automatically by CMake — nothing else to install.

```bash
pip install git+https://github.com/gfonsecabr/pypgl.git
```

### Development install

Work on the bindings from a checkout with an editable, in-place build:

```bash
git clone https://github.com/gfonsecabr/pypgl.git
cd pypgl
python3 -m venv .venv
.venv/bin/pip install scikit-build-core nanobind pytest
.venv/bin/pip install -e . --no-build-isolation
.venv/bin/python -m pytest tests/ -q
```

`--no-build-isolation` lets CMake find the venv's `nanobind`. Re-run the
`pip install -e .` step after editing any `src/*.cpp`, since the editable
install is what rebuilds the extension. To build against a local `pgl` checkout
instead of the pinned upstream commit:

```bash
.venv/bin/pip install -e . --no-build-isolation \
  -C cmake.define.PGL_INCLUDE_DIR=/path/to/pgl/include
```

## More Information

- For a brief description, check the documents at the [doc folder](doc/).
- For some simple examples, check the files at the [examples folder](examples/).
- Check the [C++ version](https://github.com/gfonsecabr/pgl).

