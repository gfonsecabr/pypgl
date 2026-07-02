<img align="left" src="figures/logo.png" width="23%"/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/logotextdark.svg"/>
  <img alt="Pangolin: Plane Geometry Library" src="figures/logotext.svg" width="65%"/>
</picture>

<!-- [![Tests](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml/badge.svg)](https://github.com/gfonsecabr/pgl/actions/workflows/tests.yml)
[![Standard](https://img.shields.io/badge/C%2B%2B-20/23/26-rgb(10,66,158).svg)](https://en.wikipedia.org/wiki/C%2B%2B#Standardization) -->
[![License](https://img.shields.io/badge/license-MIT-rgb(216,134,42).svg)](https://opensource.org/licenses/MIT)
<!-- [![Benchmarks](https://img.shields.io/badge/benchmarks-online-rgb(21,153,135).svg)](https://gfonsecabr.github.io/pgl/benchmarks/index.html) -->

> ⚠️ **Work in Progress**: This library is still under construction and contains **bugs and missing features**. Use in production environments is not recommended.

## Data Structures


### Shape Tree

`ShapeTree` is a container for bounded shapes. The tree is built once and answers range queries against an arbitrary query shape. Unlike every other pypgl class, a single tree can mix shape types — a `Triangle` and a `Disk` can be stored side by side. If the tree stores $n$ points, then it behaves like a kd-tree, with $O(\sqrt{n})$ query time for orthogonal range counting and $O(\log n)$ height. For large intersecting shapes, the tree performs similarly to storing the shapes in a list and examining all of them, but with a much larger construction time.

- `ShapeTree(shapes, leaf_size=6)` builds the tree over `shapes` (any iterable of shapes, which may mix types). `leaf_size` is the maximum number of shapes kept at a leaf before it is split.

The query methods come in two families. The *intersecting* family matches stored shapes `s` with `s.intersects(query)`; the *contained* family matches stored shapes `s` with `query.contains(s)`. Each family offers three operations:

- `countIntersecting(query)` / `countContainedIn(query)` return the number of matching stored shapes.

- `reportIntersecting(query)` / `reportContainedIn(query)` return a list with a copy of each matching stored shape.

- `emptyIntersecting(query)` / `emptyContainedIn(query)` return `True` if no stored shape matches.

The query shape may be any shape pypgl binds, including one that cannot itself be stored in a tree (e.g. a `Line`).

Other methods: `size()` and `empty()` report the tree's size; `shapes()` returns all stored shapes, in internal order; `contains(shape)` reports whether a shape equal to `shape` is stored (exact membership, not a geometric test); `insert(shape)` adds a shape without rebalancing the tree (raises if `shape` cannot be stored — see below); `erase(shape)` removes one matching shape and reports whether one was found; `rebuild(leaf_size=0)` restores tree quality after many `insert`/`erase` calls (`0` keeps the current leaf size); `nearestNeighbor(query)` returns the stored shape nearest to `query`, or `None` if the tree is empty; `boundingBoxes()` returns every node's bounding box, in pre-order.

A tree also behaves like a Python container: `len(tree)`, `for shape in tree`, and `shape in tree` (exact membership, same as `contains`).

Only bounded shapes can be stored — `Point`, `Segment`, `OrientedSegment`, `Triangle`, `Rectangle`, `Convex`, `Polygon`, `Disk`. An unbounded shape (`Line`, `OrientedLine`, `Ray`, `Halfplane`) raises if passed to the constructor or to `insert`, but remains valid as a query shape.

Drawing a tree with `canvas.draw(tree)` (or its inline rendering in a notebook) renders every node's bounding box.

<p align="center">
  <img src="figures/example_shapetree_triangles.svg" alt="Shape tree range query over random triangles" width="50%"/>
  <br/>
  <em>A shape tree over 100 random triangles: the query triangle with the triangles it contains and intersects, plus the node bounding boxes.</em>
</p>


### Triangulation

`Triangulation` stores a mutable triangulation of either a fixed polygon or a fixed point set: the vertex coordinates are fixed at construction, only the connectivity changes.

- `Triangulation()` creates an empty triangulation.
- `Triangulation(points)` builds the Delaunay triangulation of a list of points.
- `Triangulation(triangles)` builds a triangulation from an explicit set of triangles tiling a region without overlaps.
- `Triangulation(edges)` builds a triangulation from an explicit set of edges (every bounded face must be a triangle).
- `Triangulation(polygon, points=[], segments=[])` builds the constrained Delaunay triangulation of a simple polygon (convex or not), optionally adding interior points as extra vertices and/or interior segments as constrained edges — both are assumed, not checked, to lie inside `polygon`. `polygon.triangulation()` and `polygon.triangulation(segments)` are shortcuts for this.

Construction and predicates are exact. For a polygon, the triangles between it and its convex hull are excluded, so the public view — sizes, `triangles()`, `edges()`, `locate`, … — describes exactly the polygon, including non-convex ones.

- `numVertices()`, `numTriangles()`, `numEdges()`, `empty()` report the triangulation's size.

- `contains(triangle)` / `contains(edge)` report whether a `Triangle`/`Segment` belongs to the triangulation.

- `triangles()` / `edges()` return all triangles / edges, sorted.

- `locate(point)` returns the triangle containing `point`, or `None` if `point` lies outside the triangulated region (or the triangulation is empty).

- Navigation: `otherTriangle(triangle, shared)` returns the triangle on the other side of the shared edge, or `None` on a boundary edge; `edgeAdjacentTriangles(triangle)` returns the (up to three) triangles sharing an edge with `triangle`; `vertexAdjacentTriangles(triangle)` returns the triangles sharing at least one vertex with `triangle` (excluding it); `incidentTriangles(edge)` returns the (up to two) triangles incident to `edge`, and `incidentTriangles(vertex)` returns every triangle around a vertex, in rotational order.

- Range searching: `trianglesIntersecting(query)` returns the triangles `t` with `t.intersects(query)`; `trianglesInteriorIntersecting(query)` filters with `t.interiorsIntersect(query)` instead. `edgesIntersecting(query)` / `edgesInteriorIntersecting(query)` return matching edges instead of triangles. `query` may be a `Segment`, `OrientedSegment`, `Line`, `OrientedLine`, `Ray`, `Point`, `Triangle`, `Rectangle`, `Convex`, `Disk`, or `Halfplane`. If `query` is a `Segment`, `OrientedSegment`, `Line`, `OrientedLine`, or `Ray`, the result is ordered along the query; otherwise the order is unspecified.

- `isConstrained(edge)` reports whether an edge is flagged as constrained; `setConstrained(edge, value=True)` sets or clears that flag.

- `flip(edge)` replaces `edge` by the opposite diagonal, returning the new edge, or `None` if the flip cannot be performed (non-convex quadrilateral or a constrained edge). `flippable(edge)` reports whether the flip is possible, without performing it. Both also accept a list of edges, flipping them all at once if the whole set is simultaneously flippable (all-or-nothing), or returning `None`/`False` otherwise. `flip` is the only method that mutates the triangulation.

- `checkInvariants()` checks the structural invariants (orientation and neighbor symmetry); intended for debugging.

Drawing a triangulation with `canvas.draw(triangulation)` (or its inline rendering in a notebook) renders every triangle.

<p align="center">
  <img src="figures/example_triangulation2.svg" alt="Triangulation with a segment traversal highlighted" width="50%"/>
  <br/>
  <em>The constrained Delaunay triangulation of a polygon with points inside. Highlighting the triangles a segment meets and those whose interior it actually intersects.</em>
</p>



