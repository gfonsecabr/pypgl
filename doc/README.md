<!-- AUTO-GENERATED from doc/raw/README.md by doc/raw/doxylink.py — do not edit; edit the raw version and regenerate. -->

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

`pypgl` is the Python interface to [Pangolin](https://github.com/gfonsecabr/pgl)
(or `pgl`), a library for exact computational geometry in the plane.

```bash
pip install pypgl
```

This folder documents the Python API. Start with the [top-level
README](../README.md) for a tour, then:

- [shapes.md](shapes.md) — every shape, from [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload.") and [`Segment`](https://gfonsecabr.github.io/pgl/structpgl_1_1Segment.html "Unoriented closed segment between two endpoints plus optional segment label.") to [`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices."),
  [`Disk`](https://gfonsecabr.github.io/pgl/structpgl_1_1Disk.html "Closed Euclidean disk stored by boundary points plus optional disk label.") and the polygonal chains.
- [shape_methods.md](shape_methods.md) — what every shape can do: the
  [predicates](shape_methods.md#predicates), operators, affine
  [transformations](shape_methods.md#transformations), intersections, distances,
  and iteration.
- [algorithms.md](algorithms.md) — convex hull, segment intersection, smallest
  enclosing disk, closest pair, visibility, point sorting, polyominoes.
- [data_structures.md](data_structures.md) — [`ShapeTree`](https://gfonsecabr.github.io/pgl/classpgl_1_1ShapeTree.html "Static shape tree of bounded shapes."), [`IntervalTree`](https://gfonsecabr.github.io/pgl/classpgl_1_1IntervalTree.html "Mutable interval tree over the projection of bounded shapes."),
  [`Triangulation`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangulation.html "Triangulation whose connectivity may change and whose vertex set may grow."), [`Arrangement`](https://gfonsecabr.github.io/pgl/classpgl_1_1Arrangement.html "The planar subdivision induced by a set of one-dimensional shapes.") and [`Graph`](https://gfonsecabr.github.io/pgl/classpgl_1_1Graph.html "Undirected simple graph stored as adjacency sets.").
- [canvas.md](canvas.md) — drawing shapes and exporting them as SVG, PDF or Ipe,
  including inline display in a Jupyter notebook.
- [todo.md](todo.md) — what is not implemented yet.

Coordinates are **exact**: a single arbitrary-precision rational number type is
used throughout, so there is nothing to choose and no rounding to worry about.
They are given as Python `int`, `fractions.Fraction`, or `"a/b"` strings, and
come back as `Fraction`. A `float` coordinate is rejected rather than silently
approximated: there is no inexact number type to fall back to.
