<!-- AUTO-GENERATED from doc/raw/algorithms.md by doc/raw/doxylink.py — do not edit; edit the raw version and regenerate. -->

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

The algorithms are module-level functions ([`pgl.convexHull(points)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a3999bfdf73609b7ec708a4882fcaea2f "Computes the convex hull of a point container."), not a
method on a shape). Every one of them takes a plain Python list — of [`Point`](https://gfonsecabr.github.io/pgl/structpgl_1_1Point.html "Two-dimensional point with optional label payload.") or
of [`Segment`](https://gfonsecabr.github.io/pgl/structpgl_1_1Segment.html "Unoriented closed segment between two endpoints plus optional segment label.") — and, like the shapes, computes exactly.

### Intersection of Line Segments

Given a list of $n$ segments, these functions report the pairs that meet.
*Intersecting* means the two segments share at least one point; *crossing* is the
stricter relation where each one passes from one side of the other to the other
side (a shared endpoint, or a collinear overlap, intersects but does not cross).

The reporting functions return a list of pairs, each pair a list of the two
[`Segment`](https://gfonsecabr.github.io/pgl/structpgl_1_1Segment.html "Unoriented closed segment between two endpoints plus optional segment label.") objects involved.

- [`findIntersections(segments)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#adcd493466342b027a48fe7bf0718434b "Finds all intersecting segment pairs with Bentley-Ottmann."): All intersecting pairs, using the
  Bentley-Ottmann sweep line. Runs in $O((n+k) \log n)$ time for $k$ reported
  pairs.

- [`findCrossings(segments)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#abf691f267558aaeea543045e723d292e "Finds all proper crossing segment pairs with Bentley-Ottmann."): All crossing pairs, same sweep line and same
  $O((n+k) \log n)$ time.

- [`bruteForceIntersections(segments)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a390afa6b90488531f4702bc242322d46 "Finds all intersecting segment pairs by brute force.") / [`bruteForceCrossings(segments)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#aac3ae3a0e91834aef9525388948417c4 "Finds all crossing segment pairs by brute force."): The same
  two results, computed by testing every pair. They take $O(n^2)$ time, but are
  faster in practice when the output is large.

- [`detectIntersections(segments)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#adea0ebb84e7d7ada3ae27ae23ea116bc "Detects whether any two segments intersect.") / [`detectCrossings(segments)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ade9af54c89044d728daf207e9c534759 "Detects whether any two segments properly cross."): Return `True` as
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

- [`convexHull(points)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a3999bfdf73609b7ec708a4882fcaea2f "Computes the convex hull of a point container."): Returns the list of hull vertices in counterclockwise
  order, starting from the smallest (leftmost, breaking ties by lowest) point.
  Complexity $O(n \log n)$ for $n$ input points.

- [`convexHullExtended(points)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ace788332cf5ee8db888decfb08383cda "Computes the convex hull of a point container."): Returns the hull in the same order, but keeps the
  input points that lie in the interior of a hull edge instead of dropping them.
  Complexity $O(n \log n)$.

To get the hull as a shape rather than as a list of points, construct a
[`Convex`](shapes.md#convex) directly: `pgl.Convex(points)` computes the hull.
Every bounded shape also carries its own [`convexHull()`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a3999bfdf73609b7ec708a4882fcaea2f "Computes the convex hull of a point container."), which answers a
[`Convex`](https://gfonsecabr.github.io/pgl/structpgl_1_1Convex.html "Closed convex polygon stored by its vertices.") covering the same points — see
[shape methods](shape_methods.md#convex-hull).

### Smallest enclosing disk

- [`smallestEnclosingDisk(points)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ac8734297c4d99750062ee028e743d0d0 "Computes the smallest closed disk containing a set of points."): Returns the unique smallest closed
  [`Disk`](shapes.md#disk) containing every given point, by a randomized
  incremental algorithm in expected $O(n)$ time. Constructing a disk supported by
  two points halves a coordinate, which stays exact here, so the center and the
  squared radius come back exact whatever the input. Raises for an empty list.

```python
corners = [pgl.Point(0,0), pgl.Point(4,0), pgl.Point(4,4), pgl.Point(0,4)]
disk = pgl.smallestEnclosingDisk(corners)
print(disk.center(), disk.squaredRadius())
# Output: (2,2) 8
```

The order of the points does not affect the answer, and neither does anything
else: the randomization is seeded the same way every run, so the same input
gives the identical disk.

### Smallest enclosing shapes of a convex hull

Both of these read a *convex* boundary, so they live on
[`Convex`](shapes.md#convex) rather than being free functions. Any other shape
reaches them through its own [`convexHull()`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a3999bfdf73609b7ec708a4882fcaea2f "Computes the convex hull of a point container."), whose enclosing shapes are its own.

- [`Convex.smallestEnclosingDisk()`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ac8734297c4d99750062ee028e743d0d0 "Computes the smallest closed disk containing a set of points."): The same disk [`smallestEnclosingDisk`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ac8734297c4d99750062ee028e743d0d0 "Computes the smallest closed disk containing a set of points.") gives
  for the hull's vertices. Worth preferring once a hull is at hand, since it has
  already discarded the interior points.

- `Convex.smallestEnclosingRectangle()`: The smallest-**area** enclosing
  rectangle, at whatever angle that turns out to be — so it comes back as a
  [`HalfplaneIntersection`](shapes.md#halfplane-intersection) of four
  half-planes and not as a [`Rectangle`](shapes.md#rectangle), which is
  axis-aligned by definition. By rotating calipers, linear in the hull's
  vertices. Its corners are generally fractional even for integer input, which
  the exact rationals carry without rounding, while its four supporting lines
  stay in the input's own coordinates.

```python
diamond = pgl.Convex([0,4, 4,0, 8,4, 4,8])
print(diamond.smallestEnclosingRectangle().area(), diamond.bbox().area())
# Output: 32 64
```

### Closest pair of points

- [`closestPair(points)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a9d03d057595b9229d8cc245045ce4df4 "Computes a closest pair of points by divide and conquer."): Returns a [`Segment`](shapes.md#segment) joining two of
  the given points at minimum distance from each other, by divide and conquer in
  $O(n \log n)$ on ordinary inputs. Only squared distances are compared, so the
  answer is exact; ties are broken arbitrarily. Needs at least two points.

### Visibility

[`Polygon`](shapes.md#polygon), [`PolygonWithHoles`](shapes.md#polygon-with-holes)
and [`Triangulation`](data_structures.md#triangulation) each answer the same six
visibility questions, all by *triangular expansion*: the domain is triangulated
once, then each vertex or query point runs a single traversal of the mesh
carrying a cone of still-unobstructed directions that every crossed diagonal
clips, at a cost proportional to the part of the domain that vertex actually
sees.

Sight is stopped by the boundary of the domain and, on a triangulation, by every
constrained edge as well — so `poly.triangulation(walls).visibilityGraph()` is
visibility inside `poly` among the segment obstacles `walls`.

Three of them return a [`Graph`](data_structures.md#graph) on the domain's
vertices:

- `visibilityGraph()`: joins two vertices $a, b$ when the segment $ab$ stays
  inside the domain, even if it touches the boundary along the way.
- `clearVisibilityGraph()`: the strict reading — the segment must not meet the
  boundary except at $a$ and $b$. Always a subgraph of `visibilityGraph()`. A
  degenerate domain has no interior, so its vertices come back with no edges.
- `reducedVisibilityGraph()`: the subgraph a shortest path can bend along, namely
  the edges tangent to the obstacles at both ends. What survives is the boundary
  edges and the bitangents between reflex corners, which is far sparser.

The other three answer for one query point in the domain, which need not be a
vertex:

- `visibleVertices(q)`: the domain's vertices visible from `q`, under
  `visibilityGraph()`'s convention, counterclockwise around `q` starting from the
  lexicographically smallest. This is what joins a query point to
  `reducedVisibilityGraph()`.
- `clearlyVisibleVertices(q)`: the strict counterpart, always a subset.
- `regularizedVisiblePolygon(q)`: the *region* visible from `q`, as a
  [`Polygon`](shapes.md#polygon) — every point reachable by a segment that stays
  in the domain and crosses no wall. It is star-shaped about `q`, hence simply
  connected, so one polygon holds it however many holes the domain has.
  *Regularized* means the closure of the interior, so a sightline running along a
  wall or slipping through a vertex into a part beyond contributes nothing: what
  comes back always bounds area. Its vertices are the domain's own together with
  the *window* ends where a sightline past a reflex corner lands on a farther
  edge.

```python
room = pgl.PolygonWithHoles(outer, holes)
graph = room.reducedVisibilityGraph()
for w in room.visibleVertices(source):
    graph.addEdge(source, w)                 # and the same for the target
path = graph.shortestPath(source, target, lambda a, b: a.distance(b))
```

### Boolean operations, Minkowski sums and erosions

Both families are documented under
[shape methods](shape_methods.md#boolean-operations). One free function belongs
here:

- [`regularizedUnionOf(shapes, simple_boundaries=False)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ae72efa38504e74942758d2d4fb78ffcd "The regularized union of arbitrarily many shapes, as a set of regions."): Returns the regularized
  union of every given shape as one [`PolygonSet`](shapes.md#polygon-set),
  settled by a single arrangement over all their boundaries — where uniting them
  one at a time would build one arrangement per step and re-triangulate
  everything accumulated so far. The list must be homogeneous, and may hold any
  one of the six bounded region types — [`Triangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangle.html "Closed triangle stored by three vertices."), [`Rectangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Rectangle.html "Axis-aligned rectangle stored by minimum and maximum corners."), [`Convex`](https://gfonsecabr.github.io/pgl/structpgl_1_1Convex.html "Closed convex polygon stored by its vertices."),
  [`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices."), [`PolygonWithHoles`](https://gfonsecabr.github.io/pgl/structpgl_1_1PolygonWithHoles.html "Closed region bounded by one outer simple polygon minus disjoint polygonal holes.") or [`PolygonSet`](https://gfonsecabr.github.io/pgl/structpgl_1_1PolygonSet.html "Set of closed regions with pairwise disjoint interiors."); a set contributes its
  components. Set `simple_boundaries` when no piece has two boundary edges
  overlapping each other (always true of a [`Triangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Triangle.html "Closed triangle stored by three vertices."), a [`Rectangle`](https://gfonsecabr.github.io/pgl/structpgl_1_1Rectangle.html "Axis-aligned rectangle stored by minimum and maximum corners.") and a
  [`Convex`](https://gfonsecabr.github.io/pgl/structpgl_1_1Convex.html "Closed convex polygon stored by its vertices."), true of a [`Polygon`](https://gfonsecabr.github.io/pgl/structpgl_1_1Polygon.html "Closed simple polygon stored by its vertices.") that meets its simplicity precondition, and true
  of a [`PolygonWithHoles`](https://gfonsecabr.github.io/pgl/structpgl_1_1PolygonWithHoles.html "Closed region bounded by one outer simple polygon minus disjoint polygonal holes.") exactly when it carries no slit) to take the faster
  face-classification path.

### Sorting points

Both of these reorder the Python list you pass **in place** and return `None`,
like `list.sort` does.

- [`sortAround(points, p)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#aab7826153f78fb8c4468ad851564fd8f "Sorts points counterclockwise around a center point."): Reorders `points` counterclockwise around the center
  `p`, starting from the lexicographically smallest point and breaking ties by
  putting farther points first. Connecting the result in order traces a simple
  star-shaped polygon whose kernel contains `p`. Relies only on exact orientation
  and squared-distance comparisons. Complexity $O(n \log n)$.

- [`hilbertSort(points)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a57def78cd131e9c518e478cafe93e137 "Sorts points along a Hilbert space-filling curve."): Reorders `points` along a Hilbert space-filling curve,
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

- [`polyominoes(size)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a9008f6bc68cdaae01e41b0e572127a43 "Enumerates the free polyominoes of a given size as polygons."): Returns one [`Polygon`](shapes.md#polygon) per free
  polyomino of `size` cells (counted up to translation, rotation, and
  reflection). Each polygon traces the polyomino boundary with small
  non-negative integer coordinates. Polyominoes that enclose a hole (possible
  from seven cells onward) are omitted, since their boundary is not a simple
  polygon.

- [`polyominoes(n1, n2)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a9008f6bc68cdaae01e41b0e572127a43 "Enumerates the free polyominoes of a given size as polygons."): Returns the free polyominoes of every size in
  `[n1, n2]`, smallest first.

- [`polyominoesUpTo(n)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ab11fd9fab1a04d2a326acb61c619e822 "Enumerates the free polyominoes of every size from 1 to n."): Returns the free polyominoes of every size from `1` to

- [`polyominoRegions(size)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ac6b73b7ed31a9544846662b7726f1fb3 "Enumerates the free polyominoes of a given size as regions.") returns one [`PolygonWithHoles`](shapes.md#polygon-with-holes) per free polyomino of `size` cells, omitting **none** of them: a region can represent one that encloses a hole, where a polygon cannot, since such a boundary is not a simple polygon. So these are the full free-polyomino counts — 108 at size seven, where `polyominoes` returns 107, and 369 at size eight against 363. Each region has small non-negative integer coordinates, canonical rings, and area equal to the cell count.

  A hole may touch the outer boundary at a single point — two diagonally opposite cells pinch the hole shut against the outside, as in the smallest holed polyomino — which `isValid()` accepts. Such a point is in the region but has no region interior around it.

- [`polyominoRegions(min_size, max_size)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#ac6b73b7ed31a9544846662b7726f1fb3 "Enumerates the free polyominoes of a given size as regions.") and [`polyominoRegionsUpTo(n)`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a9e59554fb52a45324cc9e7e558be8709 "Enumerates the free polyominoes of every size from 1 to n as regions.") mirror the two [`polyominoes`](https://gfonsecabr.github.io/pgl/namespacepgl.html#a9008f6bc68cdaae01e41b0e572127a43 "Enumerates the free polyominoes of a given size as polygons.") range overloads.
  `n`, smallest first.

```python
print(len(pgl.polyominoes(5)))   # the 12 pentominoes
# Output: 12
```
