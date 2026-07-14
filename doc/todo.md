<img align="left" src="figures/logo.png" width="23%"/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/logotextdark.svg"/>
  <img alt="Pangolin: Plane Geometry Library" src="figures/logotext.svg" width="65%"/>
</picture>

[![Tests](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml/badge.svg)](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml)
[![Standard](https://img.shields.io/badge/C%2B%2B-20/23/26-rgb(10,66,158).svg)](https://en.wikipedia.org/wiki/C%2B%2B#Standardization)
[![License](https://img.shields.io/badge/license-MIT-rgb(216,134,42).svg)](https://opensource.org/licenses/MIT)
[![Benchmarks](https://img.shields.io/badge/benchmarks-online-rgb(21,153,135).svg)](https://gfonsecabr.github.io/pgl/benchmarks/index.html)

<br/>

⚠️ **Work in Progress**: This library is still under construction and contains **bugs and missing features**. Use in production environments is not recommended.

## Missing Features

The 1-dimensional chains that used to be listed here are now implemented: an
arbitrary, possibly self-intersecting chain is [`Polyline`](shapes.md#polyline),
and the x-monotone one (formerly called `PolyFunction`) is
[`MonotoneChain`](shapes.md#monotonechain).

- `intersection` between two 2-dimensional shapes among `Triangle`, `Rectangle`, and `Convex`.
- `intersection` of a chain (`Polyline`, `MonotoneChain`) with a `Disk` or a `Polygon`.
- `distanceL1` / `distanceLInf` to and from a `Disk`, which pgl implements only against a `Point` so far.
- Hausdorff distance for the non-convex shapes (`Polygon`, `Polyline`, `MonotoneChain`) and for `Disk`.

## Data Structures Not Yet Implemented

### Grid

### Fair-Split Tree

