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
(or `pgl`), a C++ library for computational geometry algorithms in the plane. The
API mirrors the C++ one, so the class and method names are the same.

```bash
pip install pypgl
```

This folder documents the Python API. Start with the [top-level
README](../README.md) for a tour, then:

- [shapes.md](shapes.md) — every shape, from `Point` and `Segment` to `Polygon`,
  `Disk` and the polygonal chains.
- [shape_methods.md](shape_methods.md) — what every shape can do: the
  [predicates](shape_methods.md#predicates), operators, affine
  [transformations](shape_methods.md#transformations), intersections, distances,
  and iteration.
- [algorithms.md](algorithms.md) — convex hull, segment intersection, point
  sorting, polyominoes.
- [data_structures.md](data_structures.md) — `ShapeTree` and `Triangulation`.
- [canvas.md](canvas.md) — drawing shapes and exporting them as SVG, PDF or Ipe,
  including inline display in a Jupyter notebook.
- [todo.md](todo.md) — what is not implemented yet.

Coordinates are **exact**: a single arbitrary-precision rational number type is
used throughout, so there is nothing to choose and no rounding to worry about.
They are given as Python `int`, `fractions.Fraction`, or `"a/b"` strings, and
come back as `Fraction`. A `float` coordinate is rejected rather than silently
approximated — the C++ library's `double` and fixed-width instantiations are
deliberately not exposed.
