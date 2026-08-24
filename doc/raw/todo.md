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

- `intersection` of a chain (`Polyline`, `MonotoneChain`) with a `Disk`, and of
  any shape with a `Disk` other than a `Point`.
- `minkowskiSum` and `minkowskiErosion` of a `Disk` with anything but a `Point`,
  another `Disk` or a `Halfplane`, and of an unbounded shape with a non-convex
  one. The `Disk`-with-`Halfplane` pair is bound but has no exact answer either
  way: sliding a boundary by a radius moves it along that boundary's own *unit*
  normal, which is a square root even when the radius is exact.
- `distanceL1` / `distanceLInf` to and from a `Disk`, which is implemented only
  against a `Point` so far.
- Hausdorff distance for the non-convex shapes (`Polygon`, `PolygonWithHoles`,
  `PolygonSet`, `Polyline`, `MonotoneChain`), for `Disk`, and for the
  possibly-unbounded `HalfplaneIntersection`.

Several entries that used to be here have since arrived: the two chains
[`Polyline`](shapes.md#polyline) and [`MonotoneChain`](shapes.md#monotonechain),
the two regions [`PolygonWithHoles`](shapes.md#polygon-with-holes) and
[`PolygonSet`](shapes.md#polygon-set), the convex
[`HalfplaneIntersection`](shapes.md#halfplane-intersection), the full
two-dimensional [`intersection`](shape_methods.md#intersection) grid, the
Minkowski sums of the chains and of the unbounded shapes,
[`regularizedUnionOf`](algorithms.md#boolean-operations-minkowski-sums-and-erosions)
over a range of any of the six bounded region types, and the whole
[`minkowskiErosion`](shape_methods.md#minkowski-erosion) family.

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

