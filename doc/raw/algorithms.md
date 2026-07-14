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

## Algorithms

The algorithms are module-level functions (`pgl.convexHull(points)`, not a
method on a shape). Every one of them takes a plain Python list — of `Point` or
of `Segment` — and, like the shapes, computes exactly.

### Intersection of Line Segments

Given a list of $n$ segments, these functions report the pairs that meet.
*Intersecting* means the two segments share at least one point; *crossing* is the
stricter relation where each one passes from one side of the other to the other
side (a shared endpoint, or a collinear overlap, intersects but does not cross).

The reporting functions return a list of pairs, each pair a list of the two
`Segment` objects involved.

- `findIntersections(segments)`: All intersecting pairs, using the
  Bentley-Ottmann sweep line. Runs in $O((n+k) \log n)$ time for $k$ reported
  pairs.

- `findCrossings(segments)`: All crossing pairs, same sweep line and same
  $O((n+k) \log n)$ time.

- `bruteForceIntersections(segments)` / `bruteForceCrossings(segments)`: The same
  two results, computed by testing every pair. They take $O(n^2)$ time, but are
  faster in practice when the output is large.

- `detectIntersections(segments)` / `detectCrossings(segments)`: Return `True` as
  soon as one intersecting (respectively crossing) pair exists, in
  $O(n \log n)$ time, without reporting it.

```python
segments = [pgl.Segment(0, 0, 4, 4), pgl.Segment(0, 4, 4, 0), pgl.Segment(5, 0, 6, 0)]
for a, b in pgl.findIntersections(segments):
    print(a, "meets", b, "at", a.intersection(b))
# Output: (0,0)--(4,4) meets (0,4)--(4,0) at (2,2)
print(pgl.detectCrossings(segments))
# Output: True
```

These functions use the same predicate conventions documented in
[Predicates](shape_methods.md#predicates).

### Convex hull

- `convexHull(points)`: Returns the list of hull vertices in counterclockwise
  order, starting from the smallest (leftmost, breaking ties by lowest) point.
  Complexity $O(n \log n)$ for $n$ input points.

- `convexHullExtended(points)`: Returns the hull in the same order, but keeps the
  input points that lie in the interior of a hull edge instead of dropping them.
  Complexity $O(n \log n)$.

To get the hull as a shape rather than as a list of points, construct a
[`Convex`](shapes.md#convex) directly: `pgl.Convex(points)` computes the hull.

### Sorting points

Both of these reorder the Python list you pass **in place** and return `None`,
like `list.sort` does.

- `sortAround(points, p)`: Reorders `points` counterclockwise around the center
  `p`, starting from the lexicographically smallest point and breaking ties by
  putting farther points first. Connecting the result in order traces a simple
  star-shaped polygon whose kernel contains `p`. Relies only on exact orientation
  and squared-distance comparisons. Complexity $O(n \log n)$.

- `hilbertSort(points)`: Reorders `points` along a Hilbert space-filling curve,
  so points close in the plane stay close in the sequence — a useful
  preprocessing step for incremental algorithms such as
  [`Triangulation.insertDelaunay`](data_structures.md#triangulation). Uses only
  coordinate comparisons. Complexity $O(n \log n)$.

```python
points = [pgl.Point(1, 1), pgl.Point(-1, 1), pgl.Point(0, -1)]
pgl.sortAround(points, pgl.Point(0, 0))
print(points)
# Output: [(-1,1), (0,-1), (1,1)]
```

### Polyominoes

- `polyominoes(size)`: Returns one [`Polygon`](shapes.md#polygon) per free
  polyomino of `size` cells (counted up to translation, rotation, and
  reflection). Each polygon traces the polyomino boundary with small
  non-negative integer coordinates. Polyominoes that enclose a hole (possible
  from seven cells onward) are omitted, since their boundary is not a simple
  polygon.

- `polyominoes(n1, n2)`: Returns the free polyominoes of every size in
  `[n1, n2]`, smallest first.

- `polyominoesUpTo(n)`: Returns the free polyominoes of every size from `1` to
  `n`, smallest first.

```python
print(len(pgl.polyominoes(5)))   # the 12 pentominoes
# Output: 12
```
