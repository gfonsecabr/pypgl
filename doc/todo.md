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

These operations are not implemented yet:

- `intersection` of a chain ([`Polyline`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polyline.html "Open polygonal chain stored in traversal order; may self-intersect."), [`MonotoneChain`](https://gfonsecabr.github.io/pgl/structpgl_1_1MonotoneChain.html "Weakly x-monotone polyline stored by lexicographically sorted vertices.")) with a [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label."), and of
  any shape with a [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label.") other than a [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload.").
- `minkowskiSum` of a [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label.") with anything but a [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload."), another [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label.") or a
  [`Halfplane`](https://gfonsecabr.github.io/pgl/structpgl_1_1Halfplane.html "Closed half-plane defined by an oriented boundary line."), and of an unbounded shape with a non-convex one.
- `distanceL1` / `distanceLInf` to and from a [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label."), which is implemented only
  against a [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload.") so far.
- Hausdorff distance for the non-convex shapes ([`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices."), [`PolygonWithHoles`](https://gfonsecabr.github.io/pgl/structpgl_1_1PolygonWithHoles.html "Closed region bounded by one outer simple polygon minus disjoint polygonal holes."),
  [`PolygonSet`](https://gfonsecabr.github.io/pgl/structpgl_1_1PolygonSet.html "Set of closed regions with pairwise disjoint interiors."), [`Polyline`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polyline.html "Open polygonal chain stored in traversal order; may self-intersect."), [`MonotoneChain`](https://gfonsecabr.github.io/pgl/structpgl_1_1MonotoneChain.html "Weakly x-monotone polyline stored by lexicographically sorted vertices.")), for [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label."), and for the
  possibly-unbounded [`HalfplaneIntersection`](https://gfonsecabr.github.io/pgl/structpgl_1_1HalfplaneIntersection.html "Intersection of closed half-planes; convex but possibly unbounded or empty.").

Several entries that used to be here have since arrived: the two chains
[`Polyline`](shapes.md#polyline) and [`MonotoneChain`](shapes.md#monotonechain),
the two regions [`PolygonWithHoles`](shapes.md#polygon-with-holes) and
[`PolygonSet`](shapes.md#polygon-set), the convex
[`HalfplaneIntersection`](shapes.md#halfplane-intersection), the full
two-dimensional [`intersection`](shape_methods.md#intersection) grid, the
Minkowski sums of the chains and of the unbounded shapes, and
[`regularizedUnionOf`](algorithms.md#boolean-operations-and-minkowski-sum) over a
range of any of the six bounded region types.

## Deliberately Not Exposed

A few things are left out of the Python API on purpose, and are not expected to
arrive:

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

[`Arrangement`](data_structures.md#arrangement) and
[`Graph`](data_structures.md#graph) used to be listed here; both are now bound,
along with [`IntervalTree`](data_structures.md#interval-tree).

