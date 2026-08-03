<!-- AUTO-GENERATED from doc/raw/todo.md by doc/raw/doxylink.py — do not edit; edit the raw version and regenerate. -->

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

## Missing Features

These are gaps in the underlying C++ library, so they are missing here too:

- `intersection` between two 2-dimensional shapes among [`Triangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangle.html "Closed triangle stored by three vertices."), [`Rectangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Rectangle.html "Axis-aligned rectangle stored by minimum and maximum corners."), and [`Convex`](https://gfonsecabr.github.io/pgl/structpgl_1_1Convex.html "Closed convex polygon stored by its vertices.").
- `intersection` of a chain ([`Polyline`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polyline.html "Open polygonal chain stored in traversal order; may self-intersect."), [`MonotoneChain`](https://gfonsecabr.github.io/pgl/structpgl_1_1MonotoneChain.html "Weakly x-monotone polyline stored by lexicographically sorted vertices.")) with a [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label.") or a [`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices.").
- `minkowskiSum` of two chains (`polyline + polyline`), and of a [`MonotoneChain`](https://gfonsecabr.github.io/pgl/structpgl_1_1MonotoneChain.html "Weakly x-monotone polyline stored by lexicographically sorted vertices.") receiver — convert with `asPolyline()` for the latter.
- `distanceL1` / `distanceLInf` to and from a [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label."), which pgl implements only against a [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload.") so far.
- Hausdorff distance for the non-convex shapes ([`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices."), [`PolygonWithHoles`](https://gfonsecabr.github.io/pgl/structpgl_1_1PolygonWithHoles.html "Closed region bounded by one outer simple polygon minus disjoint polygonal holes."), [`Polyline`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polyline.html "Open polygonal chain stored in traversal order; may self-intersect."), [`MonotoneChain`](https://gfonsecabr.github.io/pgl/structpgl_1_1MonotoneChain.html "Weakly x-monotone polyline stored by lexicographically sorted vertices.")), for [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label."), and for the possibly-unbounded [`HalfplaneIntersection`](https://gfonsecabr.github.io/pgl/structpgl_1_1HalfplaneIntersection.html "Intersection of closed half-planes; convex but possibly unbounded or empty.").

The 1-dimensional chains that used to be listed here are now implemented: an
arbitrary, possibly self-intersecting chain is [`Polyline`](shapes.md#polyline),
and the x-monotone one (formerly called `PolyFunction`) is
[`MonotoneChain`](shapes.md#monotonechain). Two 2-dimensional shapes have since
joined them: [`PolygonWithHoles`](shapes.md#polygon-with-holes), which is what
the [boolean operations](shape_methods.md#boolean-operations) and the non-convex
[Minkowski sum](shape_methods.md#minkowski-sum) return, and
[`HalfplaneIntersection`](shapes.md#halfplane-intersection).

## Deliberately Not Exposed

A few things exist in the C++ library but are left out of the Python API on
purpose, and are not expected to arrive:

- **Other number types.** Only the exact arbitrary-precision rational
  instantiation is bound, which is what keeps the API (and the binary) small.
  This is also why an arbitrary-angle `Transformation.rotation(radians)`,
  `Disk.fbox()` and `HalfplaneIntersection.fbox()` are missing: all exist only in
  a floating-point flavor.
- **Callback-based traversals** (`visitTriangles…`, `visitIntersecting`, …). Every
  traversal here returns a list instead, which is what a Python caller wants
  anyway.
- **The `Shape` variant.** Each shape is its own Python class. The one place a
  mixed-type container is needed, [`ShapeTree`](data_structures.md#shape-tree),
  simply accepts any shape.

## Data Structures Not Yet Implemented

### Grid

### Arrangement

### Graph

