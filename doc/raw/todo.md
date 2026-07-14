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

- `intersection` between two 2-dimensional shapes among `Triangle`, `Rectangle`, and `Convex`.
- `intersection` of a chain (`Polyline`, `MonotoneChain`) with a `Disk` or a `Polygon`.
- `distanceL1` / `distanceLInf` to and from a `Disk`, which pgl implements only against a `Point` so far.
- Hausdorff distance for the non-convex shapes (`Polygon`, `Polyline`, `MonotoneChain`) and for `Disk`.

The 1-dimensional chains that used to be listed here are now implemented: an
arbitrary, possibly self-intersecting chain is [`Polyline`](shapes.md#polyline),
and the x-monotone one (formerly called `PolyFunction`) is
[`MonotoneChain`](shapes.md#monotonechain).

## Deliberately Not Exposed

A few things exist in the C++ library but are left out of the Python API on
purpose, and are not expected to arrive:

- **Other number types.** Only the exact arbitrary-precision rational
  instantiation is bound, which is what keeps the API (and the binary) small.
  This is also why an arbitrary-angle `Transformation.rotation(radians)` and
  `Disk.fbox()` are missing: both exist only in a floating-point flavor.
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

